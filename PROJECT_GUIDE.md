# Project guide: Spotify review pipeline

This guide explains the work in plain language: what you labeled, what Jev labeled, what the program did, what each checkpoint cost, and what remains. It is written from the project instructions and the saved run records. The detailed grading requirements remain in `Data/GRADING_CONTRACT.md`; the cost-calculator requirements remain in `Data/COST_CALCULATOR.md`.

## In one sentence

We are building a repeatable program that reads Spotify reviews, asks an AI model to judge what each review means, saves a traceable label for every original review, and calculates issue counts and priorities with ordinary code.

## Who did what

### You: the golden 50

You manually labeled and approved the 50 examples in `Data/golden_50_labeled.csv`. Those are the **golden labels**: a human reference set we can compare with model results later. They are not examples sent to Jev, and their answers are not included in Jev prompts.

### Jev: meaning-based labels

Jev read each review text and returned a topic, intent, severity, and sentiment judgment. The program also asked Jev a yes/no-style verification question for a small, fixed sample. Jev did not choose the final rankings or write the pilot summaries.

### The local program: repeatable bookkeeping

Python handles file reading, ID and source-hash checks, exact-text reuse, output validation, call and cost logging, topic grouping, arithmetic, ranking, and summary-file creation. Those jobs do not need a language model.

### Workers and agents are different

A **worker** is a slot that sends model requests. The 100-, 500-, and 10,000-row checkpoints used one worker. The prepared 100,000-row runner is configured for at most two workers. It sends the same one-review state and the same four questions used in the one-worker pipeline; two requests may be in flight, but their review text and answers stay separate. A Codex agent is a separate software assistant used to help build or review code; it is not a Jev worker.

## What each label means

- **Topic:** the main supported subject, such as playback, billing, or usability.
- **Intent:** what the reviewer is doing: cancellation, complaint, request, praise, or unclear.
- **Severity:** how much the reported problem affects the reviewer, from 1 to 5. Cancellation by itself does not increase severity.
- **Sentiment:** the overall tone, stored from -1 (very negative) to +1 (very positive).
- **Entities:** exact matches to a fixed list of Spotify-related feature terms, such as playlist, lyrics, or premium. This is a simple deterministic extraction, not an AI-discovered list of every named thing.
- **Evidence quote:** the original review text, preserved verbatim in the pilot output.
- **Needs review:** set when one or more model confidence values are below 0.5, or when the verification check does not support the saved label. It is a flag for human attention, not a claim that the label is wrong.

The shared topic and severity definitions are in the grading contract. Ratings/stars are saved as metadata but are not used to decide the text labels.

## What the checkpoints did

| Checkpoint | What happened | Result |
|---|---|---|
| Golden 50 | You labeled these manually. | Held for later quality comparison; never sent as labeled examples to Jev. |
| Cold 100 | Jev labeled 100 unique review texts; 10 got verification checks. | 100/100 completed. Known Jev token charge: **$0.004468380**. |
| Warm 100 | The program checked the saved 100 results. | Zero new Jev calls; zero incremental API cost. |
| Cold 500 | This file contains the first 100 plus 400 more rows. The program reused 100 saved labels, found 21 additional exact-text duplicates, labeled 379 new unique texts, and added 38 checks. | 500/500 completed; 479 unique texts; 48 checks total; **417 new calls**; about 50.22 seconds. Cumulative known Jev token charge: **$0.021400512**. |
| Warm 500 | The program checked the saved 500 results. | Zero new Jev calls; zero incremental API cost; about 0.0036 seconds. |
| Cold 10,000 | The program reused labels for 479 distinct texts from the 500 checkpoint, labeled the remaining distinct texts, and checked a deterministic 10% verification sample. | 10,000/10,000 complete; 8,448 distinct texts; 7,969 new enrichments; 797 new verification calls (845 total checks including the 48 earlier checks). Incremental known Jev cost: **$0.356404230**. Cold runtime across the start/resume attempts: about **41 minutes**. |
| Warm 10,000 | The program validated the saved 10,000 records without contacting Jev. | 10,000/10,000 reused; zero new API calls; zero incremental API cost; **0.037 seconds**. |

The 500-run output has **83 rows flagged `needs_review`**; the 10,000-row output has **2,033**. These are attention flags, not confirmed mistakes. Repeated reviews can cause the same cached judgment or flag to appear on multiple source rows.

The ranked pilot categories are deterministic topic buckets, such as `topic-playback`. They are not yet human-named issue clusters discovered from the review corpus. Topic counts in 100, 500, or 10,000 reviews are checkpoint summaries, not estimates of the whole Spotify population.

## Cost and the saved failed attempt

The 100-, 500-, and 10,000-review checkpoints were run under a **$1 local stop limit**. The current cumulative project cap is **$8**, approved for the planned 100,000-review work. This is a guard in our program; it is not a TypeSafe billing setting and cannot guarantee against provider-side delays.

