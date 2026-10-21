# Submission readiness review

Reviewed against `Project Instructions/Multi Agent Large Data Processing Pipeline.docx`, `Data/GRADING_CONTRACT.md`, saved run artifacts, and the local checker on 2026-10-20. The approved final scope is 100,000 selected nonempty reviews plus all 13 source rows quarantined for empty text.

## Status against the assignment

| Requirement | Evidence | Status and next action |
|---|---|---|
| Public GitHub repository | `https://github.com/esidentu/spotify-review-insight-pipeline` | Complete: public repository exists, current `main` commit `bde97ca` is pushed, and local `main` is synced with `origin/main`. The latest push produced GitHub's advisory that `cost/pilot_calls.jsonl` is 57.90 MB (above the recommended 50 MB); GitHub accepted it. |
| Full source ingestion profile and provenance | `grading/ingestion.json`, `Data/manifest.json` | Complete: 660,622 source rows profiled, with source hash and missingness documented. |
| Final run and empty-text quarantine | `grading/records.jsonl`, `Data/final_scope_100000_plus_empty.csv`, `grading/run.json` | Complete for approved scope: 100,000 completed nonempty reviews plus 13 explicit `empty_review_text` quarantines. The assignment brief permits at least 100,000, but its proportional coverage rubric means this earns only partial coverage credit. |
| Golden 50, field comparison and error analysis | `Data/golden_50_labeled.csv`, `cost/review_100000_quality.md` | Complete; includes identified bare-boycott mismatches and a `needs_review` example analysis. No output labels were silently changed. |
| 100-review cost/runtime calculator | `cost/`, `cost/report.md`, `cost/README.md` | Substantially complete: cold/warm evidence, editable rates, offline replay and control logic are present. Failed-call usage remains unknown and is kept unresolved rather than fabricated. |
| Distinct enrichment, verification, grouping and memo roles | `grading/calls.jsonl`, `grading/ai_grouping.json`, `grading/ai_recommendation.json`, role prompts | Enrichment and verification have actual Jev call evidence. Two bounded Jev Choice calls used saved group metrics and review evidence: `group` selected `topic-other` for subtopic review, and `memo` selected `topic-usability` for next-cycle investigation. Code left baseline membership and ranking unchanged and rendered the recommendation from saved claims and evidence. |
| Reliable bounded requests and saved recovery | `cost/pilot.py`, call/run logs, `grading/checkpoint_before.json`, `checkpoint_after.json` | Controls and resume evidence exist. The “before” checkpoint is reconstructed from logs rather than a separately captured runtime snapshot; the assignment also requires a short recording that has not been made. |
| Planted-error and injection tests | `grading/tests/README.md`, versioned result JSON, `cost/pilot_calls.jsonl` | Complete: Jev rejected the planted label (no probability 0.02). The first injection check exposed cancellation intent being followed (0.59 probability); after strengthening only the custom-input prompt, the new v2 check selected `other` / `praise` / severity 1 and passed. Both outcomes and token usage are retained; the historical 100,000 labels were not changed. |
| Grading export and mechanical check | `grading/`, `grading-self-check.json` | Latest check accounts for all 100,013 in-scope IDs (100,000 completed, 13 quarantined), with 21,901 valid exact-text cache reuses and reproducible ranking. `group` and `memo` calls are present. Status remains `review_required` for 24 unavailable token fields across 12 older failed attempts. |
| Decision memo and traceable calculations | `grading/memo.md`, `claims.csv`, `ranking.csv`, README trace | Ranking is reproducible, memo citations use the correct claim IDs, and the checker was rerun after the export update. |
| Runnable arbitrary-input staged pipeline | `cost/pilot.py`, `prompts/enrich-v2.md`, `src/spotify_pipeline/`, `outputs/` | Complete: the runner accepts any CSV with the six source columns, hashes the input, quarantines empty text, and saves outputs/resume state in a dedicated folder. A three-row synthetic CSV preflight confirmed one unique nonempty label request, one verification request, one blank quarantine, and zero dispatched calls. The paid path uses bounded enrichment/verification, followed by deterministic membership, ranking, and memo stages. |
| Database, backend, and deployed dashboard | `dashboard/`, `render.yaml`, `grading/ai_recommendation.json` | The read-only API and dashboard are live on Render Free at `https://spotify-review-insights-e5lu.onrender.com`. The deployed image built SQLite for 100,013 records; `/healthz`, `/api/metrics`, `/api/ranking`, and `/api/recommendation` returned expected data. Evidence endpoint, corrected memo, and post-correction redeploy remain in progress. |
| README evidence map and setup | `README.md` | Rubric map, source URL/hash, architecture, one source-to-memo trace, results/limitations, and Windows setup/replay steps are present. Add live dashboard URL/access instructions after deployment. |
| Final portal submission | Course submission portal | Still required: submit the public GitHub repository URL through bCourses and select the final assignment. |

## Scope and expected coverage tradeoff

The assignment brief explicitly permits “all 660,622 (or at least 100,000)” source IDs, so the user-approved 100,000 nonempty scope is within its stated minimum. The stricter `Data/GRADING_CONTRACT.md` describes the whole corpus, while the assignment’s coverage point is proportional. Its formula is `0.2 × exact full-file profile match + 0.2 × valid accounted rows / 660,622 + 0.6 × valid classified nonempty rows / 660,609`. With this run’s full-profile match and 100,000 classifications plus 13 empty quarantines, the coverage component is about **0.321 out of 1.0**, subject to the instructor’s final validation. The local checker uses the supplied analysis subset as its denominator, so its 100% subset coverage is not the course coverage score.

## Remaining work in priority order

1. Keep `review_required` and unknown failed usage explicit unless real provider evidence resolves them; do not insert guessed token counts. Group/memo calls are now in the checker evidence and offline cost report.
2. The synthetic adversarial checks and arbitrary-input offline preflight are complete; retain both the v1 injection failure and v2 result in the submitted artifacts.
3. The 100,000 run demonstrates saved recovery; capture the required short interruption/resume recording.
4. Correct the stale memo wording discovered during live verification, rebuild and redeploy the SQLite-backed service, verify all live API/dashboard routes against saved calculations, and keep the public URL/access instructions in the README.
5. Inspect the public repository signed out, test setup in a clean environment, then submit the repository URL in the course portal. The current commit has already been pushed.

## Limits that must remain visible

The 100,000 sample does not classify the other 560,609 nonempty source rows. Historical labels include the documented bare-`Boycott` issue. Twelve failed calls have unknown token usage (24 missing token fields). The usage dashboard and local ledger previously differed; use the reproducible call ledger as known usage and do not call the checker a cost audit. The checkpoint-before file is reconstructed, not captured live. Final post-correction deployment verification, the interruption/resume recording, and course-portal submission remain outstanding.
