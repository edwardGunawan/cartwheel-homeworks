# Exploratory HW5 development review: unnecessary_messages_or_details v10

V10 was drafted from v9 with one output instruction requiring Fail whenever the critique identifies an independently unnecessary clause. Its five training examples were unchanged. `gpt-4o-mini` judged the same fixed 24 development traces (13 human Pass, 11 human Fail). No test predictions were made.

| Version | TP | FN | TN | FP | TPR (95% Wilson CI) | TNR (95% Wilson CI) | Agreement |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: |
| v9 | 11 | 2 | 5 | 6 | 84.6% (57.8–95.7%) | 45.5% (21.3–72.0%) | 66.7% |
| v10 | 9 | 4 | 6 | 5 | 69.2% (42.4–87.3%) | 54.5% (28.0–78.7%) | 62.5% |

Pass is the positive class. V10 corrected support-0065 to Fail and support-0130 to Pass, but changed human Pass support-0102, support-0157, and support-0174 to incorrect Fail. The broad “any unnecessary clause means Fail” instruction caught an unrequested tool field while also treating a blocked lookup clarification, a delivery-dispute next step, and a brief supported-help offer as unnecessary. The student's preferred TNR point estimate was reached, but TPR fell below 80%.

V10 disagrees with current human labels on support-0068, support-0102, support-0208, support-0157, support-0174, support-0028, support-0217, support-0012, and support-0176. No human label was changed. Raw metrics: `analysis/report/dev-unnecessary_messages_or_details-v10.json`. Prompt: `analysis/prompts/unnecessary_messages_or_details-v10.txt`. Predictions and critiques: `analysis/state/judges/unnecessary_messages_or_details-v10.json`.
