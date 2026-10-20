#!/usr/bin/env python3
"""Offline replay for the Spotify pilot cost and runtime calculator."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CALLS = ROOT / "cost" / "pilot_calls.jsonl"
DEFAULT_RUNS = ROOT / "cost" / "pilot_runs.jsonl"
DEFAULT_RATES = ROOT / "cost" / "rates.csv"
DEFAULT_PROJECTION = ROOT / "cost" / "projection.json"
DEFAULT_REPORT = ROOT / "cost" / "report.md"
DEFAULT_RECONCILIATIONS = ROOT / "cost" / "pilot_reconciliations.jsonl"
# Provider request counts are operational metadata, not a Jev billing unit.
RATE_FIELDS = {"input_tokens", "cached_input_tokens", "output_tokens"}
ROLES = ("enrich", "verify", "group", "memo")
STAGES = ("enrich_primary", "enrich_fallback", "verify", "group", "memo")


def stage_key(call: dict[str, Any]) -> str:
    if call.get("role") == "enrich" and call.get("route") == "fallback":
        return "enrich_fallback"
    if call.get("role") == "enrich":
        return "enrich_primary"
    return str(call.get("role", "unspecified"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: each JSONL row must be an object")
            rows.append(value)
    return rows


def read_rates(path: Path) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    rates: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    if not path.exists():
        return rates
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        for line_number, row in enumerate(reader, 2):
            if not any((value or "").strip() for value in row.values()):
                continue
            required = ("provider", "model", "tier", "unit", "price", "currency", "unit_size", "as_of", "source_url")
            if any(not (row.get(name) or "").strip() for name in required):
                raise ValueError(f"{path}:{line_number}: rate rows need all columns filled")
            unit = row["unit"].strip()
            if unit not in RATE_FIELDS:
                raise ValueError(f"{path}:{line_number}: unsupported billing unit {unit!r}")
            try:
                price = Decimal(row["price"])
                unit_size = Decimal(row["unit_size"])
            except InvalidOperation as exc:
                raise ValueError(f"{path}:{line_number}: price and unit_size must be numeric") from exc
            if not price.is_finite() or not unit_size.is_finite() or price < 0 or unit_size <= 0:
                raise ValueError(f"{path}:{line_number}: price must be nonnegative and unit_size positive")
            key = (row["provider"].strip(), row["model"].strip(), row["tier"].strip(), unit)
            if key in rates:
                raise ValueError(f"{path}:{line_number}: duplicate rate key {key}")
            rates[key] = {**row, "price_decimal": price, "unit_size_decimal": unit_size}
    return rates


def decimal_value(value: Any, label: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{label} must be a nonnegative number")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{label} must be a nonnegative number") from exc
    if not result.is_finite() or result < 0:
        raise ValueError(f"{label} must be a nonnegative number")
    return result


def call_cost(call: dict[str, Any], rates: dict[tuple[str, str, str, str], dict[str, Any]]) -> tuple[dict[str, Decimal], list[str], bool]:
    totals: dict[str, Decimal] = defaultdict(Decimal)
    missing: list[str] = []
    has_usage = False
    provider = str(call.get("provider", "")).strip()
    model = str(call.get("model", "")).strip()
    tier = str(call.get("tier", "standard")).strip()
    for unit in RATE_FIELDS:
        if unit not in call or call[unit] is None:
            continue
        has_usage = True
        amount = decimal_value(call[unit], unit)
        if amount == 0:
            continue
        key = (provider, model, tier, unit)
        rate = rates.get(key)
        if rate is None and provider.lower() == "typesafe" and model.lower().startswith("jev-"):
            # TypeSafe publishes the Jev price at the product level; the response
            # reports a resolved version ID while requests may use the jev-latest alias.
            rate = rates.get((provider, "jev", tier, unit))
        if rate is None:
            missing.append(f"{provider}/{model}/{tier}/{unit}")
            continue
        currency = rate["currency"].strip().upper()
        totals[currency] += amount / rate["unit_size_decimal"] * rate["price_decimal"]
    usage_complete = call.get("usage_complete") is True
    return dict(totals), missing, has_usage and usage_complete


def operation_work_units(calls: list[dict[str, Any]], stage: str) -> Decimal:
    """Count logical units once per operation, while including all retry charges."""
    operations: dict[str, Decimal] = {}
    for index, call in enumerate(calls):
        role = call.get("role")
        if stage_key(call) != stage or role not in ROLES or call.get("phase") != "cold":
            continue
        operation_id = str(call.get("operation_id") or f"unkeyed-call-{index}")
        if "work_units" in call:
            units = decimal_value(call["work_units"], "work_units")
        elif role in {"enrich", "verify"}:
            units = Decimal(len(call.get("review_ids", [])))
        else:
            units = Decimal(1)
        operations[operation_id] = max(operations.get(operation_id, Decimal(0)), units)
    return sum(operations.values(), Decimal(0))


def calibrate_roles(calls: list[dict[str, Any]], rates: dict[tuple[str, str, str, str], dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Calibrate cost per logical cold-run work unit; retries remain in the numerator."""
    calibrated: dict[str, dict[str, Any]] = {}
    for stage in STAGES:
        # Unknown failed attempts remain visible in the report, but cannot be
        # included in a measured price-per-work-unit calibration.
        role_calls = [call for call in calls if call.get("phase") == "cold" and stage_key(call) == stage and call.get("usage_complete") is True]
        units = operation_work_units(role_calls, stage)
        totals: dict[str, Decimal] = defaultdict(Decimal)
        fully_priced = bool(role_calls) and units > 0
        for call in role_calls:
            costs, missing, complete = call_cost(call, rates)
            fully_priced = fully_priced and complete and not missing
            for currency, amount in costs.items():
                totals[currency] += amount
        per_unit = {currency: amount / units for currency, amount in totals.items()} if fully_priced else {}
        calibrated[stage] = {"units": units, "per_unit": per_unit, "fully_priced": fully_priced}
    return calibrated


