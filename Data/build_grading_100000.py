#!/usr/bin/env python3
"""Build the Assignment 5 grading adapter for the declared 100,000-row scope.

This is an offline export. It does not call a model provider.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Data"
COST = ROOT / "cost"
OUT = ROOT / "grading"
RUN_ID = "cold-100000-20261020T213754Z"
INITIAL_ENRICH_WORK_UNITS = 3804
RECORD_FIELDS = (
    "review_id", "source_sha256", "status", "topic", "intent", "sentiment",
    "severity", "entities", "evidence_quote", "needs_review", "label_config",
)
CLAIM_METRICS = ("complaint_count", "severity_sum", "mean_severity", "priority_score")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, strict=True))


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n")
    temporary.replace(path)


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def exact_file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_fields(record: dict) -> tuple:
    return tuple(json.dumps(record.get(key), ensure_ascii=False, sort_keys=True) for key in (
        "topic", "intent", "sentiment", "severity", "entities", "evidence_quote", "needs_review", "label_config"
    ))


def main() -> None:
    existing = {path.name for path in OUT.iterdir()} if OUT.exists() else set()
    expected_outputs = {
        "run.json", "records.jsonl", "membership.csv", "ranking.csv", "claims.csv",
        "checkpoint_before.json", "checkpoint_after.json", "calls.jsonl",
        "local_stages.jsonl", "memo.md", "README.md",
    }
    if existing - expected_outputs - {"ingestion.json"}:
        raise SystemExit(f"Unexpected files in grading output directory: {sorted(existing - expected_outputs - {'ingestion.json'})}")
    OUT.mkdir(parents=True, exist_ok=True)

    analysis_path = DATA / "final_scope_100000_plus_empty.csv"
    analysis = read_csv(analysis_path)
    source_by_id = {row["review_id"]: row for row in analysis}
    if len(analysis) != 100_013 or len(source_by_id) != 100_013:
        raise SystemExit("The grading input must contain 100,000 selected reviews plus 13 empty-text rows.")
    empty_ids = {row["review_id"] for row in analysis if not row["review_text"].strip()}
    if len(empty_ids) != 13:
        raise SystemExit(f"The grading input must contain exactly 13 empty-text rows; found {len(empty_ids)}.")
    selected_order = [row["review_id"] for row in analysis if row["review_id"] not in empty_ids]

    completed = read_jsonl(COST / "pilot_records_100000_complete.jsonl")
    record_by_id = {row["review_id"]: row for row in completed}
    selected_ids = set(source_by_id) - empty_ids
    if len(completed) != 100_000 or set(record_by_id) != selected_ids:
        raise SystemExit("Completed output IDs do not exactly match the 100,000 selected nonempty reviews.")

    # Give every exact-text reuse a direct link to an in-scope original that
    # has a successful enrichment call. Identical text groups have identical
    # classification fields in the saved final output.
    raw_calls = read_jsonl(COST / "pilot_calls.jsonl")
    call_rows: list[dict] = []
    successful_enrich_ids: dict[str, list[int]] = defaultdict(list)
    for position, event in enumerate(raw_calls):
        ids = event.get("review_ids")
        if not isinstance(ids, list) or len(ids) != 1 or ids[0] not in source_by_id:
            continue
        if event.get("role") == "enrich" and event.get("outcome") == "succeeded":
            successful_enrich_ids[ids[0]].append(position)

    by_text: dict[str, list[str]] = defaultdict(list)
    for rid in selected_order:
        source = source_by_id[rid]
        by_text[source["review_text"]].append(rid)

    roots: dict[str, str] = {}
    for text, ids in by_text.items():
        representatives = [rid for rid in ids if rid in successful_enrich_ids]
        if not representatives:
            raise SystemExit("No in-scope successful enrichment call for a distinct text.")
        root_id = min(representatives, key=lambda rid: successful_enrich_ids[rid][0])
        root_record = record_by_id[root_id]
        for rid in ids:
            if canonical_fields(record_by_id[rid]) != canonical_fields(root_record):
                raise SystemExit("Exact duplicate text has inconsistent saved labels; refusing cache link.")
        roots[text] = root_id

    records = []
    for rid in selected_order:
        out_record = {key: record_by_id[rid][key] for key in RECORD_FIELDS}
        root_id = roots[source_by_id[rid]["review_text"]]
        if rid != root_id:
            out_record["cache_source_id"] = root_id
        # Retain confidence and verification provenance for auditability.
        for optional in ("confidence", "verification_probability", "confidence_review_rule", "entity_method"):
            if optional in record_by_id[rid]:
                out_record[optional] = record_by_id[rid][optional]
        records.append(out_record)
    for rid in sorted(empty_ids):
        records.append({
            "review_id": rid,
            "source_sha256": hashlib.sha256(json.dumps(
                [source_by_id[rid][field] for field in (
                    "review_id", "review_text", "review_rating", "review_likes", "app_version", "review_timestamp"
                )], ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")).hexdigest(),
            "status": "quarantined",
            "reason": "empty_review_text",
        })
    write_jsonl(OUT / "records.jsonl", records)

    subset_hash = exact_file_sha(analysis_path)
    write_json(OUT / "run.json", {
        "version": "a5-audit-v1",
        "analysis_count": len(analysis),
        "analysis_sha256": subset_hash,
        "classification_input_fields": ["review_text"],
        "allow_multi_issue": False,
        "declared_scope": "100000 deterministic selected nonempty reviews plus all 13 empty-text source rows quarantined; full source ingestion profile retained separately",
        "source_file": "Data/spotify_reviews_18months.csv",
        "source_file_sha256": "1fc85de68a304dd8978b537cfa58793d5f41cbaf417fa32cb53899f83a2fcef6",
        "analysis_file": "Data/final_scope_100000_plus_empty.csv",
        "pipeline_run_id": RUN_ID,
        "labeling_review": "See review_100000_quality.md; completed records preserved as produced.",
    })

    # Export the existing deterministic topic buckets and baseline ranking.
    membership = read_csv(COST / "pilot_membership_100000.csv")
    ranking = read_csv(COST / "pilot_ranking_100000.csv")
    write_csv(OUT / "membership.csv", ["issue_id", "review_id"], membership)
    ranking_fields = ["rank", "issue_id", "complaint_count", "severity_sum", "mean_severity", "priority_score"]
    write_csv(OUT / "ranking.csv", ranking_fields, ranking)

    claims = []
    for rank_row in ranking:
        for metric in CLAIM_METRICS:
            claims.append({
                "claim_id": f"r{int(rank_row['rank']):02d}-{metric}",
                "issue_id": rank_row["issue_id"],
                "metric": metric,
                "value": rank_row[metric],
            })
    write_csv(OUT / "claims.csv", ["claim_id", "issue_id", "metric", "value"], claims)

    # Reconstruct the saved before-checkpoint from the first logged partial
    # run's cache plus its 3,804 successful enrichments. It matches the saved
    # run ledger's 31,283 completed-record count; the after snapshot is final.
    cache_rows = read_csv(COST / "pilot_labeled_10000.csv")
    checkpoint_run = next((run for run in read_jsonl(COST / "pilot_runs.jsonl")
                           if run.get("run_id") == RUN_ID and run.get("completed_records") == 31_283), None)
    if not checkpoint_run:
        raise SystemExit("Could not locate the logged 31,283-record checkpoint boundary.")
    initial_units = checkpoint_run.get("stage_metrics", {}).get("enrich_primary", {}).get("work_units")
    if initial_units != INITIAL_ENRICH_WORK_UNITS:
        raise SystemExit("Checkpoint enrichment count differs from the documented run boundary.")
    run_enrich_successes = [event for event in raw_calls
                            if event.get("run_id") == RUN_ID and event.get("role") == "enrich"
                            and event.get("outcome") == "succeeded"]
    if len(run_enrich_successes) < initial_units:
        raise SystemExit("Call ledger is shorter than the checkpoint boundary.")
    cached_texts = {row["review_text"] for row in cache_rows}
    first_new_texts = {source_by_id[rid]["review_text"]
                       for event in run_enrich_successes[:initial_units]
                       for rid in event["review_ids"] if rid in source_by_id}
    before_texts = cached_texts | first_new_texts
    before_ids = sorted(rid for rid, source in source_by_id.items() if source["review_text"] in before_texts)
    if len(before_ids) != checkpoint_run["completed_records"]:
        raise SystemExit("Reconstructed checkpoint IDs do not match the saved run count.")
    after_ids = sorted(record_by_id)
    write_json(OUT / "checkpoint_before.json", {
        "completed_ids": before_ids,
        "snapshot_origin": "reconstructed from the deterministic 10,000-row cache, exact-text reuse, successful call order, and the saved 31,283-record run checkpoint",
        "saved_run_completed_records": checkpoint_run["completed_records"],
    })
    write_json(OUT / "checkpoint_after.json", {
        "completed_ids": after_ids,
        "snapshot_origin": "final completed 100,000-row output",
    })

    # Use local call IDs where the provider did not return a request ID. Keep
    # unavailable failed-call usage as null instead of inventing zero usage.
    successes_seen = 0
    for event in raw_calls:
        ids = event.get("review_ids")
        if not isinstance(ids, list) or len(ids) != 1 or ids[0] not in source_by_id:
            continue
        role = event.get("role")
        if role not in {"enrich", "verify"}:
            continue
        if event.get("run_id") == RUN_ID and role == "enrich":
            phase = "initial" if successes_seen < initial_units else "resume"
            if event.get("outcome") == "succeeded":
                successes_seen += 1
        elif event.get("run_id") == RUN_ID:
            phase = "resume"
        else:
            phase = "initial"
        rid = ids[0]
        request_id = event.get("request_id") or event.get("local_call_id") or event.get("operation_id")
        if not isinstance(request_id, str) or not request_id:
            raise SystemExit("A retained model call has no provider or local call ID.")
        call = {
            "request_id": request_id,
            "role": role,
            "review_ids": ids,
            "model": event.get("model") or "unknown-model-id",
            "phase": phase,
            "outcome": event.get("outcome"),
            "input_tokens": event.get("input_tokens"),
            "output_tokens": event.get("output_tokens"),
            "provider": event.get("provider"),
            "local_call_id": event.get("local_call_id"),
            "worker_count": event.get("worker_count"),
            "label_config": record_by_id[rid]["label_config"],
            "usage_complete": event.get("usage_complete"),
            "error_type": event.get("error_type"),
        }
        call["review_ids"] = ids
        call_rows.append(call)
    if len({row["request_id"] for row in call_rows}) != len(call_rows):
        raise SystemExit("Retained call IDs are not unique.")
    write_jsonl(OUT / "calls.jsonl", call_rows)

    # Deterministic grouping and memo generation are explicitly logged as
    # local stages; they are not misrepresented as model calls.
    write_jsonl(OUT / "local_stages.jsonl", [
        {"stage": "group", "method": "deterministic topic buckets", "input": "records.jsonl", "output": "membership.csv and ranking.csv", "provider_calls": 0},
        {"stage": "memo", "method": "local template from saved aggregate artifacts", "input": "ranking.csv and claims.csv", "output": "memo.md", "provider_calls": 0},
    ])

    lines = [
        "# Product recommendation from the 100,000-review sample",
        "",
        "## Scope and method",
        "",
        "This memo covers the deterministic 100,000-row subset, not the entire 660,622-row source. Topic buckets are deterministic groupings of completed complaint and cancellation labels. They are broad topics, not model-discovered product issues. The sampled reviews are self-selected public feedback and do not establish market-wide rates.",
        "",
        "## Recommendation",
        "",
        "Prioritize investigation of usability in the next planning cycle. It has the highest baseline priority score in this subset: 13,886 complaint/cancellation reviews, a severity sum of 37,501, and mean severity 2.700634 (claims `r01-complaint_count`, `r01-severity_sum`, `r01-mean_severity`, `r01-priority_score`). Billing ranks third with score 20,978 and playback fourth with score 19,747 (claims `r03-priority_score`, `r04-priority_score`). The second-ranked `other` bucket has a score of 29,493 but is too broad to directly identify a product investment (claim `r02-priority_score`). This is a prioritization signal from the selected sample; validate it with product telemetry and targeted user research before treating it as a population-wide conclusion.",
        "",
        "## Baseline ranking",
        "",
        "| Rank | Topic bucket | Complaint/cancellation count | Severity sum | Mean severity | Priority score | Claims |",
        "|---:|---|---:|---:|---:|---:|---|",
    ]
    for row in ranking:
        n = int(row["rank"])
        lines.append(
            f"| {row['rank']} | {row['issue_id']} | {row['complaint_count']} | {row['severity_sum']} | {row['mean_severity']} | {row['priority_score']} | "
            f"`r{n:02d}-complaint_count`, `r{n:02d}-severity_sum`, `r{n:02d}-mean_severity`, `r{n:02d}-priority_score` |"
        )
    lines += [
        "",
        "The table follows the required baseline: complaint count multiplied by mean severity, equal to severity sum. Counts include each source review once in its topic bucket.",
        "",
        "## Quality and evidence notes",
        "",
        "The Golden 50 comparison, `needs_review` analysis, and the 142 bare-`Boycott` intent mismatches are documented in `../cost/review_100000_quality.md`. The completed labels are preserved as produced. The enrichment and verification stages used Jev; grouping and memo generation used local deterministic code, as recorded in `local_stages.jsonl`.",
        "",
        "The checker expects successful model-call evidence for `group` and `memo`; those provider calls were not made in this run. It also requires numeric token usage on failed-call entries even when the provider returned no usage. The call log preserves those unknown values as null, so a review-required self-check is expected for those evidence gaps. The 13 empty source texts are included as explicit `empty_review_text` quarantines; they received no model calls.",
        "",
    ]
    (OUT / "memo.md").write_text("\n".join(lines), encoding="utf-8")
    (OUT / "README.md").write_text(
        "# 100,000-row grading export\n\n"
        "This folder is the grading adapter for the declared 100,000-nonempty-review scope. "
        "`run.json` identifies 100,000 selected nonempty reviews plus all 13 empty-text quarantines; `ingestion.json` profiles the full source file. "
        "The package was built offline from saved outputs and call logs. No provider requests were made.\n\n"
        "Read `memo.md` for the recommendation and ranking, `../cost/review_100000_quality.md` for the human-label and needs-review analysis, and `local_stages.jsonl` for the deterministic grouping/memo stages. `checkpoint_before.json` is reconstructed from the saved input/cache/call ordering and matches the logged 31,283-record checkpoint; it was not a separately captured snapshot file at runtime.\n\n"
        "Known evidence gaps: no model calls were made for group or memo, although the checker asks for those roles; 12 failed attempts in this selected scope have unavailable token usage (nine during the 100,000 run and three during earlier checkpoints), preserved as null. The completed bare-`Boycott` labels also remain as produced and are documented in the quality review.\n",
        encoding="utf-8",
    )
    print(f"Built {OUT} for {len(records):,} records, {len(call_rows):,} retained provider-call attempts, and {len(before_ids):,} reconstructed checkpoint IDs.")


if __name__ == "__main__":
    main()
