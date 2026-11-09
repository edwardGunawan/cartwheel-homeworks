# Exploratory HW5 development review: unnecessary_messages_or_details v12

V12 was drafted from v9 with one added single-property relevance sentence. Its five training examples were unchanged. `gpt-4o-mini` judged the same fixed 24 development traces (13 human Pass, 11 human Fail). No test predictions were made.

| Version | TP | FN | TN | FP | TPR (95% Wilson CI) | TNR (95% Wilson CI) | Agreement |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: |
| v9 | 11 | 2 | 5 | 6 | 84.6% (57.8–95.7%) | 45.5% (21.3–72.0%) | 66.7% |
| v12 | 11 | 2 | 5 | 6 | 84.6% (57.8–95.7%) | 45.5% (21.3–72.0%) | 66.7% |

Pass is the positive class. The hypothesis did not improve the aggregate rates. V12 correctly changed human Fail support-0012 to Fail and human Pass support-0130 to Pass, but incorrectly changed human Pass support-0174 to Fail and human Fail support-0025 to Pass. The four exchanges canceled exactly in the confusion counts.

V12 disagrees with current human labels on support-0068, support-0208, support-0174, support-0028, support-0065, support-0025, support-0217, and support-0176. V9 and v12 have the same TPR/TNR but different case errors, so the aggregate rates alone do not show which prompt better follows the intended boundary. No human label was changed.

Raw metrics: `analysis/report/dev-unnecessary_messages_or_details-v12.json`. Prompt: `analysis/prompts/unnecessary_messages_or_details-v12.txt`. Predictions and critiques: `analysis/state/judges/unnecessary_messages_or_details-v12.json`.
