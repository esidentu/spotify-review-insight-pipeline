#!/usr/bin/env python3
"""Compare one and two workers on identical single-review Jev requests.

The 50 Golden texts and labels are loaded locally, but only review_text is
sent to Jev. Labels are attached after each response for quality measurement.
"""

from __future__ import annotations

import argparse
from concurrent.futures import as_completed
import csv
from datetime import datetime, timezone
from decimal import Decimal
import json
import os
from pathlib import Path
import time
import uuid

from pilot import (
    CALLS, COST, DATA, LABEL_CONFIG, PROMPT_VERSION, ROOT, TypeSafeWorkerPool,
    append_call, enrich_record, estimated_reserve, load_env, previous_spend,
    questions_for_enrichment, questions_payload_for_reserve, read_budget_and_rates, validate_record,
)


MAX_BENCHMARK_RESERVE = Decimal("0.05")


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)


def run_condition(golden, plans, api_key, input_rate, output_rate, workers):
    run_id = f"worker-comparison-golden50-w{workers}"
    output = COST / f"worker_comparison_50_w{workers}.csv"
    summary_path = COST / f"worker_comparison_50_w{workers}.json"
    if output.exists() or summary_path.exists():
        raise SystemExit(f"Benchmark output already exists for {workers} workers; refusing duplicate paid calls")

    results: list[dict] = []
    call_summaries = []
    started = time.perf_counter()
    with TypeSafeWorkerPool(api_key, workers) as pool:
        for offset in range(0, len(plans), workers):
            wave = plans[offset:offset + workers]
            futures = {
                pool.submit({"review_text": row["review_text"]}, questions_for_enrichment()): (index, row, reserve, str(uuid.uuid4()))
                for index, row, reserve in wave
            }
            wave_errors = []
            for future in as_completed(futures):
                index, row, reserve, call_id = futures[future]
                response = future.result()
                exc = response["error"]
                call = {
                    "run_id": run_id, "operation_id": f"{run_id}-{row['review_id']}",
                    "phase": "cold", "role": "enrich", "route": "primary", "provider": "typesafe",
                    "model": "jev-latest", "tier": "standard", "effort": "none",
                    "prompt_version": PROMPT_VERSION, "schema_version": "record-v1",
                    "batch_size": 1, "worker_count": workers, "review_ids": [row["review_id"]],
                    "work_units": 1, "request_id": None, "attempt": 1,
                    "local_call_id": call_id, "estimated_reserve_usd": str(reserve),
                    "duration_seconds": round(response["duration"], 6), "requests": 1,
                    "cached_input_tokens": 0,
                }
                if exc is not None:
                    call.update({"outcome": "failed", "input_tokens": None, "output_tokens": None,
                                 "usage_complete": False, "error_type": type(exc).__name__})
                    append_call(call)
                    wave_errors.append(f"review {row['review_id']} failed ({type(exc).__name__})")
                    continue

                result = response["response"]
                input_tokens = result.usage.input_tokens
                output_tokens = result.usage.output_tokens
                cost = (Decimal(input_tokens) * input_rate + Decimal(output_tokens) * output_rate
                        if input_tokens is not None and output_tokens is not None else None)
                call.update({"model": result.model, "outcome": "succeeded", "input_tokens": input_tokens,
                             "output_tokens": output_tokens, "usage_complete": cost is not None})
                record = enrich_record(row, result)
                errors = validate_record(record, row)
                if errors:
                    wave_errors.append(f"review {row['review_id']} failed validation")
                record.update({
                    "gold_topic": row["topic"], "gold_intent": row["intent"],
                    "gold_severity": row["severity"], "gold_sentiment": row["sentiment"],
                    "topic_match": record["topic"] == row["topic"],
                    "intent_match": record["intent"] == row["intent"],
                    "severity_match": record["severity"] == int(row["severity"]),
                    "sentiment_absolute_error": round(abs(record["sentiment"] - float(row["sentiment"])), 4),
                })
                results.append(record)
                write_csv(output, results)
                append_call(call)
                if cost is None or cost > reserve:
                    wave_errors.append(f"review {row['review_id']} usage missing or above its reserve")
                else:
                    call_summaries.append({"seconds": response["duration"], "input_tokens": input_tokens,
                                           "output_tokens": output_tokens, "cost_usd": cost})
            if wave_errors:
                raise SystemExit("; ".join(wave_errors) + "; stopped without retry")

    wall_seconds = time.perf_counter() - started
    summary = {
        "run_id": run_id, "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_rows": len(golden), "input_review_ids": [row["review_id"] for row in golden],
        "batch_size": 1, "worker_count": workers, "prompt_version": PROMPT_VERSION,
        "label_config": LABEL_CONFIG, "wall_seconds": round(wall_seconds, 6),
        "calls": len(call_summaries), "input_tokens": sum(item["input_tokens"] or 0 for item in call_summaries),
        "output_tokens": sum(item["output_tokens"] or 0 for item in call_summaries),
        "cost_usd": str(sum((item["cost_usd"] for item in call_summaries), Decimal(0))),
        "topic_agreement": sum(row["topic_match"] for row in results) / len(results),
        "intent_agreement": sum(row["intent_match"] for row in results) / len(results),
        "severity_exact_agreement": sum(row["severity_match"] for row in results) / len(results),
        "sentiment_mae": round(sum(row["sentiment_absolute_error"] for row in results) / len(results), 6),
        "request_latencies_seconds": [round(item["seconds"], 6) for item in call_summaries],
        "note": "Both conditions use the same 50 IDs, one-review state, four questions, model alias, prompt and schema. Model answers can still vary between independent calls.",
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="send the capped paired benchmark")
    args = parser.parse_args()
    load_env(ROOT / ".env")
    api_key = os.environ.get("TYPESAFE_API_KEY")
    if not api_key:
        raise SystemExit("TYPESAFE_API_KEY is missing; no requests sent")

    budget, input_rate, output_rate = read_budget_and_rates()
    known_spend, unresolved_reserve = previous_spend(input_rate, output_rate)
    with (DATA / "golden_50_labeled.csv").open(encoding="utf-8-sig", newline="") as stream:
        golden = list(csv.DictReader(stream))
    if len(golden) != 50 or len({row["review_id"] for row in golden}) != 50:
        raise SystemExit("Expected exactly 50 Golden rows with unique IDs")

    reserve_payload = questions_payload_for_reserve()
    plans = []
    paired_reserve = Decimal(0)
    for index, row in enumerate(golden):
        if not row.get("review_text", "").strip():
            raise SystemExit(f"Golden review {row.get('review_id')} has empty text")
        reserve = estimated_reserve({"review_text": row["review_text"]}, reserve_payload, input_rate)
        plans.append((index, row, reserve))
        paired_reserve += reserve * 2
    if paired_reserve > MAX_BENCHMARK_RESERVE or known_spend + unresolved_reserve + paired_reserve > budget:
        raise SystemExit(f"Paired reserve USD {paired_reserve:.6f} exceeds the benchmark or cumulative cap; no requests sent")
    print(f"Same-data preflight: 50 reviews, 50 one-review calls per condition, one worker then two workers.")
    print(f"Maximum paired reserve USD {paired_reserve:.6f}; current known spend USD {known_spend:.6f}; unresolved reserve USD {unresolved_reserve:.6f}; local cap USD {budget:.2f}.")
    if not args.execute:
        print("No API requests sent. Add --execute only to run this benchmark.")
        return 0
    if any((COST / f"worker_comparison_50_w{workers}.csv").exists() or (COST / f"worker_comparison_50_w{workers}.json").exists() for workers in (1, 2)):
        raise SystemExit("Paired benchmark outputs already exist; refusing duplicate paid calls")
    run_condition(golden, plans, api_key, input_rate, output_rate, workers=1)
    run_condition(golden, plans, api_key, input_rate, output_rate, workers=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
