#!/usr/bin/env python3
"""Compare one and two workers on five-review Jev batches from Golden 50.

Human labels are loaded only after each model response and are never placed in
request state or questions. Paid calls are bounded by a USD 0.05 benchmark
reserve and the project's cumulative cap.
"""

from __future__ import annotations

import csv
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import sys
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from pilot import (
    COST, DATA, ROOT, CALLS, TOPIC_DESCRIPTIONS, INTENT_DESCRIPTIONS,
    SEVERITY_LEVELS, SENTIMENT_LEVELS, LABEL_CONFIG, PROMPT_VERSION,
    append_call, canonical, estimated_reserve, feature_entities,
    load_env, previous_spend, read_budget_and_rates,
)


BATCH_SIZE = 5
BENCHMARK_RESERVE = Decimal("0.05")
OUT_TEMPLATE = "batch_benchmark_golden50_w{workers}.csv"
SUMMARY_TEMPLATE = "batch_benchmark_golden50_w{workers}.json"
PROMPT_TAG = "spotify-enrich-batch5-benchmark-v1"


def question_objects(rows: list[dict[str, str]]):
    from typesafe_sdk import Choice, Score

    questions = {}
    payload = {}
    for index, row in enumerate(rows):
        prefix = f"r{index:02d}"
        target = f"Only classify review {index} with review_id {row['review_id']} from state.reviews. Ignore the other reviews in the state. "
        specs = {
            "topic": ("choice", target + "Classify the review text itself. Select its most specific supported main topic. Do not use star ratings. If no specific topic is supported, select other.", TOPIC_DESCRIPTIONS),
            "intent": ("choice", target + "Classify the reviewer's communicative intent. Apply precedence: cancellation, complaint, request, praise, unclear. Mixed praise and criticism is complaint.", INTENT_DESCRIPTIONS),
            "severity": ("score", target + "Rate the highest-severity supported problem under the shared 1-5 rubric; on a tie, use the first mentioned. Praise, neutral/unclear content, and pure requests are severity 1. Cancellation alone does not raise severity.", SEVERITY_LEVELS),
            "sentiment": ("score", target + "Rate the overall sentiment expressed by the review text, not the star rating, from very negative to very positive.", SENTIMENT_LEVELS),
        }
        for name, (kind, instructions, criteria) in specs.items():
            key = f"{prefix}_{name}"
            questions[key] = Choice(instructions=instructions, criteria=criteria) if kind == "choice" else Score(instructions=instructions, criteria=criteria)
            payload[key] = {"type": kind, "instructions": instructions, "criteria": criteria}
    return questions, payload


def chunks(items: list[dict[str, str]], size: int):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
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


def send_one(plan, api_key: str):
    from typesafe_sdk import RetryPolicy, TypeSafeClient

    batch_index, batch, state, questions, _payload, reserve = plan
    started = time.perf_counter()
    try:
        with TypeSafeClient(api_key=api_key, model="jev-latest", retry=RetryPolicy(max_retries=0)) as client:
            response = client.system_one(state=state, questions=questions)
        return {"plan": plan, "response": response, "duration": time.perf_counter() - started, "error": None}
    except Exception as exc:
        return {"plan": plan, "response": None, "duration": time.perf_counter() - started, "error": exc}