def projection_lines(projection: dict[str, Any], calibration: dict[str, dict[str, Any]], runs: list[dict[str, Any]], rates: dict[tuple[str, str, str, str], dict[str, Any]]) -> list[str]:
    lines = ["", "| Scenario | API projection | Estimated wall time | Budget check | Status |", "|---|---|---|---|---|"]
    scenarios = projection.get("scenarios", {})
    controls = projection.get("controls", {})
    budget = controls.get("remaining_budget_usd_before_10000", controls.get("budget_usd"))
    cold_runs = [run for run in runs if run.get("phase") == "cold" and not run.get("stopped_with_error")]
    metrics = cold_runs[-1].get("stage_metrics", {}) if cold_runs else {}
    any_projection = False
    for name, scenario in scenarios.items():
        work = scenario.get("work_units", {})
        retry = scenario.get("retry_multiplier_by_role", {})
        cost_totals: dict[str, Decimal] = defaultdict(Decimal)
        missing: list[str] = []
        estimated_seconds = Decimal(0)
        time_missing: list[str] = []
        for role in STAGES:
            units = work.get(role)
            if units is None:
                missing.append(f"{role} work units")
                continue
            units_d = decimal_value(units, f"{name}.{role} work units")
            if units_d == 0:
                continue
            role_cal = calibration.get(role, {})
            if not role_cal.get("fully_priced"):
                missing.append(f"{role} cold pilot rate or complete usage")
            else:
                multiplier_value = retry.get(role)
                if multiplier_value is None:
                    missing.append(f"{role} retry multiplier")
                else:
                    multiplier = decimal_value(multiplier_value, f"{name}.{role} retry multiplier")
                    for currency, unit_cost in role_cal["per_unit"].items():
                        cost_totals[currency] += unit_cost * units_d * multiplier
            stage = metrics.get(role, {})
            stage_units = stage.get("work_units")
            stage_seconds = stage.get("wall_seconds")
            if stage_units in (None, 0) or stage_seconds is None:
                time_missing.append(role)
            else:
                estimated_seconds += units_d * Decimal(str(stage_seconds)) / Decimal(str(stage_units))
        if cost_totals and not missing:
            any_projection = True
            spend = currency_text(dict(cost_totals))
            if budget is not None and len(cost_totals) == 1 and "USD" in cost_totals:
                budget_status = "OVER BUDGET" if cost_totals["USD"] > decimal_value(budget, "budget_usd") else "within budget"
            elif budget is None:
                budget_status = "budget not set"
            else:
                budget_status = "cannot compare currencies"
            wall_text = f"{estimated_seconds.quantize(Decimal('0.01'))} sec" if not time_missing else "unavailable (stage timings missing)"
            status = "complete projection" if not time_missing else "cost complete; time incomplete"
        else:
            spend = "unavailable"
            budget_status = "not assessed"
            wall_text = "unavailable"
            status = "assumptions or measured rates missing: " + ", ".join(missing or ["priced pilot data"])
        lines.append(f"| {name} | {spend} | {wall_text} | {budget_status} | {status} |")
    if not scenarios:
        lines.append("| none configured | unavailable | unavailable | not assessed | no scenarios configured |")
    lines.extend(["", "Projection cost uses per-stage charges per logical work unit from cold calls, including retries logged under each operation. Runtime uses recorded stage wall times and does not assume unmeasured concurrency speedups.", ""])
    if not any_projection:
        lines.append("No complete scenario can be calculated yet. Fill stage work-unit and retry assumptions after the pilot, and record priced cold-run usage for each stage.")
    return lines


