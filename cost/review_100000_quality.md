# 100,000-review quality review

## Scope and method

This review used the saved 100,000-row spreadsheet export and canonical JSONL output. No Jev/API calls were made. All 50 Golden 50 IDs were found in the output and compared field by field. The `needs_review` column was checked against its two saved triggers: a Jev field confidence below 0.5, or a verification support probability below 0.5. I also inspected examples from both trigger groups.

## Golden 50 comparison

| Field | Exact agreement |
|---|---:|
| Topic | 45 / 50 (90%) |
| Intent | 46 / 50 (92%) |
| Severity | 43 / 50 (86%) |

Sentiment mean absolute error is **0.158** on the -1 to +1 scale. Severity mean absolute error is **0.16**; 49 of 50 severity predictions are within one point of the human label.

These are a small-set comparison, not population-wide accuracy estimates. Some Golden 50 labels do not match the written contract. For example, the Golden label for “Deleting this App ... can't choose songs ... turn off shuffle” is `billing`, while the contract defines controls and playlist management as `usability`; the Jev output is `usability`. Likewise, the Golden label for a review saying the app is too expensive and the free version is unusable with ads is `usability`, while the contract sends price/paywall issues to `billing`; Jev chose `billing`. Those disagreements alone do not justify changing the shared definitions.

Other disagreements show genuine judgment misses or ambiguity. For the review describing an app crash followed by successful help from Support, the human label is `playback` and Jev chose `support`; the written rule says to choose the highest-severity supported problem. This output was not flagged `needs_review`. Several severity differences involve short or multilingual text and were flagged, which is appropriate for human inspection.

The entities field has exact list agreement on **27 / 50**. This is not a like-for-like score: the run uses a fixed deterministic list of Spotify feature terms (for example, `ads`, `song`, `playlist`, `premium`), while Golden labels include broader names such as `Spotify`, people, places, and religious terms. The feature terms are matched from the review text; this check did not reveal an invented entity. The final write-up should state this entity convention so the reader does not mistake it for general named-entity extraction.

## `needs_review` review

There are **20,683 flagged rows (20.683%)** in the 100,000-row CSV:

- **12,373** have at least one topic, intent, severity, or sentiment confidence below 0.5.
- **8,310** have all four field confidences at or above 0.5 but were flagged because Jev's independent verification probability was below 0.5.

The flag is useful for triage, but it is not a correctness score. In the 50 Golden examples, compared with the human `needs_review` labels, the output has 7 true positives, 4 false positives, 9 false negatives, and 30 true negatives. In particular, some high-confidence label disagreements were not flagged.

The inspected flagged examples include very short or unclear text (“Pro”, “Boycott”), unsupported-language text, and conflicting verification of simple praise (“I ❤️ you”, “Good”). The low-confidence flags generally point to genuinely hard-to-interpret inputs. Some verification-only flags appear to be false alarms, so keep the verifier signal as a prompt for inspection rather than automatically changing labels.

## Clear correction to carry forward

The grading contract says bare boycott slogans are `unclear` unless they include a product complaint or an explicit personal departure. The enrichment prompt does not spell out this exception, and **142 rows whose text is only “Boycott” (case/punctuation ignored) were labeled `cancellation`**; 135 of those were flagged. This is a concrete prompt/rule-application gap. Add the explicit exception to the prompt and verifier instructions before any future run. The existing 100,000 output still contains these labels; this review documents the issue but does not silently edit completed model records.

## Decision

Keep the shared topic, intent, and severity definitions. The comparison does not support a broad rule rewrite. Carry forward the explicit bare-boycott exception, preserve the current `needs_review` flag as an attention cue, and disclose the entity extraction convention. The user approved 100,000 reviews as the final scope. The grading export and zero-API mechanical check have since been completed; course-portal submission remains the final external step.
