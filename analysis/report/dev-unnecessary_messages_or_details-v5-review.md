# Exploratory HW5 development review: unnecessary_messages_or_details v5

V5 used `gpt-4o-mini` on the fixed 24 development traces (13 human Pass, 11 human Fail). UI and HW5 labels matched before the run. The five prompt examples are unchanged from v4 and all come from training. V5 is an exploratory version beyond the handout's revision limit. No test predictions were made.

| Version | TP | FN | TN | FP | TPR (95% Wilson CI) | TNR (95% Wilson CI) | Agreement |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: |
| v4 | 12 | 1 | 4 | 7 | 92.3% (66.7–98.6%) | 36.4% (15.2–64.6%) | 66.7% |
| v5 | 10 | 3 | 6 | 5 | 76.9% (49.7–91.8%) | 54.5% (28.0–78.7%) | 66.7% |

Pass is the positive class. V5 changed four development verdicts from v4, all Pass to Fail. It correctly caught two more human Fail cases (support-0181 and support-0065) but newly failed two human Pass cases (support-0102 and support-0208). The TNR point estimate rose above the student's 50% preference, but TPR fell below the student's 80% preference. Agreement stayed 16/24. These preferences are not HW5 acceptance requirements, and the small class counts leave broad uncertainty.

## Critique quality on changed cases

- **support-0102:** V5 marked Fail because it called the blocked-store explanation repetitive of a prior promise and the request to confirm store details insufficiently actionable. This conflicts with the prompt's latest-reply and blocked-lookup rules. Human label: Pass.
- **support-0208:** V5 marked Fail because it counted the access restriction repeated after the user challenged it. This conflicts with the prompt's explicit challenged-restriction rule. Human label: Pass.
- **support-0181:** V5 marked Fail, agreeing with the human label, but its critique faulted the sentence saying the item name was missing. That sentence explains the blocker; the unrequested total and delivery status are the stronger unnecessary-detail evidence. The correct verdict is not fully supported by the critique.
- **support-0065:** V5 marked Fail, agreeing with the human label, and noticed the unrequested refund-eligibility clause. However, the critique ends by saying that clause "does not constitute a failure," contradicting its Fail verdict. Treat this agreement cautiously.

V5's remaining disagreements are support-0068, support-0174, support-0028, support-0217, support-0012, and support-0176, plus support-0102 and support-0208 above. Support-0176's human Fail label remains a boundary review candidate because its blocked store lookup and request for confirmation resemble support-0102's human Pass boundary. No human label was changed.

Raw metrics: `analysis/report/dev-unnecessary_messages_or_details-v5.json`. Prompt: `analysis/prompts/unnecessary_messages_or_details-v5.txt`. Cached predictions and critiques: `analysis/state/judges/unnecessary_messages_or_details-v5.json`.
