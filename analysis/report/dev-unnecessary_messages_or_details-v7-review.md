# Exploratory HW5 development review: unnecessary_messages_or_details v7

V7 was drafted from v5 with one additional Pass sentence allowing a brief supported-help offer after an out-of-scope refusal. Its five training examples were unchanged. `gpt-4o-mini` judged the same fixed 24 development traces (13 human Pass, 11 human Fail). No test predictions were made.

| Version | TP | FN | TN | FP | TPR (95% Wilson CI) | TNR (95% Wilson CI) | Agreement |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: |
| v5 | 10 | 3 | 6 | 5 | 76.9% (49.7–91.8%) | 54.5% (28.0–78.7%) | 66.7% |
| v7 | 6 | 7 | 8 | 3 | 46.2% (23.2–70.9%) | 72.7% (43.4–90.3%) | 58.3% |

Pass is the positive class. The hypothesis failed. Six verdicts changed from v5: four human Pass cases (support-0166, support-0150, support-0149, support-0130) became incorrect Fail verdicts, while two human Fail cases (support-0217, support-0176) became correct Fail verdicts. The intended out-of-scope case support-0174 remained an incorrect Fail. Support-0102 and support-0208 also remained incorrect Fail.

The saved critiques for support-0102, support-0208, and support-0174 still treat a blocked-answer clarification, a restriction restated after challenge, or a brief supported-help offer as unnecessary despite the prompt's allowances. The large verdict shift from one sentence shows that a small prompt edit can have broad effects on this 24-case development set; it does not establish that the new sentence alone caused each change.

Raw metrics: `analysis/report/dev-unnecessary_messages_or_details-v7.json`. Prompt: `analysis/prompts/unnecessary_messages_or_details-v7.txt`. Predictions and critiques: `analysis/state/judges/unnecessary_messages_or_details-v7.json`.
