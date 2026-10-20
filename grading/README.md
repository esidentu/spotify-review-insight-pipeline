# 100,000-row grading export

This folder is the grading adapter for the user's declared 100,000-row scope. `run.json` identifies the exact analysis subset; `ingestion.json` profiles the full source file. The package was built offline from saved outputs and call logs. No provider requests were made.

Read `memo.md` for the recommendation and ranking, `../cost/review_100000_quality.md` for the human-label and needs-review analysis, and `local_stages.jsonl` for the deterministic grouping/memo stages. `checkpoint_before.json` is reconstructed from the saved input/cache/call ordering and matches the logged 31,283-record checkpoint; it was not a separately captured snapshot file at runtime.

Known evidence gaps: no model calls were made for group or memo, although the checker asks for those roles. Twelve failed attempts on IDs in this selected subset have unavailable token usage, preserved as null; nine occurred during the 100,000-row run and three during earlier checkpoints. The checker reports those missing token fields and the two absent model roles. The completed bare-`Boycott` labels also remain as produced and are documented in the quality review.

The zero-API self-check is saved outside this folder as `grading-self-check.json`; it reports `review_required` while confirming 100% record coverage and valid cache reuse for 21,901 rows.
