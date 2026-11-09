# HW5 v5 training review: useful detail versus related background

This is a learning note for the exploratory `unnecessary_messages_or_details-v5.txt` prompt. The examples below are from the fixed training split. Development cases informed the question, but no development or test trace is used as a prompt example. Human labels remain the student's decisions. The v5 development run is reviewed separately in `dev-unnecessary_messages_or_details-v5-review.md`.

## What changed from v3 to v4

V3 asked whether a clause could be removed while leaving the bare answer. V4 said that an optional explanation or next step can still be useful. That shifted all eight changed development verdicts from Fail to Pass. Four human Pass cases became correct, raising TPR from 8/13 to 12/13. Four human Fail cases became false Pass verdicts, lowering TNR from 8/11 to 4/11. Overall agreement stayed 16/24.

**The lesson:** “Could I delete this?” is too strict; almost every explanation can be deleted from a bare answer. “Is this about the same order or topic?” is too loose; an accurate field can concern the same order without helping with the user's question. The better question is: **What does this clause contribute to this user's specific request?** It should give the answer, a distinct fact or rule explaining it, the concrete blocker, or a practical way to continue. A brief required identifier or courtesy closing is also allowed. An extra detail is not justified merely by being true or sharing the subject.

## Training evidence for that boundary

| Training trace | Human label | What it teaches |
| --- | --- | --- |
| support-0048 | Pass | Shipped status and the general pre-shipment cancellation rule explain the cancellation decision; a return after delivery is a relevant next step. The rule and next step add value beyond the bare “cannot cancel.” |
| support-0212 | Pass | Permission denial explains why shipping status cannot be given. Checking the store's order system is a practical next step. A missing direct answer is not, by itself, unnecessary detail. |
| support-0156 | Pass | The completed escalation, ticket ID, and expected response time help the user track an unresolved delivery issue. They are more than generic order background. |
| support-0057 | Fail | “Eligible for a return, as it is eligible for a refund” restates the case-specific decision in different words rather than explaining the return rule. The offer to help with a return does not erase that separate repetition. |
| support-0148 | Fail | Friday payout timing and processing duration share the payout-policy topic but do not help answer whether refunds are deducted from the next payout. Their factual accuracy does not make them relevant to that question. |

## A review method for future judge prompts

1. Identify the **latest user question** and judge only the **final assistant reply**. Earlier messages and tool results provide context, not extra target text. A pre-tool plan and a post-tool confirmation are different updates.
2. For any questionable clause, name its role: answer, distinct reason or rule, blocker, information needed to retry, relevant next action, required identifier, or brief courtesy. If the only defense is “it gives context about the same order,” check again.
3. Distinguish a **distinct reason** from a **semantic restatement**. A status or policy rule may explain a decision; repeating the decision with synonymous words does not.
4. Treat a mixed reply clause by clause. A useful next step does not cancel an independently unrelated fact. For Fail, quote the offending words and say why they serve no relevant role. For Pass, explain why a suspicious-looking clause actually helps.

## What the v5 draft changes

V5 keeps the blocked-lookup and escalation protections from v4. It asks the judge to test each extra field for a **specific link** to the current question, distinct reason, blocker, case identification, or practical next step. It explicitly rejects “same order,” “general context,” or “might be interesting later” as enough to pass. Its five prompt examples remain the same training examples used in v4. The development disagreements were not copied into the prompt.

Two additional training examples were considered, then removed from the v5 prompt before any run:

- **support-0057 (Fail)** was intended to teach that a “because” clause can merely rename the decision. Its final reply is very close in wording and failure pattern to development support-0068. Using it verbatim could make a development gain on 0068 look more general than it is. The v5 draft keeps the semantic-restatement rule in general terms instead.
- **support-0156 (Pass)** was intended to teach that a completed escalation with a ticket ID differs from a pre-tool promise. It resembles development support-0166's final escalation pattern, and v4 already classified 0166 correctly. The v5 draft keeps the general planned-versus-completed rule without adding this example.

V4's development TPR point estimate is 92.3% (95% Wilson interval 66.7–98.6%), while TNR is 36.4% (15.2–64.6%). With 11 human Fail development cases, TNR above 50% would require at least 6 correct Fail verdicts, two more than v4's 4. Keeping TPR above 80% with 13 human Pass cases would require at least 11 correct Pass verdicts; v4 had 12. These are the student's selection preferences, not HW5 minimum scores, and a v5 prompt cannot guarantee them. The wide intervals matter when deciding how broadly to use the judge. See `dev-unnecessary_messages_or_details-v4-review.md` for the development disagreements.

V4 was frozen at the student's request before any test batch. The Cartwheel helper does not unfreeze a version. V5 has now been registered and run on development only; it is not frozen, and no v5 or v4 test predictions have been made. The handout allows at most two revisions after v0; v3, v4, and v5 are exploratory extra versions.
