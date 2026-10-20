#!/usr/bin/env python3
"""Export the completed 100,000-review Jev output as a review-friendly CSV."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "Data" / "final_100000.csv"
OUTPUT = ROOT / "grading" / "records.jsonl"
CSV_OUTPUT = ROOT / "cost" / "pilot_labeled_100000.csv"
FIELDS = [
    "review_id", "review_text", "review_rating", "review_likes", "app_version",
    "review_timestamp", "topic", "intent", "sentiment", "severity", "entities",
    "evidence_quote", "needs_review", "confidence_topic", "confidence_intent",
    "confidence_severity", "confidence_sentiment",
]
TEXT_FIELDS = {"review_text", "app_version", "topic", "intent", "evidence_quote"}


def excel_safe_text(value: object) -> object:
    """Prefix formula-leading text so spreadsheet apps display it as text."""
    if isinstance(value, str) and value.lstrip()[:1] in {"=", "+", "-", "@"}:
        return "'" + value
    return value


def main() -> None:
    with INPUT.open(encoding="utf-8-sig", newline="") as stream:
        source_rows = list(csv.DictReader(stream))
    records = {
        record["review_id"]: record
        for line in OUTPUT.open(encoding="utf-8")
        for record in [json.loads(line)]
    }
    if len(source_rows) != 100_000:
        raise SystemExit(f"Expected 100,000 source rows; found {len(source_rows)}")
    if len(records) != 100_000 or set(records) != {row["review_id"] for row in source_rows}:
        raise SystemExit("Completed output IDs do not exactly match the 100,000 source IDs")
    if any(record.get("status") != "completed" for record in records.values()):
        raise SystemExit("Output contains incomplete records; CSV export stopped")

    with CSV_OUTPUT.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for source in source_rows:
            record = records[source["review_id"]]
            confidence = record.get("confidence", {})
            source_fields = {
                field: (excel_safe_text(source.get(field, "")) if field in TEXT_FIELDS else source.get(field, ""))
                for field in FIELDS[:6]
            }
            writer.writerow({
                **source_fields,
                "topic": excel_safe_text(record["topic"]),
                "intent": excel_safe_text(record["intent"]),
                "sentiment": record["sentiment"],
                "severity": record["severity"],
                "entities": json.dumps(record.get("entities", []), ensure_ascii=False),
                "evidence_quote": excel_safe_text(record["evidence_quote"]),
                "needs_review": str(bool(record["needs_review"])).lower(),
                "confidence_topic": confidence.get("topic", ""),
                "confidence_intent": confidence.get("intent", ""),
                "confidence_severity": confidence.get("severity", ""),
                "confidence_sentiment": confidence.get("sentiment", ""),
            })
    print(f"Wrote {len(source_rows)} rows to {CSV_OUTPUT}")


if __name__ == "__main__":
    main()
