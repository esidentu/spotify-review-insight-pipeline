# Offline cost calculator

The 100-review pilot and the 500- and 10,000-review checkpoints were run under a **USD 1.00** local cap. The current approved cumulative local cap is **USD 8.00**, recorded in `projection.json`; this is not a TypeSafe billing setting and cannot guarantee against delayed provider billing. The fallback cap is 0%. TypeSafe's published Jev rates are recorded in `rates.csv` with their source and date.

Before any API request, run the offline preflight:

```powershell
.\.venv\Scripts\python.exe cost\pilot_preflight.py
```

Preflight reads the fixed sample, local settings, and credential presence without displaying the credential or contacting TypeSafe. It does not execute the pilot. Pilot execution remains a separate explicit step.

When you explicitly want to start the paid cold pass, run:

```powershell
.\.venv\Scripts\python.exe cost\pilot.py cold --execute
```

This sends one Jev enrichment request per unique review text and a second Jev consistency check for a deterministic 10% sample. It uses up to two workers by default (`--workers 1` selects sequential processing), while each request keeps the same one-review prompt, model, and schema. It enforces the USD 8.00 cumulative local cap, reserves the next wave's estimated cost before dispatch, and stops after any failed or unpriced response. Automatic SDK retries are disabled. The main process alone writes the call ledger and validated progress; each result is flushed to disk before a worker slot is reused. A separate in-flight journal blocks resume if a process exits before dispatched calls are reconciled. Resume must use the same input, cache path/content, label configuration, and worker count. The call is a real paid request; `.env` must contain a valid `TYPESAFE_API_KEY`.

After a complete cold pass, measure result-cache reuse with:

```powershell
.\.venv\Scripts\python.exe cost\pilot.py warm
```

The warm command validates all 100 cached rows and logs a zero-call, zero-incremental-API-cost run. It does not contact TypeSafe. Both commands are separate from the offline replay below.

For the 500-review checkpoint, the first 100 rows are reused from the completed 100-review pilot; only uncached exact texts are sent to Jev. At the time, the cumulative USD 1.00 local stop limit, one-worker setting, and call ledger applied:

```powershell
.\.venv\Scripts\python.exe cost\pilot.py cold --input Data\checkpoint_500.csv --cache-from cost\pilot_records.jsonl --execute
.\.venv\Scripts\python.exe cost\pilot.py warm --input Data\checkpoint_500.csv
```

The 500-row results and local aggregate artifacts are written to `pilot_records_500.jsonl`, `pilot_membership_500.csv`, `pilot_ranking_500.csv`, and `pilot_memo_500.md`. Calls and measured runs remain in the shared logs. The checkpoint input is validated against its manifest checksum before any requests.

For the 10,000-review development checkpoint, 479 distinct texts from the 500 checkpoint are reused. The offline preflight computes a whole-run reserve before the first paid call and accounts for the reserved amount of any failed request whose dashboard usage is still unavailable. The TypeSafe Usage page can lag; the call ledger remains the source for returned token usage. Start the checkpoint with:

```powershell
.\.venv\Scripts\python.exe cost\pilot.py cold --input Data\analysis_10000.csv --cache-from cost\pilot_records_500.jsonl --execute
```

If a connection error stops the run, check the saved call ledger and provider usage, then resume saved state with:

```powershell
.\.venv\Scripts\python.exe cost\pilot.py cold --input Data\analysis_10000.csv --resume --execute
```

After all rows are completed, validate the saved cache without provider calls:

```powershell
.\.venv\Scripts\python.exe cost\pilot.py warm --input Data\analysis_10000.csv
```

For the selected 100,000-review run, prepare the deterministic input offline from the already loaded full CSV. This writes `Data/final_100000.csv` and adds its source and output checksums to the manifest; it does not contact TypeSafe:

```powershell
.\.venv\Scripts\python.exe Data\prepare_final_100000.py
```

Run the whole-run offline preflight before paying. It validates the manifest and cache, reports the planned work and cost reserve, and checks the two-worker configuration without writing run state or contacting TypeSafe:

```powershell
.\.venv\Scripts\python.exe cost\pilot.py cold --input Data\final_100000.csv --cache-from cost\pilot_records_10000_complete.jsonl --workers 2 --preflight-only
```

The paid runner accepts the prepared input and reuses compatible records from the 10,000 checkpoint:

```powershell
.\.venv\Scripts\python.exe cost\pilot.py cold --input Data\final_100000.csv --cache-from cost\pilot_records_10000_complete.jsonl --workers 2 --execute
```

If the run pauses with saved progress, first reconcile any pending in-flight calls with the offline helper below. Then resume with the identical input, cache, and worker count:

```powershell
.\.venv\Scripts\python.exe cost\pilot.py cold --input Data\final_100000.csv --cache-from cost\pilot_records_10000_complete.jsonl --workers 2 --resume --execute
```

After completion, validate the saved results without API calls:

