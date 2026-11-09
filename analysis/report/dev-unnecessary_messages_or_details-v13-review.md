# Exploratory HW5 development review: unnecessary_messages_or_details v13

V13 adds one priority boundary for constrained replies to v12. It says that, after the user challenges an access restriction, one acknowledgment and one statement of the continuing restriction are relevant; a brief refusal and supported-help offer are also relevant for an out-of-scope request. The five training examples are unchanged. At the student's request, the original v13 cache and report were archived, the active cache was cleared, and `gpt-4o-mini` judged the same fixed 24 development traces again (13 human Pass, 11 human Fail). No test predictions were made.

| Version | TP | FN | TN | FP | TPR (95% Wilson CI) | TNR (95% Wilson CI) | Agreement |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: |
| v12 | 11 | 2 | 5 | 6 | 84.6% (57.8–95.7%) | 45.5% (21.3–72.0%) | 66.7% |
| v13 initial | 12 | 1 | 6 | 5 | 92.3% (66.7–98.6%) | 54.5% (28.0–78.7%) | 75.0% |
| v13 rerun (active) | 12 | 1 | 6 | 5 | 92.3% (66.7–98.6%) | 54.5% (28.0–78.7%) | 75.0% |

Pass is the positive class. The rerun has the same aggregate counts as the initial v13 batch, but four individual verdicts changed: human Pass support-0208 changed correctly to Pass; human Fail support-0065 changed correctly to Fail; human Pass support-0102 changed incorrectly to Fail; human Fail support-0028 changed incorrectly to Pass. Both v13 batches exceed v12's point estimates, but the Wilson intervals remain wide because each class has only 11–13 development examples.

The targeted access case support-0208 is **Pass in the active rerun**. Its critique treats the restated restriction as an explanation of the continuing blocker and the friend-checking suggestion as a relevant next step. Human Pass support-0174 also remains correctly Pass. However, the rerun now incorrectly fails support-0102: its critique admits that asking the user to confirm store details is related, but faults the reply for lacking a more concrete path to the price check. That is a task-completion critique rather than identification of removable content. Human Fail support-0068 remains an incorrect Pass: the critique treats “marked as refund eligible” as an explanation of return eligibility rather than semantic repetition.

The active v13 rerun disagrees with current human labels on support-0012, support-0028, support-0068, support-0102, support-0176, and support-0217. These are development findings, not grounds to change human labels automatically. The case swaps with unchanged aggregate scores show that this judge is sensitive to reruns on this boundary.

## Student disagreement decisions

- **support-0068:** Student confirms the human **Fail** label is correct. The active v13 judge says Pass, so this is a judge error. The student considers “eligible for return” followed by “marked as refund eligible” a semantic restatement rather than a distinct reason.
- **support-0102:** Student confirms the human **Pass** label is correct. The active v13 judge says Fail, so this is a judge error. The reply explains the blocked store lookup and asks for store details needed to continue the price check.

These decisions record the student's review; no label, prompt, prediction, or metric was changed.

Active raw metrics: `analysis/report/dev-unnecessary_messages_or_details-v13.json`. Active predictions and critiques: `analysis/state/judges/unnecessary_messages_or_details-v13.json`. Archived initial metrics: `analysis/report/dev-unnecessary_messages_or_details-v13-initial.json`. Archived initial predictions and critiques: `analysis/state/judges/archive/unnecessary_messages_or_details-v13-initial.json`. Prompt: `analysis/prompts/unnecessary_messages_or_details-v13.txt`. After this review, the student selected and froze v13; v12 is draft. The later held-out test is reported separately in `test-unnecessary_messages_or_details-v13-review.md`.

## Separate one-trace replicate

Before the full rerun, the unchanged v13 prompt was run again through DocETL on support-0208 alone. This fresh `gpt-4o-mini` call returned **Pass**, matching the human label. Its critique treated the restated restriction as an explanation of the continuing blocker and the friend-checking suggestion as a relevant next step. The initial 24-trace v13 run returned Fail for this trace; the subsequent full rerun returned Pass. The one-trace result is saved separately in `analysis/report/unnecessary_messages_or_details-v13-support-0208-replicate.json` and was not included in either batch's metrics. No test trace was used.
