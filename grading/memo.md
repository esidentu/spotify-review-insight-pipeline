# Product recommendation from the 100,000-review sample

## Scope and method

This memo covers the deterministic 100,000-row subset, not the entire 660,622-row source. Topic buckets are deterministic groupings of completed complaint and cancellation labels. They are broad topics, not model-discovered product issues. The sampled reviews are self-selected public feedback and do not establish market-wide rates.

## Recommendation

Prioritize investigation of usability in the next planning cycle. It has the highest baseline priority score in this subset: 13,886 complaint/cancellation reviews, a severity sum of 37,501, and mean severity 2.700634 (claims `r01-complaint_count`, `r01-severity_sum`, `r01-mean_severity`, `r01-priority_score`). Billing ranks third with score 20,978 and playback fourth with score 19,747 (claims `r03-priority_score`, `r04-priority_score`). The second-ranked `other` bucket has a score of 29,493 but is too broad to directly identify a product investment (claim `r02-priority_score`). This is a prioritization signal from the selected sample; validate it with product telemetry and targeted user research before treating it as a population-wide conclusion.

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

The Golden 50 comparison, `needs_review` analysis, and the 142 bare-`Boycott` intent mismatches are documented in `../cost/review_100000_quality.md`. The completed labels are preserved as produced. The enrichment and verification stages used Jev; grouping and memo generation used local deterministic code, as recorded in `local_stages.jsonl`.

The checker expects successful model-call evidence for `group` and `memo`; those provider calls were not made in this run. It also requires numeric token usage on failed-call entries even when the provider returned no usage. The call log preserves those unknown values as null, so a review-required self-check is expected for those evidence gaps. The 13 empty source texts are included as explicit `empty_review_text` quarantines; they received no model calls.
