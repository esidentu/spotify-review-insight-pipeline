# Submission readiness review

Reviewed against `Project Instructions/Multi Agent Large Data Processing Pipeline.docx`, `Data/GRADING_CONTRACT.md`, the saved run artifacts, and the local zero-API self-check on 2026-10-20.

## Complete or substantially evidenced

| Requirement | Current evidence | Status |
|---|---|---|
| Read/profile source and preserve source identity | `grading/ingestion.json` profiles all 660,622 source rows, including 13 empty texts; `grading/run.json` records source and selected-input hashes | Complete for ingestion/profile |
| Process at least 100,000 reviews | `grading/records.jsonl`, `grading/run.json`, `grading-self-check.json` | 100,000/100,000 selected IDs completed; the assignment document permits at least 100,000 |
| Golden 50 and error analysis | `Data/golden_50_labeled.csv`, `cost/review_100000_quality.md` | Complete; evaluation is diagnostic and limitations are documented |
| Cost/runtime pilot and offline replay | `cost/`, `cost/README.md`, `cost/report.md` | Substantially complete; known returned-usage cost is separated from unknown failed-call usage |
| Saved outputs, deterministic ranking, memo claims | `grading/records.jsonl`, `membership.csv`, `ranking.csv`, `claims.csv`, `memo.md` | Complete for the selected 100,000 scope |
| Checkpoint/resume evidence | `grading/checkpoint_before.json`, `checkpoint_after.json` | Present; before snapshot is reconstructed from run logs and cache evidence, not a separate runtime capture |
| Labeling rule correction for future work | `prompts/enrich-v2.md`, `prompts/verify-v2.md` | Added the contract's bare-boycott exception; historical 100,000 labels remain unchanged |

## Open requirements

| Requirement | Current state | Work remaining |
|---|---|---|
| Mechanical submission check | `grading-self-check.json` says `review_required`; coverage is complete | The checker reports missing usage for 12 failed attempts (24 null token fields) and missing successful `group`/`memo` model-call roles |
| Distinct executed model roles | Enrichment and verification have provider evidence; grouping and memo were local deterministic stages | Run and log separate bounded group and memo model tasks, or confirm with the instructor that the local deterministic implementations satisfy the role requirement. This would be additional paid provider work if model roles are used. |
| Independent verification tests | 10% verification sample is logged | Add the separate deliberately-wrong-label test and a prompt-injection test, with saved outcomes |
| Dashboard/backend/database | A local SQLite database, read-only HTTP API, and browser dashboard are now implemented under `dashboard/`; the database is generated from saved records and aggregates | Deploy to a host with a persistent database, test live metrics against saved calculations, add the live URL and access instructions. The displayed recommendation is explicitly labeled as the saved local memo, not AI-generated |
| Public repository and final packaging | Local Git repository initialized and assignment files committed; no GitHub remote or public URL exists yet | Complete GitHub sign-in, create/push the public repository, recheck tracked files and history, then submit its URL through the course portal |
| Interruption/resume recording | Checkpoint files exist; no recording artifact was found | Record a short walkthrough of saved progress and resume evidence, if the instructor still requires the recording |

## Scope note

The assignment document's submission section and definition of done both allow “all 660,622 (or at least 100,000)” IDs. `Data/GRADING_CONTRACT.md` describes all 660,622 IDs as the final run. The current export declares and checks a deterministic 100,000-ID subset, which meets the assignment document's minimum wording but not the stricter contract wording. Keep that difference explicit in the README and ask the instructor only if the course expects the stricter contract to override the assignment brief.

## Cost and label integrity

No new model calls were made during this review. Failed-call token usage remains unavailable and is not estimated as a factual billed amount. The completed 100,000 labels were not edited; the new prompt files are for future runs and require a new prompt/schema label configuration if used.