def currency_text(values: dict[str, Decimal]) -> str:
    if not values:
        return "unavailable"
    return ", ".join(f"{currency} {amount.quantize(Decimal('0.000001'))}" for currency, amount in sorted(values.items()))


def make_report(calls: list[dict[str, Any]], runs: list[dict[str, Any]], rates: dict[tuple[str, str, str, str], dict[str, Any]], projection: dict[str, Any], reconciliations: list[dict[str, Any]] | None = None) -> str:
    lines = ["# Pilot cost and runtime report", "", "This report is calculated offline from saved call usage, run measurements, and editable rates.", ""]
    if not calls:
        lines.extend(["## Measurement status", "", "No call log is present. Pilot usage and API spend are **not measured**; missing values are not treated as zero.", ""])
    if not rates:
        lines.extend(["No rates are configured in `cost/rates.csv`; any API cost is **unpriced**, not free.", ""])

    grouped: dict[tuple[str, str, str, str, str, str], dict[str, Any]] = {}
    total_by_currency: dict[str, Decimal] = defaultdict(Decimal)
    missing_rate_items: Counter[str] = Counter()
    unresolved_usage = 0
    for call in calls:
        phase = str(call.get("phase", "unspecified"))
        role = str(call.get("role", "unspecified"))
        route = str(call.get("route", "primary")) if role == "enrich" else ""
        provider = str(call.get("provider", "unspecified"))
        model = str(call.get("model", "unspecified"))
        run_id = str(call.get("run_id", "unspecified"))
        key = (run_id, phase, role, route, provider, model)
        bucket = grouped.setdefault(key, {"calls": 0, "outcomes": Counter(), "tokens": Counter(), "cost": defaultdict(Decimal), "unknown": False, "efforts": set(), "prompt_versions": set(), "schema_versions": set(), "batch_sizes": set(), "workers": set()})
        bucket["calls"] += 1
        bucket["outcomes"][str(call.get("outcome", "unknown"))] += 1
        for field, target in (("effort", "efforts"), ("prompt_version", "prompt_versions"), ("schema_version", "schema_versions"), ("batch_size", "batch_sizes"), ("worker_count", "workers")):
            if call.get(field) is not None:
                bucket[target].add(str(call[field]))
        for usage_field in ("input_tokens", "cached_input_tokens", "output_tokens", "requests"):
            if call.get(usage_field) is not None:
                bucket["tokens"][usage_field] += int(decimal_value(call[usage_field], usage_field))
        costs, missing, complete = call_cost(call, rates)
        for currency, amount in costs.items():
            bucket["cost"][currency] += amount
            total_by_currency[currency] += amount
        if missing:
            bucket["unknown"] = True
            missing_rate_items.update(missing)
        if not complete:
            bucket["unknown"] = True
            unresolved_usage += 1

    if grouped:
        lines.extend(["## Saved call usage", "", "| Run | Phase | Role | Provider | Model | Effort | Prompt version | Schema version | Batch sizes | Workers | Attempts | Outcomes | Input tokens | Cached input tokens | Output tokens | Billed requests | Known cost | Status |", "|---|---|---|---|---|---|---|---|---|---|---:|---|---:|---:|---:|---:|---|---|"])
        for (run_id, phase, role, route, provider, model), bucket in sorted(grouped.items()):
            tokens = bucket["tokens"]
            outcomes = ", ".join(f"{k}: {v}" for k, v in sorted(bucket["outcomes"].items()))
            status = "partial or unresolved" if bucket["unknown"] else "priced usage"
            role_label = f"{role} ({route})" if route else role
            def metadata(field: str) -> str:
                return ", ".join(sorted(bucket[field])) or "unrecorded"
            lines.append(f"| {run_id} | {phase} | {role_label} | {provider} | {model} | {metadata('efforts')} | {metadata('prompt_versions')} | {metadata('schema_versions')} | {metadata('batch_sizes')} | {metadata('workers')} | {bucket['calls']} | {outcomes} | {tokens['input_tokens']} | {tokens['cached_input_tokens']} | {tokens['output_tokens']} | {tokens['requests']} | {currency_text(bucket['cost'])} | {status} |")
        lines.extend(["", f"**Known API subtotal:** {currency_text(dict(total_by_currency))}.", f"**Calls with incomplete or missing usage:** {unresolved_usage}.", ""])
    if missing_rate_items:
        lines.extend(["Unpriced usage items:", ""])
        lines.extend(f"- `{item}`: {count} call(s)" for item, count in sorted(missing_rate_items.items()))
        lines.append("")
    if reconciliations:
        lines.extend(["## Usage dashboard reconciliation", "", "These notes record dashboard readings and checks of failed calls. TypeSafe warns that usage may be delayed. Failed requests keep their estimated reserve against the local cap until token usage appears; a dashboard total that trails the call ledger is not treated as a final reconciliation.", ""])
        for item in reconciliations:
            reserve = item.get("potential_cost_reserve_usd")
            reserve_text = f" Reserved against the local cap: USD {reserve}." if reserve is not None else ""
            call_id = item.get("local_call_id")
            subject = f"Call `{call_id}`" if call_id else "Dashboard snapshot"
            lines.append(f"- {subject}: {item.get('evidence', 'No evidence note saved.')}{reserve_text}")
        lines.append("")
    if rates:
        lines.extend(["## Rate sources", "", "| Provider | Model | Tier | Billing unit | Price | Currency | Unit size | As of | Source |", "|---|---|---|---|---:|---|---:|---|---|"])
        for key, rate in sorted(rates.items()):
            provider, model, tier, unit = key
            lines.append(f"| {provider} | {model} | {tier} | {unit} | {rate['price']} | {rate['currency']} | {rate['unit_size']} | {rate['as_of']} | {rate['source_url']} |")
        lines.append("")

    if runs:
        lines.extend(["## Measured runs", "", "| Run | Phase | Input rows | Input SHA-256 | Pilot IDs | Completed | Failed | Unique texts | Cache hits | Workers | Wall seconds | Throughput (inputs/sec) | Cost per 1,000 inputs | Cost per completed record | Local compute |", "|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|"])
        run_cost: dict[str, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
        run_unknown: set[str] = set()
        for (run_id, _phase, _role, _route, _provider, _model), bucket in grouped.items():
            for currency, amount in bucket["cost"].items():
                run_cost[run_id][currency] += amount
            if bucket["unknown"]:
                run_unknown.add(run_id)
        for run in runs:
            phase = str(run.get("phase", "unspecified"))
            run_id = str(run.get("run_id", "unspecified"))
            inputs = run.get("input_rows")
            completed = run.get("completed_records")
            zero_call_run = run.get("new_provider_calls") == 0 and run_id not in run_unknown
            cost_known = run_id not in run_unknown and (bool(run_cost[run_id]) or zero_call_run)
            cost = currency_text(dict(run_cost[run_id])) if run_cost[run_id] else ("USD 0.000000" if zero_call_run else "unavailable or partial")
            per_thousand = "unavailable"
            per_completed = "unavailable"
            throughput = "unavailable"
            wall_seconds = run.get("wall_seconds")
            if inputs is not None and wall_seconds not in (None, 0):
                throughput = str((Decimal(str(inputs)) / Decimal(str(wall_seconds))).quantize(Decimal("0.01")))
            if cost_known and len(run_cost[run_id]) == 1:
                amount = next(iter(run_cost[run_id].values()))
                currency = next(iter(run_cost[run_id]))
                if inputs:
                    per_thousand = f"{currency} {(amount * 1000 / Decimal(str(inputs))).quantize(Decimal('0.000001'))}"
                if completed:
                    per_completed = f"{currency} {(amount / Decimal(str(completed))).quantize(Decimal('0.000001'))}"
            local_compute = run.get("local_compute_cost")
            local_compute_text = str(local_compute) if local_compute is not None else "unknown/not recorded"
            input_ids = run.get("input_review_ids", [])
            id_count = len(set(input_ids)) if isinstance(input_ids, list) else "unknown"
            lines.append(f"| {run.get('run_id','unspecified')} | {phase} | {inputs if inputs is not None else 'unknown'} | {run.get('input_sha256','unknown')} | {id_count} | {completed if completed is not None else 'unknown'} | {run.get('failed_records','unknown')} | {run.get('unique_texts','unknown')} | {run.get('cache_hits','unknown')} | {run.get('worker_count','unknown')} | {wall_seconds if wall_seconds is not None else 'unmeasured'} | {throughput} | {per_thousand} | {per_completed} | {local_compute_text} |")
        lines.extend(["", "Costs are phase totals across logged model roles. Request-duration sums are not substituted for wall-clock time. Local compute is reported separately and remains unknown unless measured or estimated in the run log.", ""])
    else:
        lines.extend(["## Measured runs", "", "No run timing file is present. Cold/warm wall time, throughput, and per-record rates are **not measured**.", ""])

    lines.extend(["## Projection readiness", ""])
    population = projection.get("target_population", {})
    if population:
        lines.append("Target counts from the editable projection file: " + ", ".join(f"{key}={value}" for key, value in population.items()) + ".")
    controls = projection.get("controls", {})
    lines.append("Spend budget: " + (f"USD {controls['budget_usd']}" if controls.get("budget_usd") is not None else "not set") + ".")
    priced_calls = [call for call in calls if call.get("usage_complete") is True]
    cold_roles = {stage: operation_work_units(priced_calls, stage) for stage in STAGES}
    if not calls or not rates:
        lines.append("Base and conservative dollar/time projections are not available until a measured pilot, dated rates, and stage work assumptions are recorded.")
    else:
        lines.append("Observed cold work units by role: " + ", ".join(f"{role}={units}" for role, units in cold_roles.items()) + ".")
        lines.append("Only calls with complete token usage are used to calibrate per-work-unit cost. Failed calls with missing usage remain listed as unresolved and are excluded from calibration. Request counts are recorded as operational metadata, not priced as token usage.")
    lines.extend(projection_lines(projection, calibrate_roles(calls, rates), runs, rates))
    lines.extend(["", "## Controls", "", f"- Maximum workers: {controls.get('max_workers', 'unset')}", f"- Maximum output tokens: {controls.get('max_output_tokens') if controls.get('max_output_tokens') is not None else 'not set'}", f"- Fallback fraction cap: {controls.get('fallback_fraction_cap') if controls.get('fallback_fraction_cap') is not None else 'not set'}", "- No paid API calls were made by this report.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    replay = subparsers.add_parser("replay", help="recompute saved pilot costs offline")
    replay.add_argument("--calls", type=Path, default=DEFAULT_CALLS)
    replay.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    replay.add_argument("--rates", type=Path, default=DEFAULT_RATES)
    replay.add_argument("--projection", type=Path, default=DEFAULT_PROJECTION)
    replay.add_argument("--reconciliations", type=Path, default=DEFAULT_RECONCILIATIONS)
    replay.add_argument("--out", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    if args.command == "replay":
        calls = read_jsonl(args.calls)
        runs = read_jsonl(args.runs)
        rates = read_rates(args.rates)
        projection = json.loads(args.projection.read_text(encoding="utf-8")) if args.projection.exists() else {}
        reconciliations = read_jsonl(args.reconciliations)
        report = make_report(calls, runs, rates, projection, reconciliations)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8", newline="\n")
        print(f"Wrote offline report: {args.out}")
        print("No model or provider API was contacted.")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
