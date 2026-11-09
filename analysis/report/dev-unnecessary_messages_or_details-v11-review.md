# Exploratory HW5 development review: unnecessary_messages_or_details v11

V11 was drafted from v9 with a narrower output instruction for unnecessary facts copied from tool results, while explicitly protecting blocker explanations and relevant next steps. Its five training examples were unchanged. `gpt-4o-mini` judged the same fixed 24 development traces (13 human Pass, 11 human Fail). No test predictions were made.

| Version | TP | FN | TN | FP | TPR (95% Wilson CI) | TNR (95% Wilson CI) | Agreement |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: |
| v9 | 11 | 2 | 5 | 6 | 84.6% (57.8–95.7%) | 45.5% (21.3–72.0%) | 66.7% |
| v11 | 11 | 2 | 4 | 7 | 84.6% (57.8–95.7%) | 36.4% (15.2–64.6%) | 62.5% |

Pass is the positive class. V11 did not improve the intended tradeoff. Human Pass support-0130 changed correctly to Pass, but support-0157 changed incorrectly to Fail. Human Fail support-0025 changed incorrectly to Pass. TPR stayed 11/13 while TNR fell to 4/11.

The changed verdicts were not confined to the targeted extra-field case, continuing the prompt sensitivity seen in prior versions. Raw metrics: `analysis/report/dev-unnecessary_messages_or_details-v11.json`. Prompt: `analysis/prompts/unnecessary_messages_or_details-v11.txt`. Predictions and critiques: `analysis/state/judges/unnecessary_messages_or_details-v11.json`.
