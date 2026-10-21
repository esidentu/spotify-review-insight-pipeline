#!/usr/bin/env python3
"""Build the declared 100,000-review scope plus all empty-text quarantines."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Data"
SOURCE = DATA / "spotify_reviews_18months.csv"
SELECTED = DATA / "final_100000.csv"
OUTPUT = DATA / "final_scope_100000_plus_empty.csv"
MANIFEST = DATA / "manifest.json"
FIELDS = ["review_id", "review_text", "review_rating", "review_likes", "app_version", "review_timestamp"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected_source = manifest["files"][SOURCE.name]["sha256"]
    if sha256_file(SOURCE) != expected_source:
        raise SystemExit("Source checksum does not match Data/manifest.json")

    with SELECTED.open(encoding="utf-8-sig", newline="") as stream:
        selected = list(csv.DictReader(stream, strict=True))
    if len(selected) != 100_000 or any(not row["review_text"].strip() for row in selected):
        raise SystemExit("Data/final_100000.csv must contain exactly 100,000 nonempty reviews")
    selected_ids = {row["review_id"] for row in selected}
    if len(selected_ids) != len(selected):
        raise SystemExit("Selected input contains duplicate review IDs")

    empty_rows: list[dict[str, str]] = []
    with SOURCE.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        if not set(FIELDS).issubset(reader.fieldnames or []):
            raise SystemExit("Source CSV does not have the expected six fields")
        for row in reader:
            if not row["review_text"].strip():
                if row["review_id"] in selected_ids:
                    raise SystemExit("An empty-text source row unexpectedly appears in the selected sample")
                empty_rows.append({field: row[field] for field in FIELDS})
    if len(empty_rows) != 13:
        raise SystemExit(f"Expected 13 empty-text rows; found {len(empty_rows)}")
    if selected_ids.intersection(row["review_id"] for row in empty_rows):
        raise SystemExit("Scope contains duplicate IDs")

    rows = [*selected, *sorted(empty_rows, key=lambda row: row["review_id"])]
    with OUTPUT.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    manifest.setdefault("files", {})[OUTPUT.name] = {
        "bytes": OUTPUT.stat().st_size,
        "sha256": sha256_file(OUTPUT),
    }
    manifest.setdefault("samples", {})["final_scope_100000_plus_empty"] = (
        "100,000 deterministic selected nonempty reviews plus all 13 empty-text source rows; "
        "the empty rows are quarantined and receive no model calls."
    )
    manifest["assignment_scope"]["selected_final_rows"] = 100_000
    manifest["assignment_scope"]["quarantined_empty_rows"] = 13
    manifest["assignment_scope"]["grading_input"] = OUTPUT.name
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_rows_profiled": 660_622,
        "selected_nonempty_rows": len(selected),
        "empty_text_quarantines": len(empty_rows),
        "grading_input_rows": len(rows),
        "output": str(OUTPUT),
        "sha256": sha256_file(OUTPUT),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
