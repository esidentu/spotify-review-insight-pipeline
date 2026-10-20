#!/usr/bin/env python3
"""Offline readiness check for the fixed TypeSafe 100-review pilot."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


def load_local_env(path: Path) -> None:
    """Load simple KEY=VALUE entries without printing or overwriting env vars."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip("\"'")
        if key and value:
            os.environ.setdefault(key, value)


def main() -> int:
    errors: list[str] = []
    manifest_path = ROOT / "Data" / "manifest.json"
    sample_path = ROOT / "Data" / "cost_100.csv"
    projection_path = ROOT / "cost" / "projection.json"
    rates_path = ROOT / "cost" / "rates.csv"
    prompt_path = ROOT / "prompts" / "enrich.md"

    load_local_env(ROOT / ".env")
    if not os.environ.get("TYPESAFE_API_KEY"):
        errors.append("TYPESAFE_API_KEY is missing from the environment or local .env")
    try:
        import typesafe_sdk  # noqa: F401
    except ImportError:
        errors.append("typesafe-sdk is not importable in the active Python environment")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = manifest["files"]["cost_100.csv"]["sha256"]
        actual = hashlib.sha256(sample_path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append("cost_100.csv checksum does not match Data/manifest.json")
        with sample_path.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        ids = [row.get("review_id", "") for row in rows]
        if len(rows) != 100:
            errors.append(f"fixed pilot sample has {len(rows)} rows, expected 100")
        if any(not value for value in ids) or len(set(ids)) != len(ids):
            errors.append("pilot sample IDs are missing or duplicated")
        if any(not (row.get("review_text") or "").strip() for row in rows):
            errors.append("pilot sample contains an empty review text")
    except (OSError, KeyError, json.JSONDecodeError, csv.Error) as exc:
        errors.append(f"could not validate fixed sample and manifest ({type(exc).__name__})")

    try:
        projection = json.loads(projection_path.read_text(encoding="utf-8"))
        controls = projection["controls"]
        if controls.get("budget_usd") != 8.0:
            errors.append("local cumulative budget must be USD 8.00")
        if controls.get("max_workers") != 2:
            errors.append("configured worker maximum must be two")
        if controls.get("fallback_fraction_cap") != 0.0:
            errors.append("fallback cap must remain 0 until separately approved")
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        errors.append(f"could not validate pilot controls ({type(exc).__name__})")

    if not prompt_path.is_file():
        errors.append("enrichment prompt is missing")
    if not rates_path.is_file():
        errors.append("editable provider rates file is missing")

    print("Offline pilot preflight (no API requests made)")
    print("- API key: " + ("present (value hidden)" if os.environ.get("TYPESAFE_API_KEY") else "missing"))
    print("- Fixed sample: " + ("valid 100-row checksum and IDs" if not any("sample" in e or "cost_100" in e or "manifest" in e for e in errors) else "needs attention"))
    print("- Local cumulative budget: USD 8.00")
    print("- Workers: maximum 2; each request carries one review; fallback cap: 0%")
    print("- Pilot execution: not started")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("READY for a separately authorized pilot run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
