# Submission readiness review

Reviewed against `Project Instructions/Multi Agent Large Data Processing Pipeline.docx`, `Data/GRADING_CONTRACT.md`, saved run artifacts, and the local checker on 2026-10-20. The approved final scope is 100,000 selected nonempty reviews plus all 13 source rows quarantined for empty text.

## Status against the assignment

| Requirement | Evidence | Status and next action |
|---|---|---|
| Public GitHub repository | `https://github.com/esidentu/spotify-review-insight-pipeline` | Repository and `origin` remote exist. Push the current working changes, then inspect the final public state signed out. |
| Full source ingestion profile and provenance | `grading/ingestion.json`, `Data/manifest.json` | Complete: 660,622 source rows profiled, with source hash and missingness documented. |
| Final run and empty-text quarantine | `grading/records.jsonl`, `Data/final_scope_100000_plus_empty.csv`, `grading/run.json` | Complete for approved scope: 100,000 completed nonempty reviews plus 13 explicit `empty_review_text` quarantines. The assignment brief permits at least 100,000, but its proportional coverage rubric means this earns only partial coverage credit. |
| Golden 50, field comparison and error analysis | `Data/golden_50_labeled.csv`, `cost/review_100000_quality.md` | Complete; includes identified bare-boycott mismatches and a `needs_review` example analysis. No output labels were silently changed. |
| 100-review cost/runtime calculator | `cost/`, `cost/report.md`, `cost/README.md` | Substantially complete: cold/warm evidence, editable rates, offline replay and control logic are present. Failed-call usage remains unknown and is kept unresolved rather than fabricated. |
| Distinct enrichment, verification, grouping and memo roles | `grading/calls.jsonl`, `grading/local_stages.jsonl`, role prompts | Enrichment and verification have actual Jev call evidence. Grouping and memo were deterministic local code; the checker flags missing successful `group` and `memo` model-call roles. Decide whether to add bounded paid Jev role calls or submit transparently with this gap. |
| Reliable bounded requests and saved recovery | `cost/pilot.py`, call/run logs, `grading/checkpoint_before.json`, `checkpoint_after.json` | Controls and resume evidence exist. The “before” checkpoint is reconstructed from logs rather than a separately captured runtime snapshot; the assignment also requires a short recording that has not been made. |
| Planted-error and injection tests | Existing golden comparison and verification sample | Incomplete: add tests for a deliberately wrong proposed label and a synthetic review containing an instruction injection. Save actual inputs, outputs, and decisions; do not describe unrun tests as passed. |
| Grading export and mechanical check | `grading/`, `grading-self-check.json` | Latest check accounts for all 100,013 in-scope IDs (100,000 completed, 13 quarantined), with 21,901 valid exact-text cache reuses and reproducible ranking. Status remains `review_required` for 24 unavailable token fields across 12 failed attempts and missing `group`/`memo` calls. |
| Decision memo and traceable calculations | `grading/memo.md`, `claims.csv`, `ranking.csv`, README trace | Ranking is reproducible, memo citations use the correct claim IDs, and the checker was rerun after the export update. |
| Runnable arbitrary-input staged pipeline | `cost/pilot.py`, `src/spotify_pipeline/` | The paid runner supports fixed assignment checkpoints; confirm or implement an arbitrary input-CSV path, with separate role handoffs and safe offline defaults. |
| Database, backend, and deployed dashboard | `dashboard/` | Local SQLite, read-only API and dashboard exist. Not deployed; the dashboard recommendation is the saved local memo, not an AI-generated grounded recommendation. Deployment, live database-backed checks, and a recommendation generated from analyzed metrics remain required. |
| README evidence map and setup | `README.md` | Rubric map, source URL/hash, architecture, one source-to-memo trace, results/limitations, and Windows setup/replay steps are present. Add live dashboard URL/access instructions after deployment. |
| Final portal submission | Course submission portal | Still required: submit the public GitHub repository URL through bCourses and select the final assignment. |

## Scope and expected coverage tradeoff

The assignment brief explicitly permits “all 660,622 (or at least 100,000)” source IDs, so the user-approved 100,000 nonempty scope is within its stated minimum. The stricter `Data/GRADING_CONTRACT.md` describes the whole corpus, while the assignment’s coverage point is proportional. Its formula is `0.2 × exact full-file profile match + 0.2 × valid accounted rows / 660,622 + 0.6 × valid classified nonempty rows / 660,609`. With this run’s full-profile match and 100,000 classifications plus 13 empty quarantines, the coverage component is about **0.321 out of 1.0**, subject to the instructor’s final validation. The local checker uses the supplied analysis subset as its denominator, so its 100% subset coverage is not the course coverage score.

## Remaining work in priority order

1. Keep `review_required` and unknown failed usage explicit unless real provider evidence resolves them; do not insert guessed token counts. The updated checker and offline replay have been run.
2. Add and run the planted-error and prompt-injection tests. Save their actual artifacts and document verifier behavior.
3. Decide whether to spend a small amount from the approved cumulative USD 8 cap on bounded Jev `group` and `memo` calls. A call must be real, usage-recorded, and reflected in the artifacts; never synthesize call evidence to silence the checker.
4. Confirm that one command can accept an arbitrary input CSV and coordinate ingest, enrich, verify, group, rank, and recommendation without manual pasting. Demonstrate the saved-state resume path and capture the required short recording.
5. Deploy the SQLite-backed service and dashboard, add a grounded AI-generated recommendation with issue/review evidence, and verify displayed values against saved calculations. Choose a host and provide deployment credentials/configuration before this can be completed.
6. Test setup in a clean environment, inspect tracked files and the public repository signed out, push the final artifacts, then submit the repository URL in the course portal.

## Limits that must remain visible

The 100,000 sample does not classify the other 560,609 nonempty source rows. Historical labels include the documented bare-`Boycott` issue. Twelve failed calls have unknown token usage (24 missing token fields). The usage dashboard and local ledger previously differed; use the reproducible call ledger as known usage and do not call the checker a cost audit. The checkpoint-before file is reconstructed, not captured live. Deployment, the live AI recommendation, tests, recording, and course-portal submission are not yet evidenced.