def run_condition(plans, golden, api_key, input_rate, output_rate, workers):
    tag = f"{PROMPT_TAG}-w{workers}"
    run_id = f"batch-benchmark-golden50-w{workers}"
    out_path = COST / OUT_TEMPLATE.format(workers=workers)
    summary_path = COST / SUMMARY_TEMPLATE.format(workers=workers)
    started = time.perf_counter()
    results: list[dict[str, object]] = []
    call_summaries = []
    def record_result(item):
        batch_index, batch, _state, _questions, _payload, reserve = item["plan"]
        local_call_id = str(uuid.uuid4())
        response = item["response"]
        error = item["error"]
        if error is not None:
            append_call({
                "run_id": run_id, "operation_id": f"{tag}-{batch_index:03d}",
                "phase": "cold", "role": "enrich", "route": "primary", "provider": "typesafe",
                "model": "jev-latest", "tier": "standard", "effort": "none",
                "prompt_version": PROMPT_TAG, "schema_version": "record-v1", "batch_size": len(batch),
                "worker_count": workers, "review_ids": [row["review_id"] for row in batch],
                "work_units": len(batch), "request_id": None, "attempt": 1, "outcome": "failed",
                "input_tokens": None, "cached_input_tokens": 0, "output_tokens": None,
                "requests": 1, "usage_complete": False, "duration_seconds": round(item["duration"], 6),
                "local_call_id": local_call_id, "estimated_reserve_usd": str(reserve),
                "error_type": type(error).__name__,
            })
            return f"Batch {batch_index} failed ({type(error).__name__}); no retry was attempted"

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        call_cost = None if input_tokens is None or output_tokens is None else Decimal(input_tokens) * input_rate + Decimal(output_tokens) * output_rate
        append_call({
            "run_id": run_id, "operation_id": f"{tag}-{batch_index:03d}",
            "phase": "cold", "role": "enrich", "route": "primary", "provider": "typesafe",
            "model": response.model, "tier": "standard", "effort": "none",
            "prompt_version": PROMPT_TAG, "schema_version": "record-v1", "batch_size": len(batch),
            "worker_count": workers, "review_ids": [row["review_id"] for row in batch],
            "work_units": len(batch), "request_id": None, "attempt": 1, "outcome": "succeeded",
            "input_tokens": input_tokens, "cached_input_tokens": 0, "output_tokens": output_tokens,
            "requests": 1, "usage_complete": call_cost is not None, "duration_seconds": round(item["duration"], 6),
            "local_call_id": local_call_id, "estimated_reserve_usd": str(reserve),
        })
        if call_cost is None or call_cost > reserve:
            return f"Batch {batch_index} usage was missing or above its reservation; stopping this condition"
        call_summaries.append({"batch": batch_index, "rows": len(batch), "seconds": round(item["duration"], 6), "input_tokens": input_tokens, "output_tokens": output_tokens, "cost_usd": str(call_cost), "model": response.model})

        for index, raw in enumerate(batch):
            prefix = f"r{index:02d}"
            answers = response.answers
            topic_answer = answers[f"{prefix}_topic"]
            intent_answer = answers[f"{prefix}_intent"]
            severity_answer = answers[f"{prefix}_severity"]
            sentiment_answer = answers[f"{prefix}_sentiment"]
            severity = int(max(severity_answer.probabilities, key=severity_answer.probabilities.get)) + 1
            sentiment = round(max(-1.0, min(1.0, (float(sentiment_answer.score) - 2.0) / 2.0)), 4)
            confidence = {
                "topic": round(float(topic_answer.confidence), 4),
                "intent": round(float(intent_answer.confidence), 4),
                "severity": round(float(severity_answer.confidence), 4),
                "sentiment": round(float(sentiment_answer.confidence), 4),
            }
            prediction = {
                "review_id": raw["review_id"], "review_text": raw["review_text"],
                "topic": str(topic_answer.choice), "intent": str(intent_answer.choice),
                "severity": severity, "sentiment": sentiment, "entities": feature_entities(raw["review_text"]),
                "evidence_quote": raw["review_text"], "needs_review": min(confidence.values()) < 0.5,
                "confidence": confidence,
            }
            gold = golden[(batch_index - 1) * BATCH_SIZE + index]
            prediction.update({
                "gold_topic": gold["topic"], "gold_intent": gold["intent"],
                "gold_severity": gold["severity"], "gold_sentiment": gold["sentiment"],
                "topic_match": str(prediction["topic"] == gold["topic"]).lower(),
                "intent_match": str(prediction["intent"] == gold["intent"]).lower(),
                "severity_match": str(prediction["severity"] == int(gold["severity"])).lower(),
                "sentiment_absolute_error": round(abs(prediction["sentiment"] - float(gold["sentiment"])), 4),
            })
            results.append(prediction)
        write_rows(out_path, results)
        return None

    if workers == 1:
        for plan in plans:
            item = send_one(plan, api_key)
            problem = record_result(item)
            if problem:
                raise SystemExit(problem)
    else:
        # Submit only two at a time so the recorded worker count matches actual in-flight requests.
        for offset in range(0, len(plans), workers):
            wave = plans[offset:offset + workers]
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(send_one, plan, api_key) for plan in wave]
                wave_results = [future.result() for future in as_completed(futures)]
            problems = [problem for problem in (record_result(item) for item in wave_results) if problem]
            if problems:
                raise SystemExit("; ".join(problems))

    wall = time.perf_counter() - started
    mae = sum(float(row["sentiment_absolute_error"]) for row in results) / len(results)
    summary = {
        "run_id": run_id, "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_rows": len(golden), "batch_size": BATCH_SIZE, "worker_count": workers,
        "prompt_version": PROMPT_TAG, "model_ids": sorted({row["model"] for row in call_summaries}),
        "wall_seconds": round(wall, 6), "calls": len(call_summaries),
        "input_tokens": sum(row["input_tokens"] or 0 for row in call_summaries),
        "output_tokens": sum(row["output_tokens"] or 0 for row in call_summaries),
        "cost_usd": str(sum((Decimal(row["cost_usd"]) for row in call_summaries), Decimal(0))),
        "topic_agreement": sum(row["topic_match"] == "true" for row in results) / len(results),
        "intent_agreement": sum(row["intent_match"] == "true" for row in results) / len(results),
        "severity_exact_agreement": sum(row["severity_match"] == "true" for row in results) / len(results),
        "sentiment_mae": round(mae, 6), "batch_latencies_seconds": [row["seconds"] for row in call_summaries],
        "estimate_note": "The 50-row benchmark is a directional speed and quality check; it does not certify 100,000-row latency or accuracy.",
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="send the separately budgeted paid benchmark")
    args = parser.parse_args()

    load_env(ROOT / ".env")
    if not os.environ.get("TYPESAFE_API_KEY"):
        raise SystemExit("TYPESAFE_API_KEY is missing; no requests sent")
    budget, input_rate, output_rate = read_budget_and_rates()
    old_spend, unresolved_reserve = previous_spend(input_rate, output_rate)
    guarded_spend = old_spend + unresolved_reserve

    with (DATA / "golden_50_labeled.csv").open(encoding="utf-8-sig", newline="") as stream:
        golden = list(csv.DictReader(stream))
    if len(golden) != 50:
        raise SystemExit("Expected exactly 50 Golden rows")
    # Explicitly project only the raw text and ID into model state.
    model_rows = [{"review_id": row["review_id"], "review_text": row["review_text"]} for row in golden]
    batch_plans = []
    total_reserve = Decimal(0)
    for batch_index, batch in enumerate(chunks(model_rows, BATCH_SIZE), 1):
        state = {"reviews": batch}
        questions, payload = question_objects(batch)
        reserve = estimated_reserve(state, payload, input_rate, token_ratio=Decimal("0.95"))
        batch_plans.append((batch_index, batch, state, questions, payload, reserve))
        total_reserve += reserve
    if total_reserve > BENCHMARK_RESERVE:
        raise SystemExit(f"Benchmark reserve USD {total_reserve} exceeds USD {BENCHMARK_RESERVE}; no requests sent")
    if guarded_spend + total_reserve > budget:
        raise SystemExit("Benchmark plus prior spend exceeds the configured USD 8.00 cap; no requests sent")
    # Reserve for both the sequential control and the two-worker condition before any call.
    paired_reserve = total_reserve * 2
    if paired_reserve > BENCHMARK_RESERVE:
        raise SystemExit(f"Paired benchmark reserve USD {paired_reserve} exceeds USD {BENCHMARK_RESERVE}; no requests sent")
    if guarded_spend + paired_reserve > budget:
        raise SystemExit("Paired benchmark plus prior spend exceeds the configured USD 8.00 cap; no requests sent")
    print(f"Offline benchmark preflight: 50 review texts, {len(batch_plans)} batches of at most {BATCH_SIZE}; one-worker control plus two-worker condition.")
    print(f"Maximum paired benchmark reserve USD {paired_reserve:.6f}; known cumulative spend USD {old_spend:.6f}; unresolved reserve USD {unresolved_reserve:.6f}; cumulative cap USD {budget:.2f}.")
    if not args.execute:
        print("No API requests sent. Add --execute only to run this benchmark.")
        return 0

    api_key = os.environ["TYPESAFE_API_KEY"]
    run_condition(batch_plans, golden, api_key, input_rate, output_rate, workers=1)
    run_condition(batch_plans, golden, api_key, input_rate, output_rate, workers=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
