# Exploratory HW5 development review: unnecessary_messages_or_details v8

V8 was drafted from v5 with one additional Pass sentence protecting a failed lookup explanation and a request to confirm or correct its input. Its five training examples were unchanged. `gpt-4o-mini` judged the same fixed 24 development traces (13 human Pass, 11 human Fail). No test predictions were made.

| Version | TP | FN | TN | FP | TPR (95% Wilson CI) | TNR (95% Wilson CI) | Agreement |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: |
| v5 | 10 | 3 | 6 | 5 | 76.9% (49.7–91.8%) | 54.5% (28.0–78.7%) | 66.7% |
| v8 | 9 | 4 | 4 | 7 | 69.2% (42.4–87.3%) | 36.4% (15.2–64.6%) | 54.2% |

Pass is the positive class. The hypothesis failed overall. V8 correctly changed support-0102 to Pass, but incorrectly changed human Pass support-0157 and support-0128 to Fail and human Fail support-0201 and support-0011 to Pass. Support-0208 and support-0174 remained incorrect Fail. The added blocked-lookup sentence did not preserve v5's TNR.

The five verdict changes from a one-sentence edit, and v7's similarly broad changes, show substantial prompt sensitivity on this small development set. The saved critiques also continue to interpret missing answers or prior-turn repetition as this failure, despite explicit instructions. This is a reason to avoid treating a point-estimate threshold on these 24 cases as proof of general judge reliability.

Raw metrics: `analysis/report/dev-unnecessary_messages_or_details-v8.json`. Prompt: `analysis/prompts/unnecessary_messages_or_details-v8.txt`. Predictions and critiques: `analysis/state/judges/unnecessary_messages_or_details-v8.json`.
