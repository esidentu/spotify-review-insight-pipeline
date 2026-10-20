#!/usr/bin/env python3
"""Rebuild the required deterministic issue ranking from saved records."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import tempfile
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


RANKING_FIELDS = [
    "rank",
    "issue_id",
    "complaint_count",
    "severity_sum",
    "mean_severity",
    "priority_score",
]


def load_records(path: Path, db: sqlite3.Connection) -> int:
    count = 0
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                record: dict[str, Any] = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            review_id = record.get("review_id")
            if not isinstance(review_id, str) or not review_id:
                raise ValueError(f"{path}:{line_number}: missing string review_id")
            if record.get("status") == "completed" and record.get("intent") in {"complaint", "cancellation"}:
                severity = record.get("severity")
                if isinstance(severity, bool) or not isinstance(severity, int) or not 1 <= severity <= 5:
                    raise ValueError(f"{path}:{line_number}: completed complaint/cancellation needs integer severity 1-5")
            try:
                db.execute(
                    "INSERT INTO records(review_id, status, intent, severity) VALUES (?, ?, ?, ?)",
                    (review_id, record.get("status"), record.get("intent"), record.get("severity")),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError(f"{path}:{line_number}: duplicate review_id {review_id!r}") from exc
            count += 1
    return count


def load_membership(path: Path, db: sqlite3.Connection) -> int:
    count = 0
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not {"issue_id", "review_id"}.issubset(reader.fieldnames):
            raise ValueError(f"{path}: expected issue_id,review_id columns")
        for line_number, row in enumerate(reader, 2):
            issue_id = (row.get("issue_id") or "").strip()
            review_id = (row.get("review_id") or "").strip()
            if not issue_id or not review_id:
                raise ValueError(f"{path}:{line_number}: issue_id and review_id must be nonempty")
            try:
                db.execute("INSERT INTO membership(issue_id, review_id) VALUES (?, ?)", (issue_id, review_id))
            except sqlite3.IntegrityError as exc:
                raise ValueError(f"{path}:{line_number}: duplicate (issue_id, review_id) pair") from exc
            count += 1
    return count


def validate(db: sqlite3.Connection, allow_multi_issue: bool) -> None:
    foreign = db.execute(
        "SELECT m.review_id FROM membership m LEFT JOIN records r USING(review_id) WHERE r.review_id IS NULL LIMIT 1"
    ).fetchone()
    if foreign:
        raise ValueError(f"membership references unknown review_id {foreign[0]!r}")

    invalid_member = db.execute(
        "SELECT m.review_id FROM membership m JOIN records r USING(review_id) "
        "WHERE r.status != 'completed' OR r.intent NOT IN ('complaint','cancellation') LIMIT 1"
    ).fetchone()
    if invalid_member:
        raise ValueError(f"membership includes a non-completed or non-complaint review {invalid_member[0]!r}")

    bad_severity = db.execute(
        "SELECT review_id, severity FROM records "
        "WHERE status='completed' AND intent IN ('complaint','cancellation') "
        "AND (typeof(severity) NOT IN ('integer','real') OR severity < 1 OR severity > 5 OR severity != CAST(severity AS INTEGER)) LIMIT 1"
    ).fetchone()
    if bad_severity:
        raise ValueError(f"complaint/cancellation {bad_severity[0]!r} has invalid severity {bad_severity[1]!r}")

    unassigned = db.execute(
        "SELECT r.review_id FROM records r LEFT JOIN membership m USING(review_id) "
        "WHERE r.status='completed' AND r.intent IN ('complaint','cancellation') "
        "GROUP BY r.review_id HAVING COUNT(m.issue_id)=0 LIMIT 1"
    ).fetchone()
    if unassigned:
        raise ValueError(f"complaint/cancellation {unassigned[0]!r} has no issue membership")

    if not allow_multi_issue:
        multiple = db.execute(
            "SELECT review_id FROM membership GROUP BY review_id HAVING COUNT(*) > 1 LIMIT 1"
        ).fetchone()
        if multiple:
            raise ValueError(f"review {multiple[0]!r} belongs to multiple issues; pass --allow-multi-issue only if documented")


def build_ranking(db: sqlite3.Connection) -> list[dict[str, str]]:
    aggregates = db.execute(
        "SELECT m.issue_id, COUNT(*) AS complaint_count, SUM(CAST(r.severity AS INTEGER)) AS severity_sum "
        "FROM membership m JOIN records r USING(review_id) "
        "GROUP BY m.issue_id"
    ).fetchall()
    rows = []
    for issue_id, count, severity_sum in aggregates:
        mean = (Decimal(severity_sum) / Decimal(count)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        rows.append(
            {
                "issue_id": issue_id,
                "complaint_count": str(count),
                "severity_sum": str(severity_sum),
                "mean_severity": f"{mean:.6f}",
                "priority_score": str(severity_sum),
            }
        )
    rows.sort(key=lambda row: (-int(row["priority_score"]), row["issue_id"]))
    for rank, row in enumerate(rows, 1):
        row["rank"] = str(rank)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True, help="completed records JSONL")
    parser.add_argument("--membership", type=Path, required=True, help="issue_id,review_id CSV")
    parser.add_argument("--out", type=Path, required=True, help="ranking CSV output path")
    parser.add_argument("--allow-multi-issue", action="store_true", help="allow overlapping issue membership")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="spotify-rank-") as tmp:
        db_path = Path(tmp) / "ranking.sqlite3"
        db = sqlite3.connect(db_path)
        try:
            with db:
                db.execute("CREATE TABLE records(review_id TEXT PRIMARY KEY, status TEXT, intent TEXT, severity NUMERIC)")
                db.execute("CREATE TABLE membership(issue_id TEXT NOT NULL, review_id TEXT NOT NULL, PRIMARY KEY(issue_id, review_id))")
                record_count = load_records(args.records, db)
                membership_count = load_membership(args.membership, db)
                validate(db, args.allow_multi_issue)
                ranked = build_ranking(db)
        finally:
            # The transaction context commits or rolls back, but does not close
            # the SQLite handle. Explicit close is required before Windows can
            # remove the temporary directory containing the database.
            db.close()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=RANKING_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ranked)
    print(f"Ranked {len(ranked)} issues from {membership_count} memberships across {record_count} records.")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
