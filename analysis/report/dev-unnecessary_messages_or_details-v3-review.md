# Exploratory HW5 development review: unnecessary_messages_or_details v3

V3 is an extra exploratory revision beyond the handout's limit of two revisions after v0. It used the same fixed 24 development traces, `gpt-4o-mini` model, and current human labels (13 Pass, 11 Fail). It did not use or predict any test cases. The UI labels and HW5 labels matched before the run.

| Version | TP | FN | TN | FP | TPR (95% Wilson CI) | TNR (95% Wilson CI) | Agreement |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: |
| v1 | 7 | 6 | 10 | 1 | 53.8% (29.1–76.8%) | 90.9% (62.3–98.4%) | 70.8% |
| v2 | 8 | 5 | 8 | 3 | 61.5% (35.5–82.3%) | 72.7% (43.4–90.3%) | 66.7% |
| v3 | 8 | 5 | 8 | 3 | 61.5% (35.5–82.3%) | 72.7% (43.4–90.3%) | 66.7% |

Pass is the positive class. TPR is correct Pass verdicts divided by human Pass cases; TNR is correct Fail verdicts divided by human Fail cases.

## Verdicts changed from v2 to v3

| Trace | Human | v2 | v3 |
| --- | --- | --- | --- |
| support-0068 | Fail | Pass | Fail |
| support-0177 | Pass | Pass | Fail |
| support-0166 | Pass | Pass | Fail |
| support-0157 | Pass | Fail | Pass |
| support-0181 | Fail | Fail | Pass |
| support-0011 | Fail | Pass | Fail |
| support-0149 | Pass | Fail | Pass |
| support-0217 | Fail | Fail | Pass |

Four of these changes introduced new disagreements with the human labels:

- **support-0177 (human Pass, v3 Fail):** V3 calls the explanation for using one price and the offer to standardize listings redundant. V2 treated them as a rationale and a relevant next step. The v3 critique applies the “removable words” test too strictly to related help.
- **support-0166 (human Pass, v3 Fail):** V3 compares the assistant's pre-tool promise to escalate with its post-tool confirmation. The final reply reports that escalation happened and supplies ticket ID 162. Comparing two different turns and treating planned versus completed action as the same statement conflicts with the prompt's latest-reply rule.
- **support-0181 (human Fail, v3 Pass):** V3 notices the unrequested $9.75 total and delivery status but excuses them as transaction context, although the user asked what item they bought. V2 reached the human verdict, but its critique focused on the missing item name rather than these extra details, so its agreement was not fully grounded either.
- **support-0217 (human Fail, v3 Pass):** V3 notices refund eligibility was unrequested but excuses it as useful context. Order IDs and statuses can help disambiguate several matching orders; refund eligibility for each order does not answer the status request. V2's Fail verdict agreed with the human label, though its critique also broadly challenged listing multiple orders.

These are interpretations of the saved critiques, not proof of the model's internal reasoning or changes to the human labels.

## Boundary cases that remain incorrect

- **support-0102:** V3 calls the request to confirm store details unnecessary, although the store lookup returned `not_found` and the prompt explicitly allows a clarification needed to retry.
- **support-0208:** V3 calls the access explanation repetition across turns, although the user challenged the restriction in a new turn and the prompt says repetition across turns alone is not this failure.
- **support-0174:** V3 calls the single refusal sentence repetitive. It does not identify a repeated decision within that reply, and the reply briefly offers supported help.

V3 disagrees with current human labels on support-0102, support-0177, support-0166, support-0208, support-0174, support-0181, support-0217, and support-0176. The judge's critiques and verdicts are observations; they do not change human labels. Raw metrics are in `analysis/report/dev-unnecessary_messages_or_details-v3.json`; predictions and critiques are in `analysis/state/judges/unnecessary_messages_or_details-v3.json`.
