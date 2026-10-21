#!/usr/bin/env python3
"""Build a local SQLite dashboard database from saved, reviewed project outputs."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc


def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        yield from csv.DictReader(stream, strict=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=ROOT / "dashboard" / "spotify.sqlite3")
    parser.add_argument("--replace", action="store_true", help="replace an existing database file")
    args = parser.parse_args()

    records_path = ROOT / "grading" / "records.jsonl"
    source_path = ROOT / "Data" / "final_scope_100000_plus_empty.csv"
    membership_path = ROOT / "grading" / "membership.csv"
    ranking_path = ROOT / "grading" / "ranking.csv"
    claims_path = ROOT / "grading" / "claims.csv"
    memo_path = ROOT / "grading" / "memo.md"
    for path in (records_path, source_path, membership_path, ranking_path, claims_path, memo_path):
        if not path.is_file():
            raise SystemExit(f"Required project artifact is missing: {path}")
    db_path = args.database.resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists() and not args.replace:
        raise SystemExit(f"Database already exists: {db_path}. Pass --replace to rebuild it.")
    if db_path.exists():
        db_path.unlink()

    con = sqlite3.connect(db_path)
    try:
        con.executescript("""
            PRAGMA foreign_keys = ON;
            CREATE TABLE reviews (
                review_id TEXT PRIMARY KEY,
                review_text TEXT NOT NULL,
                review_rating TEXT NOT NULL,
                review_likes TEXT NOT NULL,
                app_version TEXT NOT NULL,
                review_timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                topic TEXT,
                intent TEXT,
                sentiment REAL,
                severity INTEGER,
                entities_json TEXT,
                evidence_quote TEXT,
                verification_probability REAL,
                needs_review INTEGER,
                cache_source_id TEXT,
                FOREIGN KEY(cache_source_id) REFERENCES reviews(review_id) DEFERRABLE INITIALLY DEFERRED
            );
            CREATE TABLE issue_membership (
                issue_id TEXT NOT NULL,
                review_id TEXT NOT NULL REFERENCES reviews(review_id),
                PRIMARY KEY(issue_id, review_id)
            );
            CREATE INDEX membership_issue_idx ON issue_membership(issue_id, review_id);
            CREATE TABLE ranking (
                rank INTEGER PRIMARY KEY,
                issue_id TEXT UNIQUE NOT NULL,
                complaint_count INTEGER NOT NULL,
                severity_sum INTEGER NOT NULL,
                mean_severity TEXT NOT NULL,
                priority_score INTEGER NOT NULL
            );
            CREATE TABLE claims (
                claim_id TEXT PRIMARY KEY,
                issue_id TEXT NOT NULL,
                metric TEXT NOT NULL,
                value TEXT NOT NULL
            );
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        source_by_id = {r["review_id"]: r for r in read_csv(source_path)}
        record_count = 0
        for record in read_jsonl(records_path):
            rid = record["review_id"]
            src = source_by_id.get(rid)
            if src is None:
                raise ValueError(f"Output record has no matching selected input row: {rid}")
            con.execute("""INSERT INTO reviews VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                rid, src["review_text"], src["review_rating"], src["review_likes"], src["app_version"],
                src["review_timestamp"], record["status"], record.get("topic"), record.get("intent"),
                record.get("sentiment"), record.get("severity"), json.dumps(record.get("entities", []), ensure_ascii=False),
                record.get("evidence_quote"), record.get("verification_probability"),
                int(bool(record.get("needs_review"))), record.get("cache_source_id"),
            ))
            record_count += 1
        if record_count != len(source_by_id):
            raise ValueError(f"Records ({record_count}) do not cover the selected input ({len(source_by_id)}).")
        membership_count = 0
        for row in read_csv(membership_path):
            con.execute("INSERT INTO issue_membership VALUES (?,?)", (row["issue_id"], row["review_id"]))
            membership_count += 1
        for row in read_csv(ranking_path):
            con.execute("INSERT INTO ranking VALUES (?,?,?,?,?,?)", (
                int(row["rank"]), row["issue_id"], int(row["complaint_count"]), int(row["severity_sum"]),
                row["mean_severity"], int(row["priority_score"]),
            ))
        for row in read_csv(claims_path):
            con.execute("INSERT INTO claims VALUES (?,?,?,?)", (row["claim_id"], row["issue_id"], row["metric"], row["value"]))

        status = json.loads((ROOT / "grading-self-check.json").read_text(encoding="utf-8"))
        run = json.loads((ROOT / "grading" / "run.json").read_text(encoding="utf-8"))
        ingestion = json.loads((ROOT / "grading" / "ingestion.json").read_text(encoding="utf-8"))
        decision_path = ROOT / "grading" / "ai_recommendation.json"
        group_path = ROOT / "grading" / "ai_grouping.json"
        recommendation_origin = "saved memo; local template stage, not a model-generated memo"
        grouping_choice = "not run"
        if decision_path.is_file():
            decision = json.loads(decision_path.read_text(encoding="utf-8"))
            recommendation_origin = f"TypeSafe {decision['model']} Choice plus deterministic, claim-checked rendering"
        if group_path.is_file():
            grouping_choice = json.loads(group_path.read_text(encoding="utf-8"))["choice"]
        metadata = {
            "analysis_count": str(record_count),
            "source_rows": str(ingestion["counts"]["records"]),
            "source_file_sha256": run["source_file_sha256"],
            "analysis_sha256": run["analysis_sha256"],
            "pipeline_run_id": run["pipeline_run_id"],
            "self_check_status": status["status"],
            "self_check_coverage": json.dumps(status["coverage"], sort_keys=True),
            "recommendation_origin": recommendation_origin,
            "grouping_follow_up": grouping_choice,
            "recommendation_markdown": memo_path.read_text(encoding="utf-8"),
        }
        con.executemany("INSERT INTO metadata VALUES (?,?)", metadata.items())
        con.commit()
        print(f"Built {db_path}: {record_count:,} reviews, {membership_count:,} memberships, {len(metadata)} metadata values.")
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
