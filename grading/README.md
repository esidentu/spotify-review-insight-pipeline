# 100,000-row grading export

This folder is the grading adapter for the declared 100,000-nonempty-review scope. `run.json` identifies 100,000 selected nonempty reviews plus all 13 empty-text quarantines; `ingestion.json` profiles the full source file. The package was built offline from saved outputs and call logs. No provider requests were made.

Read `memo.md` for the recommendation and ranking, `../cost/review_100000_quality.md` for the human-label and needs-review analysis, and `local_stages.jsonl` for the deterministic grouping/memo stages. `checkpoint_before.json` is reconstructed from the saved input/cache/call ordering and matches the logged 31,283-record checkpoint; it was not a separately captured snapshot file at runtime.

Known evidence gaps: no model calls were made for group or memo, although the checker asks for those roles; 12 failed attempts in the selected scope have unavailable token usage (nine during the 100,000 run and three during earlier checkpoints), preserved as null. The completed bare-`Boycott` labels also remain as produced and are documented in the quality review.
