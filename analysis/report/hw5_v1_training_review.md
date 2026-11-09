# HW5 v1 training review: unnecessary_messages_or_details

This review is based on the 12 saved training traces. The v1 prompt now includes support-0212 and a general blocked-lookup rule. No v1 judge batch has run. Development cases are mentioned only to explain the questions the training set needs to answer; they are not prompt examples.

| Training scenario | HW5 export label | Relevance to v1 |
| --- | --- | --- |
| support-0057 | Fail | The student's UI label and note were synced to HW5. The note identifies the refund-eligible clause as a restatement of the return decision. |
| support-0101 | Pass | Direct price answer; a simple clear Pass. |
| support-0156 | Pass | Escalation, ticket ID, and response time are relevant to the unresolved delivery problem. It supports keeping required escalation detail. |
| support-0050 | Fail | The unrelated refund eligibility after a cancellation decision is a clear Fail reason. The v1 critique now focuses on this, consistent with the useful explanation in support-0048. |
| support-0234 | Fail | Quantity and total are labeled unnecessary in a refund request. Because the amount might matter to a refund, this is a less clear prompt example unless the student confirms the boundary. |
| support-0048 | Pass | Shipped status, the cancellation rule, the decision, and a return option form a useful explanation and next step. Keep as a guard against treating every rule explanation as repetition. |
| support-0199 | Fail | The reply combines an incomplete answer with extra order/refund information. The unnecessary-detail reason should remain separate from the unfinished-request issue. |
| support-0083 | Fail | Mixes refund order fields with an unfinished refund request. The neighboring issue makes it a less clean prompt example. |
| support-0142 | Pass | Shipping timeframe helps answer “after an order”; the policy ID supports the policy answer. Already used in v0. |
| support-0212 | Pass | After denied access and a follow-up question, the final reply explains the restriction and gives a relevant next step. It is now Example 5 in v1. |
| support-0140 | Fail | The reply states the payout timing and then says to tell the merchant “this timeline.” Because the user asked what to tell the merchant, check whether that closing is redundant before using it as a repetition example. |
| support-0148 | Fail | Clear unrelated payout schedule added to a question about whether refunds are deducted from the next payout. Already used in v0. |

## Training findings and v1 status

1. **Label source is synchronized.** The student's UI decisions and notes now match the HW5 evaluation labels. The v0 development report was recalculated from its cached verdicts; v1 has not run.
2. **Example 3 was corrected.** Its Fail rationale is the unrelated refund detail and weak advice. The shipped-status explanation is analogous to the useful fact → rule → decision sequence in Pass case support-0048.
3. **Support-0212 was added as a borderline Pass example.** It shows why explaining a denied lookup and giving a relevant next step can be useful even after a follow-up question.
4. **The boundary now covers blocked lookups.** A missing direct answer alone does not establish this mode; the judge must identify independently unnecessary or repeated content in the final reply.

The prompt uses training examples only. V1 has now been run on the fixed development split; see `dev-unnecessary_messages_or_details-v1.json` and `dev-unnecessary_messages_or_details-v1-review.md` for results. No test predictions have been run.