```powershell
.\.venv\Scripts\python.exe cost\pilot.py warm --input Data\final_100000.csv
```

The current local cumulative cap is USD 8.00 and the configured maximum worker count is two. The production runner retains one review per request, as in the one-worker runs, and only changes the number of independent calls in flight. It disables SDK retries and uses a 60-second request timeout. The original one-request-per-unique-review implementation projected 6.5–8.8 hours. The separate five-review benchmark below does not estimate this runner's full-scale timing.

`batch_benchmark_50.py` compared one and two workers on the same 50 Golden review texts and the same ten five-review batches. Jev received only IDs and text; expected labels were joined locally after each response. Both conditions completed with complete usage: one worker took 1.671 seconds and two workers took 0.836 seconds, at USD 0.002229318 per condition. This was an exploratory multi-review batching experiment, not a direct comparison for the production runner, which uses one review per request. The earlier failed DNS attempt remains in the call ledger with its USD 0.000702744 reserve; it was not retried.

`worker_comparison_50.py` makes the production-shape comparison: it uses the same 50 review IDs, the same one-review state, same questions, Jev alias, prompt and schema, once with one worker and once with two. It never sends Golden labels. Both runs completed with usage for all 50 calls. One worker took 6.110 seconds and two workers took 3.108 seconds (about 49% less wall time); both cost USD 0.002134650. Agreement with the Golden labels was topic 90% in both, intent 92% in both, severity 88% with one worker and 86% with two, and sentiment MAE 0.1604 and 0.1597. Independent model responses can differ even on identical requests, so the one severity difference is output variation, not evidence that concurrent requests changed the classification rules. Results: `worker_comparison_50_w1.csv` / `.json` and `worker_comparison_50_w2.csv` / `.json`. This bounded sample supports trying two workers; it does not certify 100,000-row accuracy or runtime.

For interruption recovery, `pilot_records_100000_progress.jsonl` stores each newly processed representative record as an append-only checkpoint, `pilot_state_100000.json` pins the input/cache/label/worker configuration, and `pilot_inflight.json` stores cost reservations for requests sent but not yet reconciled. If an in-flight journal remains after a crash, inspect it and the TypeSafe provider usage first. Reconcile each call only with provider-confirmed evidence:

```powershell
.\.venv\Scripts\python.exe cost\reconcile_inflight.py --call-id CALL_ID --input-tokens INPUT_TOKENS --output-tokens OUTPUT_TOKENS --evidence "TypeSafe usage export"
```

Or, when the provider explicitly confirms the request incurred no usage:

```powershell
.\.venv\Scripts\python.exe cost\reconcile_inflight.py --call-id CALL_ID --confirm-no-usage --evidence "Provider support confirmed no usage"
```

The helper is offline and does not infer usage. Its pending IDs, usage, and evidence are added to the existing local ledgers; only then may the saved run be resumed.

If a completed call attempt returns a connection error without enough provider detail to prove whether usage was recorded, preserve the full estimated reserve in `pilot_reconciliations.jsonl` with resolution `request_usage_unknown_reserve_held`. `pilot.py` carries that reserve into the USD 8 cap check, and the next resume reserves the new attempt separately. Do not mark an ambiguous timeout as confirmed no-usage.

The completed 10,000-row outputs use the `_10000` suffix. This checkpoint had 8,448 distinct texts, reused 479 of them from the 500 checkpoint, made 7,969 enrichment calls and 797 new verification calls, and completed in about 41 minutes across its start/resume attempts. Its measured incremental Jev token cost was **USD 0.356404230**; cumulative known pilot cost was **USD 0.377804742**. Warm validation took 0.037 seconds and made no provider calls. The cost report includes 100,000-review estimates of about USD 3.27–4.47 depending on the deduplication assumption, plus a USD 21.65 estimate for the full population. These are extrapolations from measured pilot calls; the 100,000 input's actual duplicate rate will determine the final cost.

The TypeSafe Usage page later showed USD 0.2166, 5,967,246 tokens, and 5,088 requests for its “Last 24 hours” view, while warning that statistics may be delayed. The local call ledger calculates USD 0.377804742 from successful response usage. The provider dashboard has not caught up to the full local ledger yet, so use the local amount as the reproducible estimate and keep the dashboard difference noted.

The 100,000-review run completed on 2026-10-20 with two workers. It produced 100,000 completed output records from 78,099 distinct texts. It made 69,651 successful enrichment calls and 6,965 successful verification calls; the nine failed attempts were resumed without automatic retries, and all final records completed. The run's known Jev token cost was USD 3.119385; cumulative known project cost is USD 3.505917. Unknown usage for failed calls remains conservatively reserved; USD 4.492264 remained under the local cap after those reserves. The TypeSafe Usage page later showed USD 3.228, 88,910,604 tokens, and 75,711 requests, with its delayed-stats notice still visible. The dashboard and local ledger differ; the local ledger is the reproducible run accounting.

