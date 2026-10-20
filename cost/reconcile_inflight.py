#!/usr/bin/env python3
"""Reconcile a worker request left pending by an interrupted paid run.

This utility is offline. It never contacts TypeSafe. Supply either exact usage
from the provider or evidence that the provider confirmed no usage.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
import os
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COST = ROOT / "cost"
INFLIGHT = COST / "pilot_inflight.json"
CALLS = COST / "pilot_calls.jsonl"
RECONCILIATIONS = COST / "pilot_reconciliations.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def append_jsonl(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        stream.flush()


def write_jsonl_atomic(path: Path, rows: list[dict]) -> None:
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        Path(name).replace(path)
    except Exception:
        Path(name).unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--call-id", required=True, help="local_call_id shown by the pending-call list")
    parser.add_argument("--evidence", required=True, help="briefly state where confirmed usage information came from")
    outcome = parser.add_mutually_exclusive_group()
    outcome.add_argument("--confirm-no-usage", action="store_true", help="provider confirms no charge/request usage")
    parser.add_argument("--input-tokens", type=int, help="exact input token usage reported by TypeSafe")
    parser.add_argument("--output-tokens", type=int, help="exact output token usage reported by TypeSafe")
    args = parser.parse_args()
    if not args.evidence.strip():
        parser.error("--evidence cannot be blank")
    if args.confirm_no_usage and (args.input_tokens is not None or args.output_tokens is not None):
        parser.error("do not combine --confirm-no-usage with token counts")
    if not args.confirm_no_usage and (args.input_tokens is None or args.output_tokens is None):
        parser.error("provide --confirm-no-usage or both token counts")
    if args.input_tokens is not None and (args.input_tokens < 0 or args.output_tokens is None or args.output_tokens < 0):
        parser.error("provide nonnegative --input-tokens and --output-tokens together")
    if not INFLIGHT.exists():
        raise SystemExit("No in-flight journal exists")
    journal = json.loads(INFLIGHT.read_text(encoding="utf-8"))
    calls = journal.get("calls", [])
    pending = next((call for call in calls if call.get("local_call_id") == args.call_id), None)
    if pending is None:
        raise SystemExit("That call ID is not pending in the in-flight journal")

    call_log = read_jsonl(CALLS)
    existing_call = next((row for row in call_log if row.get("local_call_id") == args.call_id), None)
    has_usage = args.input_tokens is not None
    if existing_call and existing_call.get("usage_complete") is True:
        if not has_usage:
            parser.error("the call ledger already contains usage; do not reconcile it as no usage")
        if existing_call.get("input_tokens") != args.input_tokens or existing_call.get("output_tokens") != args.output_tokens:
            parser.error("provided token counts do not match the already logged call")
    reconciliations = read_jsonl(RECONCILIATIONS)

    resolution = "usage_reconciled_after_interruption" if has_usage else "request_confirmed_no_usage_after_interruption"
    reconciliation = {
        "resolution": resolution,
        "local_call_id": args.call_id,
        "potential_cost_reserve_usd": pending.get("estimated_reserve_usd", "0") if not has_usage else "0",
        "evidence": args.evidence.strip(),
        "reconciled_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    prior_reconciliation = next((row for row in reconciliations if row.get("local_call_id") == args.call_id), None)
    if prior_reconciliation:
        if prior_reconciliation.get("resolution") != resolution:
            parser.error("this call ID already has a different reconciliation outcome")
    else:
        append_jsonl(RECONCILIATIONS, reconciliation)

    if existing_call is None:
        ledger_row = {
            **pending,
            "outcome": "failed_reconciled" if has_usage else "failed_reconciled_no_usage",
            "input_tokens": args.input_tokens if has_usage else None,
            "cached_input_tokens": 0,
            "output_tokens": args.output_tokens if has_usage else None,
            "requests": 1,
            "usage_complete": has_usage,
            "duration_seconds": None,
            "error_type": "interrupted_before_response_logging",
        }
        append_jsonl(CALLS, ledger_row)
    elif existing_call.get("usage_complete") is True:
        pass
    else:
        existing_call.update({
            "outcome": "failed_reconciled" if has_usage else "failed_reconciled_no_usage",
            "input_tokens": args.input_tokens if has_usage else None,
            "cached_input_tokens": 0,
            "output_tokens": args.output_tokens if has_usage else None,
            "requests": 1,
            "usage_complete": has_usage,
            "error_type": "interrupted_before_response_logging",
        })
        write_jsonl_atomic(CALLS, call_log)

    remaining = [call for call in calls if call.get("local_call_id") != args.call_id]
    if remaining:
        journal["calls"] = remaining
        journal["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
        temp = INFLIGHT.with_suffix(".tmp")
        with temp.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(journal, ensure_ascii=False, separators=(",", ":")) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        temp.replace(INFLIGHT)
    else:
        INFLIGHT.unlink(missing_ok=True)
    print("Reconciled one pending call offline; review pilot_calls.jsonl and pilot_reconciliations.jsonl before resuming.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
