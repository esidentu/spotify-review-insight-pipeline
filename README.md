# Spotify Review Insight Pipeline

This project analyzes the supplied historical Spotify review extract using a staged, auditable pipeline. The 100-, 500-, and 10,000-review Jev checkpoints have been run and saved. See [PROJECT_GUIDE.md](PROJECT_GUIDE.md) for a plain-language walkthrough of the work, labels, costs, and next steps.

## Project status

- Source dataset is in `Data/`; its full CSV is excluded from Git by `.gitignore`.
- The reviewed golden labels are in `Data/golden_50_labeled.csv`. They are evaluation-only and must not be included in development prompts, routing rules, or issue discovery.
- The 100-, 500-, and 10,000-review results, cost report, and call/run logs are saved under `cost/`.
- Read `Data/GRADING_CONTRACT.md` and `Data/COST_CALCULATOR.md` before running model work.
- See [`SUBMISSION_READINESS.md`](SUBMISSION_READINESS.md) for a requirement-by-requirement audit and remaining work.

## Low-cost design

Use Python or SQL for CSV parsing, source accounting, exact-text deduplication and cache lookup, schema checks, grouping, aggregation, and ranking. The assignment suggests Jev for fixed labels and a small language model for bounded judgment tasks; those are candidates to measure, not hard requirements. Distinct enrichment, verification, grouping, and memo roles will have separate instructions and saved artifacts, and may share a model. Exact-text cache hits still produce one output per original review ID.

## Local setup

Use Python 3.11 or newer. The local pipeline uses the project virtual environment and the TypeSafe Python SDK for Jev requests. The offline cost report uses only local saved files and makes no provider requests.

1. Copy `.env.example` to `.env` and add only the keys for the provider you select. Keep `.env` local.
2. Set the pilot spend ceiling and editable rates in `cost/projection.json` and `cost/rates.csv` before a paid run.
3. Use the offline calculator instructions in `cost/README.md` to replay saved usage without credentials or API calls.

The current cumulative local stop limit is USD 8.00. The earlier 100-, 500-, and 10,000-review runs were performed under the previous USD 1.00 cap. The deterministic 100,000-review input can be prepared offline with `\.venv\Scripts\python.exe Data\prepare_final_100000.py`. Run the offline readiness check with `\.venv\Scripts\python.exe cost\pilot_preflight.py`; it does not contact TypeSafe. Paid cold commands are documented in `cost/README.md`; warm runs and offline cost replay make no provider calls. The cap is local and does not configure provider-side billing limits.

Never put API keys in code, logs, prompts, browser code, screenshots, or submitted artifacts.

## Required scale checkpoints

Measure the fixed cold and warm `cost_100.csv` pilot first, then refresh estimates at 500 and 10,000 reviews. The assignment accepts a final classification run of at least 100,000 nonempty reviews; the full source has 660,609 nonempty reviews and 13 empty-text quarantines. Requests must contain at most 50 reviews. Start with one worker, then try two within measured capacity. The current runner keeps one review per request and overlaps up to two independent calls; each result is validated and durably saved before its slot is reused. Resume requires the same input, cache, labels, and worker count.

The reproducible ranking, evaluation results, interruption/recovery evidence, and local database-backed dashboard are in the repository. The deployed dashboard/backend/database requirement remains open; see [`SUBMISSION_READINESS.md`](SUBMISSION_READINESS.md).

## 100,000-row grading export

The selected 100,000-row input is `Data/final_100000.csv`. Its grading adapter is in [`grading/`](grading/), including the exact run manifest, full-source ingestion profile, completed records, membership, ranking, claims, actual provider-call evidence, checkpoint snapshots, and decision memo. Review the Golden 50 and `needs_review` analysis in [`cost/review_100000_quality.md`](cost/review_100000_quality.md).

Run the zero-API self-check with the prepared local reference:

```powershell
.\.venv\Scripts\python.exe Data\check_submission.py check --reference grading-reference.json --submission grading --out grading-self-check.json
```

The check reports 100,000/100,000 completed IDs and `review_required` for unavailable usage on failed calls and missing group/memo model-call roles. Those stages used local deterministic code and are documented in `grading/local_stages.jsonl`; the report is saved outside the grading folder at `grading-self-check.json`.

The historical run used the original prompts in `prompts/enrich.md` and `prompts/verify.md`. The contract's explicit bare-boycott exception was added afterward in `prompts/enrich-v2.md` and `prompts/verify-v2.md`; those versioned prompts do not retroactively change the saved labels or call evidence.

## Local evidence dashboard

Build a SQLite database from the saved 100,000-row outputs and run the local read-only dashboard:

```powershell
.\.venv\Scripts\python.exe dashboard\build_database.py
.\.venv\Scripts\python.exe dashboard\server.py
```

Open `http://127.0.0.1:8765/`. See [`dashboard/README.md`](dashboard/README.md) for its API and current limits. This is a local implementation, not the required deployed dashboard. Its saved recommendation is the local memo output, not a model-generated recommendation.

## Rebuild ranking without model calls

Once `grading/records.jsonl` and `grading/membership.csv` exist, regenerate the baseline ranking with:

```powershell
python src/spotify_pipeline/ranking.py --records grading/records.jsonl --membership grading/membership.csv --out grading/ranking.csv
```

The ranker uses temporary SQLite storage, validates memberships and severities, and applies the contract's descending severity-sum order with ascending issue ID as the tie-break.
