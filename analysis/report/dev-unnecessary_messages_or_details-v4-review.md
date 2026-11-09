# Exploratory HW5 development review: unnecessary_messages_or_details v4

V4 is an extra exploratory revision beyond the handout's two-revision limit. It used `gpt-4o-mini` on the unchanged 24-trace development split (13 human Pass, 11 human Fail). The UI labels matched the HW5 labels before the run. No test predictions were made.

| Version | TP | FN | TN | FP | TPR (95% Wilson CI) | TNR (95% Wilson CI) | Agreement |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: |
| v1 | 7 | 6 | 10 | 1 | 53.8% (29.1–76.8%) | 90.9% (62.3–98.4%) | 70.8% |
| v2 | 8 | 5 | 8 | 3 | 61.5% (35.5–82.3%) | 72.7% (43.4–90.3%) | 66.7% |
| v3 | 8 | 5 | 8 | 3 | 61.5% (35.5–82.3%) | 72.7% (43.4–90.3%) | 66.7% |
| v4 | 12 | 1 | 4 | 7 | 92.3% (66.7–98.6%) | 36.4% (15.2–64.6%) | 66.7% |

Pass is the positive class. V4 made eight verdict changes from v3. It corrected four human Pass cases (support-0102, support-0177, support-0166, support-0208) and newly passed four human Fail cases (support-0068, support-0028, support-0065, support-0012). The gains in TPR came with an equal loss in TNR; overall agreement stayed 16/24.

## Cases targeted by the wording change

- **support-0102:** V4 calls the blocked store lookup explanation and request for store details relevant, matching the human Pass label.
- **support-0177:** V4 treats the explanation for one price and standardizing listings as useful, matching human Pass.
- **support-0166:** V4 evaluates the final escalation confirmation and ticket ID, rather than treating the earlier pre-tool promise as a duplicate, matching human Pass.
- **support-0208:** V4 allows the access restriction after the user challenges it, matching human Pass.
- **support-0174:** V4 still calls the brief offer of supported help unrelated and marks Fail against human Pass.
- **support-0181 and support-0217:** V4 still excuses unrelated order details as context and marks Pass against human Fail.

## New false Pass verdicts

- **support-0068:** V4 treats “marked as refund eligible” as a distinct reason for “eligible for a return”; the human note calls that a semantic restatement of the decision.
- **support-0028:** V4 treats historical order dates, store, and total as useful context for a request for the current refund status.
- **support-0065:** V4 treats refund eligibility and return processing as relevant to a question about whether the order remains inside its return window. The human note flags the extra eligibility description; a separate accuracy concern belongs to another mode.
- **support-0012:** V4 treats a full order detail list, including refund eligibility and a repeated status, as relevant to a current-status question.

V4 also marks support-0176 Pass against the human Fail label. Its blocked store lookup and request to confirm the store name resemble the Pass boundary applied to support-0102, so this is a human boundary review candidate if the student wants to revisit it. No human label was changed.

Raw metrics: `analysis/report/dev-unnecessary_messages_or_details-v4.json`. Prompt: `analysis/prompts/unnecessary_messages_or_details-v4.txt`. Cached predictions and critiques: `analysis/state/judges/unnecessary_messages_or_details-v4.json`.