`grading/records.jsonl` is the published canonical 100,000-row output. `pilot_labeled_100000.csv` has the same review fields and labels in the same shape as the 10,000-row CSV. The export prefixes formula-leading text with an apostrophe so Excel treats it as text; the canonical JSONL retains exact source text. Rebuild the CSV without API calls with:

```powershell
.\.venv\Scripts\python.exe cost\export_labeled_100000.py
```

The CSV contains 100,000 rows, including 20,683 rows with `needs_review=true`. Of these, 12,373 have at least one Jev field confidence below 0.5; 8,310 have all four field confidences at or above 0.5 but a verification support probability below 0.5. The 10% verification sample completed. See `review_100000_quality.md` for the Golden 50 comparison and inspected examples.

The calculator recomputes cost only from saved call usage and editable rates. It never contacts a model provider. The 100-, 500-, and 10,000-review runs provide token and time measurements. Reconciled failed calls remain visible and their small estimated request reserves count against the local stop limit until usage appears.

## Offline replay

After a pilot has created the call and run logs, run:

```powershell
python cost/calculator.py replay
```

Optional paths:

```powershell
python cost/calculator.py replay --calls cost/pilot_calls.jsonl --runs cost/pilot_runs.jsonl --rates cost/rates.csv --projection cost/projection.json --out cost/report.md
```

The default command is offline. It reads local files, applies current editable rates, writes a report, and makes no API calls. `python cost/calculator.py --help` lists options.

## Evidence files

- `pilot_calls.jsonl`: every actual call attempt, including failed attempts, retries, and fallbacks. Record provider, exact model, role, cold/warm phase, operation ID, review IDs, usage, outcome, request ID, and call duration. Record token classes separately; `input_tokens` must exclude `cached_input_tokens`.
- `pilot_runs.jsonl`: measured wall-clock time and stage-level work counts/durations for each run. Call durations are not a substitute for elapsed wall-clock time.
- `rates.csv`: one row per provider/model/tier/billing unit, with price, currency, unit size, effective date, and official source URL. Leave unknown rates blank; do not enter zero to mean unknown.
- `projection.json`: target population, budget and output/concurrency controls, plus base and conservative stage work assumptions. Unknown assumptions stay `null` until measured or explicitly chosen.

The starter projections use the manifest's 484,189 unique texts for the base enrichment volume and 660,609 nonempty reviews for the no-reuse comparison. Verification and fallback counts are intentionally `null` until their rates are selected and measured. Do not read an incomplete scenario as a cost estimate.

The report separates known charges from missing usage or rates. It does not treat unpriced usage as free. For token rates, `unit_size=1000000` represents a price per million tokens. Billing categories are mutually exclusive: uncached input, cached input, and output.

Each call record uses the grading role names `enrich`, `verify`, `group`, or `memo`. A stronger-model enrichment fallback remains `role: "enrich"` and sets `route: "fallback"`. Log every retry with the same `operation_id` so the calculator can include its charge without counting the logical work twice. `work_units` may be set explicitly; otherwise enrichment and verification count their `review_ids`, while grouping and memo calls count as one work unit. Set `usage_complete` to `true` only when provider usage is fully known for that attempt.

Example call record shape (replace the placeholder values with actual call evidence; this example is not a measured result):

```json
{"run_id":"cold-100-v1","operation_id":"enrich-batch-0001","phase":"cold","role":"enrich","route":"primary","provider":"provider-name","model":"exact-model-id","tier":"standard","effort":"none","prompt_version":"enrich-v1","schema_version":"record-v1","batch_size":10,"worker_count":1,"review_ids":["source-review-id"],"work_units":1,"request_id":"provider-request-id","attempt":1,"outcome":"succeeded","input_tokens":100,"cached_input_tokens":0,"output_tokens":30,"requests":1,"usage_complete":true,"duration_seconds":1.2}
```

Example run record shape:

```json
{"run_id":"cold-100-v1","phase":"cold","input_rows":100,"input_sha256":"actual-cost_100.csv-sha256","input_review_ids":["source-review-id-1","source-review-id-2"],"completed_records":100,"failed_records":0,"unique_texts":98,"cache_hits":0,"worker_count":1,"wall_seconds":45.0,"stage_metrics":{"enrich_primary":{"work_units":98,"wall_seconds":35.0},"verify":{"work_units":10,"wall_seconds":5.0},"group":{"work_units":1,"wall_seconds":2.0},"memo":{"work_units":1,"wall_seconds":3.0}}}
```

The values above illustrate the schema only; they are not project measurements. Use the real run's actual counts and timings.

## Paid execution

Paid execution is implemented separately in `pilot.py` and requires the explicit `--execute` flag. It supports the fixed manifest-verified 100-, 500-, and 10,000-review checkpoints and the generated, manifest-verified 100,000-review input. Never put credentials in a call log.
