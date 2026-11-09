# HW5 Part D held-out test: unnecessary_messages_or_details v13

Frozen v13 was run once through DocETL with `gpt-4o-mini` on all 24 held-out test traces. The test split had 12 human Pass and 12 human Fail labels. The prompt and human labels were unchanged after the development review. Pass is the positive class.

| Split | Human Pass | Human Fail | TP | FN | TN | FP | TPR (95% Wilson CI) | TNR (95% Wilson CI) | Agreement |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: |
| Development, final v13 rerun | 13 | 11 | 12 | 1 | 6 | 5 | 92.3% (66.7–98.6%) | 54.5% (28.0–78.7%) | 75.0% |
| Held-out test | 12 | 12 | 11 | 1 | 3 | 9 | 91.7% (64.6–98.5%) | 25.0% (8.9–53.2%) | 58.3% |

On test, the judge agreed with 11 of 12 human Pass labels but only 3 of 12 human Fail labels. The nine false Pass verdicts are missed failures of this mode. TNR was lower on held-out test than on development, and both intervals are wide with 12 cases per class. The handout sets no numerical acceptance threshold. Based on this one test, I would not rely on v13 alone to detect this failure mode; its missed-failure rate is too high for unattended use.

## Student's use assessment

The student finds the high TPR encouraging but does not fully trust v13 because its test TNR is low: nine of twelve human Fail cases received false Pass verdicts. Their main diagnosis is that the judge often treats details about the same order, or a possible future need, as sufficient reason to include them. They would want a TNR around 40–50% before considering the judge useful; this is their own criterion, not a HW5 requirement. They also note the small sample: with twelve human Fail cases, one changed verdict moves the observed TNR by 1/12, or about 8.3 percentage points. The 95% Wilson interval of 8.9–53.2% reflects substantial uncertainty around the 25.0% point estimate. This assessment does not change the frozen judge or the test result.

The 10 test disagreements, shown as human label → judge verdict, are:

| Trace | Human → judge |
| --- | --- |
| support-0003 | Fail → Pass |
| support-0019 | Fail → Pass |
| support-0051 | Pass → Fail |
| support-0131 | Fail → Pass |
| support-0143 | Fail → Pass |
| support-0158 | Fail → Pass |
| support-0187 | Fail → Pass |
| support-0191 | Fail → Pass |
| support-0202 | Fail → Pass |
| support-0248 | Fail → Pass |

## Why the nine human Fail cases became judge Pass

These are descriptions of the saved test critiques, not changes to the student's labels. Where a saved human note does not identify an exact span, the likely unnecessary content below is an interpretation for student review.

| Trace | Likely failure type under the human Fail label | Why v13 said Pass |
| --- | --- | --- |
| support-0003 | Unasked refund eligibility after a shipping-status answer | Treated refund eligibility as relevant “financial aspects” of the same order. |
| support-0019 | Broad order-detail dump, including quantity, total, and refund eligibility, after answering status | Read “what does the record show?” broadly and justified extra fields as comprehensive context or useful for a possible follow-up. |
| support-0131 | Opened-item fee cap and opt-in details in an answer about an unopened return | Treated the opened-item rules as policy context and the concluding customer-facing sentence as an actionable answer. The latter may itself be useful because the user asked what to tell the customer. |
| support-0143 | Possible semantic restatement of “original payment method” as “the same way they paid” | Treated the paraphrase as explanation and the policy-lookup offer as a useful optional next step. |
| support-0158 | Unasked refund eligibility in a delivered-but-not-received complaint | Assumed refund eligibility was relevant to a possible refund expectation, even though the request was to handle the delivery complaint. |
| support-0187 | Recent-orders tangent in a product-price lookup | Treated recent orders as a possible way to clarify product pricing and grouped that tangent with the more relevant request for product details. |
| support-0191 | Unasked refund eligibility in an answer about delivery appearing before shipment | Explicitly noticed the refund detail was off-topic, but excused it because the main answer was still understandable. |
| support-0202 | Delivery and refund details in an answer about why a product appears on an order | Treated unrelated same-order fields as status context. |
| support-0248 | “Already refunded” followed by “no longer eligible for a new refund” as a possible semantic restatement | Treated the second clause as a distinct explanation of the refund decision; the student's earlier note identified it as unnecessary. |

The dominant pattern is that the judge grants relevance because information concerns the same order, policy, or a conceivable follow-up. That conflicts with v13's narrower requirement that each extra fact serve the current question, decision, or practical continuation. The semantic-restatement cases are subtler and remain for the student to assess. No prompt or label was changed after the test.

This is the final held-out measurement for frozen v13. Do not revise v13 using these test cases or rerun the test to select a favorable result. The saved metrics are in `analysis/report/test-unnecessary_messages_or_details-v13.json`; the test predictions and critiques are cached in `analysis/state/judges/unnecessary_messages_or_details-v13.json`. The student's overall use assessment is recorded above; any further per-case review remains their decision.
