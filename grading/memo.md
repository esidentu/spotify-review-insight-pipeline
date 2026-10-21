# Product recommendation from the 100,000-review sample

## Scope and method

This memo covers the deterministic 100,000-row subset, not the entire 660,622-row source. Topic buckets are deterministic groupings of completed complaint and cancellation labels. They are broad topics, not model-discovered product issues. The sampled reviews are self-selected public feedback and do not establish market-wide rates.

## Recommendation

Prioritize investigation of usability in the next planning cycle. It has the highest baseline priority score in this subset: 13,886 complaint/cancellation reviews, a severity sum of 37,501, and mean severity 2.700634 (claims `r01-complaint_count`, `r01-severity_sum`, `r01-mean_severity`, `r01-priority_score`). Billing ranks third with score 20,978 and playback fourth with score 19,747 (claims `r03-priority_score`, `r04-priority_score`). The second-ranked `other` bucket has a score of 29,493 but is too broad to directly identify a product investment (claim `r02-priority_score`). This is a prioritization signal from the selected sample; validate it with product telemetry and targeted user research before treating it as a population-wide conclusion.

## Model-informed recommendation

A bounded Jev Choice selected **topic-usability** for the next planning-cycle priority (confidence 0.580). The model saw the saved topic aggregates and two review-evidence excerpts per topic. Code rendered this section from the selected option and saved calculations; it did not ask Jev to invent metrics or prose.

In the approved sample, topic-usability has 13,886 complaint/cancellation reviews, a severity sum of 37,501, mean severity 2.700634, and priority score 37,501. These numbers map to `r01-complaint_count`, `r01-severity_sum`, `r01-mean_severity`, `r01-priority_score`.

A Jev grouping assessment selected **topic-other** as the bucket most in need of further subtopic review (confidence 0.950). This is a follow-up signal only: the deterministic baseline memberships and ranking were not changed.

### Supporting review evidence

- `117770a7-cec9-4bc3-8a9f-a5d6f3544b5d` (severity 5): “This app is not good it trase our history and their are many ads in it and it is very difficult to use.”

- `12856471-acdc-44c5-8f4f-612e4ac878da` (severity 5): “I thought the some songs just got deleted from my playlist, turns out this idiot app removed a lot of good songs 🤬🤬🤬😡😡😡”

### Alternative

The next ranked baseline bucket is topic-other with score 29,493 (`r02-priority_score`). The broad `topic-other` bucket ranks 2 and should be decomposed before it is treated as a specific feature investment.

This is an action-priority judgment about a self-selected sample of 100,000 reviews, not a population estimate. Validate it against product telemetry and targeted research before committing engineering work.

## Baseline ranking

| Rank | Topic bucket | Complaint/cancellation count | Severity sum | Mean severity | Priority score | Claims |
|---:|---|---:|---:|---:|---:|---|
| 1 | topic-usability | 13886 | 37501 | 2.700634 | 37501 | `r01-complaint_count`, `r01-severity_sum`, `r01-mean_severity`, `r01-priority_score` |
| 2 | topic-other | 15213 | 29493 | 1.938671 | 29493 | `r02-complaint_count`, `r02-severity_sum`, `r02-mean_severity`, `r02-priority_score` |
| 3 | topic-billing | 7414 | 20978 | 2.829512 | 20978 | `r03-complaint_count`, `r03-severity_sum`, `r03-mean_severity`, `r03-priority_score` |
| 4 | topic-playback | 5633 | 19747 | 3.505592 | 19747 | `r04-complaint_count`, `r04-severity_sum`, `r04-mean_severity`, `r04-priority_score` |
| 5 | topic-catalog | 2327 | 6556 | 2.817361 | 6556 | `r05-complaint_count`, `r05-severity_sum`, `r05-mean_severity`, `r05-priority_score` |
| 6 | topic-access | 1453 | 5724 | 3.939436 | 5724 | `r06-complaint_count`, `r06-severity_sum`, `r06-mean_severity`, `r06-priority_score` |
| 7 | topic-downloads | 1182 | 3943 | 3.335871 | 3943 | `r07-complaint_count`, `r07-severity_sum`, `r07-mean_severity`, `r07-priority_score` |
| 8 | topic-support | 137 | 398 | 2.905109 | 398 | `r08-complaint_count`, `r08-severity_sum`, `r08-mean_severity`, `r08-priority_score` |

The table follows the required baseline: complaint count multiplied by mean severity, equal to severity sum. Counts include each source review once in its topic bucket.

## Quality and evidence notes

The Golden 50 comparison, `needs_review` analysis, and the 142 bare-`Boycott` intent mismatches are documented in `../cost/review_100000_quality.md`. The completed labels are preserved as produced. Enrichment and verification used Jev. Two later bounded Jev Choice calls selected `topic-other` for subtopic follow-up and `topic-usability` for the next-cycle priority; Python rendered the recommendation from those saved choices, the saved metrics, and review evidence. The decisions did not change baseline memberships or ranking. Their inputs and usage are saved in `calls.jsonl`, `ai_grouping.json`, and `ai_recommendation.json`.

The self-check remains `review_required` because 12 older failed calls have unknown token usage (24 unavailable token fields); those values remain null rather than being guessed. A later grouping connection failure is also retained in the call log, followed by a successful grouping call. The 13 empty source texts are included as explicit `empty_review_text` quarantines; they received no model calls.
