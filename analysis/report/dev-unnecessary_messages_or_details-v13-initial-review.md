# Exploratory HW5 development review: unnecessary_messages_or_details v13

V13 adds one priority boundary for constrained replies to v12. It says that, after the user challenges an access restriction, one acknowledgment and one statement of the continuing restriction are relevant; a brief refusal and supported-help offer are also relevant for an out-of-scope request. The five training examples are unchanged. `gpt-4o-mini` judged the same fixed 24 development traces (13 human Pass, 11 human Fail). No test predictions were made.

| Version | TP | FN | TN | FP | TPR (95% Wilson CI) | TNR (95% Wilson CI) | Agreement |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: |
| v12 | 11 | 2 | 5 | 6 | 84.6% (57.8–95.7%) | 45.5% (21.3–72.0%) | 66.7% |
| v13 | 12 | 1 | 6 | 5 | 92.3% (66.7–98.6%) | 54.5% (28.0–78.7%) | 75.0% |

Pass is the positive class. Relative to v12, four verdicts changed. Human Pass support-0174 changed correctly from Fail to Pass. Human Fail support-0025 and support-0028 changed correctly from Pass to Fail. Human Fail support-0012 changed incorrectly from Fail to Pass. Both point estimates rose, but the Wilson intervals remain wide because each class has only 11–13 development examples.

The targeted access case support-0208 **remains an incorrect Fail**. Its v13 critique acknowledges that the opening clause is relevant, but calls the still-applicable access restriction unnecessary because it was stated in an earlier assistant turn. That directly conflicts with the new priority rule's instruction not to count repetition across assistant turns as repetition within the final reply. The critique also faults the reply for not fulfilling the original order-status request, which is a separate issue from this failure mode. The other target, support-0174, is now correctly Pass; its critique treats the brief refusal and supported-help offer as relevant. Human Fail support-0068 remains an incorrect Pass: the critique treats “marked as refund eligible” as a distinct explanation of return eligibility rather than semantic repetition.

V13 disagrees with current human labels on support-0012, support-0065, support-0068, support-0176, support-0208, and support-0217. These are development findings, not grounds to change human labels automatically. The improvement is promising on this fixed set, but further selection against the same cases risks fitting the development split.

Raw metrics: `analysis/report/dev-unnecessary_messages_or_details-v13.json`. Prompt: `analysis/prompts/unnecessary_messages_or_details-v13.txt`. Saved development predictions and critiques: `analysis/state/judges/unnecessary_messages_or_details-v13.json`. V13 is still draft; v12 remains frozen.

## Separate one-trace replicate

At the student's request, the unchanged v13 prompt was run again through DocETL on support-0208 alone. This fresh `gpt-4o-mini` call returned **Pass**, matching the human label. Its critique treated the restated restriction as an explanation of the continuing blocker and the friend-checking suggestion as a relevant next step. The original 24-trace v13 run returned Fail for this trace. This disagreement across runs shows sensitivity on this boundary; it does not change the original v13 cache, confusion counts, TPR, TNR, or Wilson intervals. The replicate is saved in `analysis/report/unnecessary_messages_or_details-v13-support-0208-replicate.json`. No test trace was used.