The TypeSafe pricing file records Jev's published **$0.042 per million input tokens** and **$0 per output tokens**. The saved successful-call usage totals produce the known token charge shown above. See the dated source in `cost/rates.csv` and TypeSafe's [model and pricing documentation](https://docs.typesafe.ai/models).

The first 100-row request and two early 10,000-row attempts failed before returning token usage. A no-cost diagnostic confirmed that DNS could not resolve the TypeSafe API host at that time; after network access was restored, the checkpoint resumed successfully. The local $1 cap continues to hold **$0.000272412** for the three unanswered calls.

The cost report uses returned tokens for cost, treats request count as operational metadata, keeps failed calls visible, and calibrates from calls with complete usage. Before the 10,000 run, it projected about **$0.356**; measured incremental token cost was **$0.356404230**. Cumulative known token cost through 10,000 was **$0.377804742**, with about **$0.621923** left under the then-active $1 cap after failed-call reserves. The earlier 100,000-review projections were about **$3.28–$4.47**; measured known Jev cost for the completed 100,000 run was **$3.119385**. Cumulative known project cost is **$3.505917**, with **$4.492264** left under the $8 cap after unresolved-call reserves. The provider dashboard most recently showed **$3.228**, 88,910,604 tokens, and 75,711 requests for “All traffic / Last 24 hours”; the page warns that usage stats may be delayed, and this snapshot is still below the local response-usage ledger.

## Where to find the work

Open the project's `cost` folder:

- `pilot_records.jsonl` — 100 labeled records.
- `pilot_records_500.jsonl` — 500 labeled records, including source IDs and model judgments.
- `pilot_records_10000.jsonl` — completed 10,000-row labeled checkpoint.
- `pilot_membership_10000.csv`, `pilot_ranking_10000.csv`, and `pilot_memo_10000.md` — local 10,000-row grouping, ranking, and simple summary.
- `pilot_labeled_10000.csv` — spreadsheet-friendly 10,000-row review export, including original review text, labels, confidence values, and the `needs_review` flag. Filter `needs_review` to `true` to focus on flagged examples.
- `Data/final_100000.csv` — deterministic 100,000-review input prepared locally from the full source; it includes the Golden 50 review texts but not their expected labels.
- `Data/prepare_final_100000.py` — regenerates the 100,000 input and manifest checksum without API calls.
- `grading/records.jsonl` — canonical completed 100,000-row labeled output in the grading export.
- `cost/pilot_labeled_100000.csv` — spreadsheet-friendly copy of that output with original review fields, labels, confidence values, and `needs_review`; filter `needs_review` to `true` to inspect 20,683 flagged rows.
- `cost/export_labeled_100000.py` — rebuilds the CSV locally from the completed JSONL and source CSV without API calls.
- `cost/pilot_membership_100000.csv`, `cost/pilot_ranking_100000.csv`, and `cost/pilot_memo_100000.md` — local grouping, ranking, and summary.
- `pilot_memo.md` and `pilot_memo_500.md` — plain-language pilot summaries and rankings.
- `pilot_ranking.csv` and `pilot_ranking_500.csv` — deterministic topic-bucket rankings.
- `pilot_calls.jsonl` — every provider request attempt and its recorded usage/status.
- `pilot_runs.jsonl` — sample counts, cache use, duration, and run totals.
- `pilot_reconciliations.jsonl` — failed-call reserve notes and provider dashboard snapshots.
- `report.md` — offline replay of logged costs, rates, and measurements.

## 100,000-review run result and next steps

The 100,000-review run is complete. It produced 100,000 completed rows from 78,099 distinct review texts. Jev made 69,651 new enrichment calls and 6,965 verification calls. Every request carried one review; two independent calls ran at a time. The one-review prompt and schema stayed the same as the one-worker pipeline. SDK retries were disabled, progress was checkpointed, and the request timeout was raised from the 10-second SDK default to 60 seconds after intermittent timeouts. Nine failed attempts were manually resumed; their usage remains unknown and their estimated charges remain reserved under the local cap. All final rows nevertheless have completed labels. The 10% verification sample completed.

The 100,000-row run cost USD 3.119385 in known Jev usage. Cumulative known project usage is USD 3.505917; the local USD 8 cap has USD 4.492264 remaining after unresolved-call reserves. The TypeSafe Usage page showed USD 3.228, 88,910,604 tokens, and 75,711 requests for “All traffic / Last 24 hours” and still warns that statistics may be delayed. Keep the local ledger and this dashboard difference visible until they reconcile.

Quality review of the 100,000 output is recorded in `cost/review_100000_quality.md`. The user confirmed that 100,000 reviews is the intended final scope, consistent with the assignment brief's “all 660,622 (or at least 100,000)” wording. The 100,000-row grading export is in `grading/`; its zero-API self-check is `grading-self-check.json`. Coverage is complete (100,000/100,000), but the checker status is `review_required`: it found 24 unavailable-token fields across 12 failed attempts and no model-call evidence for group/memo roles, which ran locally. The checkpoint-before ID list is reconstructed from saved run/cache evidence and matches the logged 31,283-row checkpoint. The output review found a specific prompt gap for bare boycott slogans; completed model records remain unchanged and the gap is documented in the review report.

## Important meanings

- **Cold run:** a run that makes new provider requests for work not already in the result cache.
- **Warm run:** a check that reuses saved results and measures the cache path without making new model requests.
- **Exact-text reuse:** reuse only when the review text and label configuration match exactly. Every original review ID still gets its own output record.
- **Cumulative known cost:** token cost calculated from calls with usage returned. It can differ from the provider's live dashboard while billing updates; unknown usage stays marked unknown.
- **10,000 checkpoint:** completed scale test before quality evaluation and the planned 100,000-review run; it is not the final full-data run.
