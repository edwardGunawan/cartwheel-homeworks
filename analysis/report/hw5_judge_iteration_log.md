# HW5 judge iteration log: unnecessary_messages_or_details

This log records the prompt change, hypothesis, and observed development result for each version, followed by the held-out test of frozen v13. The fixed development split has 24 traces: 13 current human Pass and 11 current human Fail. Pass is the positive class. Each live batch uses `gpt-4o-mini` through the Cartwheel DocETL helper. Human labels, exported inputs, and split IDs were not changed by prompt iteration.

The student's preferred development point estimates are TPR above 80% and TNR above 50%. With these denominators, that means at least 11/13 Pass and 6/11 Fail cases correct. These are personal selection preferences, not HW5 acceptance requirements. Repeated tuning on the same 24 cases can overfit development; the 95% Wilson intervals remain wide. The handout asks for at most two revisions after v0; v3 onward are exploratory extra versions.

| Version | Prompt | TP/FN/TN/FP | TPR | TNR | Agreement | Status |
| --- | --- | --- | ---: | ---: | ---: | --- |
| v0 | `analysis/prompts/unnecessary_messages_or_details-v0.txt` | 5/8/10/1 | 38.5% | 90.9% | 62.5% | Evaluated on dev |
| v1 | `analysis/prompts/unnecessary_messages_or_details-v1.txt` | 7/6/10/1 | 53.8% | 90.9% | 70.8% | Evaluated on dev |
| v2 | `analysis/prompts/unnecessary_messages_or_details-v2.txt` | 8/5/8/3 | 61.5% | 72.7% | 66.7% | Evaluated on dev |
| v3 | `analysis/prompts/unnecessary_messages_or_details-v3.txt` | 8/5/8/3 | 61.5% | 72.7% | 66.7% | Evaluated on dev |
| v4 | `analysis/prompts/unnecessary_messages_or_details-v4.txt` | 12/1/4/7 | 92.3% | 36.4% | 66.7% | Student manually reset status to draft after freeze; no test run |
| v5 | `analysis/prompts/unnecessary_messages_or_details-v5.txt` | 10/3/6/5 | 76.9% | 54.5% | 66.7% | Evaluated on dev |
| v6 | `analysis/prompts/unnecessary_messages_or_details-v6.txt` | 9/4/6/5 | 69.2% | 54.5% | 62.5% | Evaluated on dev |
| v7 | `analysis/prompts/unnecessary_messages_or_details-v7.txt` | 6/7/8/3 | 46.2% | 72.7% | 58.3% | Evaluated on dev |
| v8 | `analysis/prompts/unnecessary_messages_or_details-v8.txt` | 9/4/4/7 | 69.2% | 36.4% | 54.2% | Evaluated on dev |
| v9 | `analysis/prompts/unnecessary_messages_or_details-v9.txt` | 11/2/5/6 | 84.6% | 45.5% | 66.7% | Evaluated on dev |
| v10 | `analysis/prompts/unnecessary_messages_or_details-v10.txt` | 9/4/6/5 | 69.2% | 54.5% | 62.5% | Evaluated on dev |
| v11 | `analysis/prompts/unnecessary_messages_or_details-v11.txt` | 11/2/4/7 | 84.6% | 36.4% | 62.5% | Evaluated on dev |
| v12 | `analysis/prompts/unnecessary_messages_or_details-v12.txt` | 11/2/5/6 | 84.6% | 45.5% | 66.7% | Draft after student-requested unfreeze; no test run |
| v13 | `analysis/prompts/unnecessary_messages_or_details-v13.txt` | 12/1/6/5 | 92.3% | 54.5% | 75.0% | Frozen after two dev batches; held-out test completed |

## Retrospective prompt changes

### v0 → v1

- **Change:** Added a training Pass example for a denied order lookup after a follow-up question, plus a general blocked-lookup boundary.
- **Hypothesis:** A still-applicable access restriction and relevant next step should not be mistaken for unnecessary repetition or a missing answer.
- **Observed:** TPR rose from 5/13 to 7/13; TNR stayed 10/11. The prompt still missed some blocked-answer and next-step cases.

### v1 → v2

- **Change:** Clarified that a Fail needs independently repeated or materially unrelated content; permitted short explanations, ticket IDs, clarifications, and supported help after refusals. Training examples stayed fixed.
- **Hypothesis:** Explicit boundary rules would reduce false Fail verdicts on useful additions.
- **Observed:** TPR rose to 8/13, but TNR fell to 8/11. The judge still failed some protected cases.

### v2 → v3

- **Change:** Required the critique to quote exact removable words before marking Fail, rather than faulting a missing answer or ideal next step. Training examples stayed fixed.
- **Hypothesis:** Requiring evidence of an actual unnecessary span would prevent holistic helpfulness judgments.
- **Observed:** Aggregate counts stayed 8/13 Pass and 8/11 Fail correct, though eight individual verdicts changed. The judge still rationalized some incorrect Fail verdicts.

### v3 → v4

- **Change:** Replaced the strict “could these words be removed?” idea with “what role does each clause play?” and allowed optional but useful explanations and next steps.
- **Hypothesis:** Relevant explanations and next steps would be less likely to be marked unnecessary.
- **Observed:** All eight changed verdicts went Fail → Pass. TPR rose to 12/13, but TNR fell to 4/11 because the judge also excused unrelated fields as context.

### v4 → v5

- **Change:** Made the relevance test more specific: evaluate each extra field separately, require a connection to the current question, and distinguish a separate reason from a semantic restatement. Five training examples stayed unchanged. Two additional training examples were considered but removed before the run because their wording was too close to development cases.
- **Hypothesis:** The judge would stop accepting generic same-order context while retaining v4's useful blocker and next-step Pass decisions.
- **Observed:** TNR rose to 6/11, while TPR fell to 10/13. The judge newly failed human Pass support-0102 and support-0208. Its correct Fail critiques for support-0181 and support-0065 were partly misfocused or internally inconsistent, so the TNR gain should be treated cautiously.

### v5 → v6

- **Change:** Added a decision order emphasizing the latest user turn, blocked lookup explanations, challenged access restrictions, and supported help after an out-of-scope refusal. The stricter extra-field rule and five training examples stayed unchanged.
- **Hypothesis:** At least one of v5's false Fail verdicts would become Pass without losing its 6/11 Fail detection.
- **Observed:** Support-0102 and support-0174 changed correctly to Pass, but support-0157, support-0149, and support-0128 changed incorrectly to Fail. Support-0208 remained Fail. TPR fell to 9/13; TNR stayed 6/11. The broad decision-order rewrite was too disruptive to the Pass boundary.

### v5 → v7, one-sentence supported-help exception

- **Why this baseline:** V5 had the best TNR among the versions with more than half of human Fail cases correct. V6's broad rewrite hurt TPR and did not raise TNR. Evaluated v6 remains unchanged for an auditable history.
- **One change:** Make the v5 Pass definition explicitly allow one brief offer of supported help after an out-of-scope refusal, matching its existing boundary rule. Keep v5's extra-field relevance test, all five training examples, and the blocked-lookup wording unchanged.
- **Hypothesis before run:** This might correct a human Pass refusal case without reopening v4's broad acceptance of unrelated order fields. If one of v5's three false Fail cases became Pass and its 6 correct Fail verdicts remained, the point estimates would be at least 11/13 TPR (84.6%) and 6/11 TNR (54.5%). No dev example was added to the prompt.
- **Paid batch:** `gpt-4o-mini`, 24 fixed development traces, covered by the student's standing approval to iterate. No test batch.
- **Observed:** The intended refusal case remained Fail. TPR fell to 6/13 and TNR rose to 8/11. Four previously correct Pass cases became Fail while two previously missed Fail cases became correct. The single sentence produced broad, unpredictable changes; v7 is not an improvement under the student's two-rate preference. See `dev-unnecessary_messages_or_details-v7-review.md`.

### v5 → v8, one-sentence blocked-lookup exception

- **One change:** Add one Pass sentence saying that, after a tool lookup fails because an input was not found, naming the blocker and asking the user to confirm or correct that input is a practical same-request next step. It need not provide the missing fact or a full later procedure. Keep all other v5 wording and the five training examples unchanged.
- **Hypothesis before run:** This might correct one blocked-lookup human Pass case that v5 called Fail, while the unrelated-field rule kept at least 6/11 human Fail cases correct. One additional correct Pass with no Fail loss would give 11/13 TPR (84.6%) and 6/11 TNR (54.5%). V7 showed that even a single sentence can change unrelated verdicts, so this was uncertain.
- **Paid batch:** `gpt-4o-mini`, 24 fixed development traces under the student's standing approval. No test batch.
- **Observed:** Support-0102 became a correct Pass, but support-0157 and support-0128 became incorrect Fail and support-0201 and support-0011 became incorrect Pass. TPR fell to 9/13 and TNR to 4/11; the hypothesis failed. See `dev-unnecessary_messages_or_details-v8-review.md`.

### v4 → v9, direct-purpose test for tool facts

- **Why this baseline:** V4 already had TPR above the student's 80% preference (12/13), but TNR was only 4/11. V5, v7, and v8 demonstrated that broad or even small Pass-boundary edits can lose correct Pass verdicts.
- **One change:** In v4's Fail definition, require each extra fact copied from a tool result to serve a direct purpose for the current question, case identification, decision rationale, or relevant next action. Same-order or same-product context alone is insufficient. Keep v4's Pass rules and five training examples unchanged.
- **Hypothesis before run:** At least two human Fail cases with unrelated tool fields might change from Pass to Fail while retaining at least 11/13 correct Pass cases. That would produce TNR at least 6/11 (54.5%) and TPR at least 11/13 (84.6%). The previous small edits had broad effects, so this was uncertain.
- **Paid batch:** `gpt-4o-mini`, 24 fixed development traces under the student's standing approval. No test batch.
- **Observed:** TPR was 11/13 (84.6%) and TNR 5/11 (45.5%). Support-0181 and support-0174 became correct, while support-0208 and support-0130 became incorrect. The judge still accepted several unrelated tool fields as context. Its support-0065 critique acknowledged an unnecessary clause but returned Pass. See `dev-unnecessary_messages_or_details-v9-review.md`.

### v9 → v10, unconditional verdict consistency

- **One change:** Add one output instruction: if the critique identifies an independently unnecessary clause, the verdict must be Fail even if the rest of the reply is useful or the clause shares the broader order topic. Keep v9's criterion, Pass/Fail rules, and five training examples unchanged.
- **Hypothesis before run:** This might correct an internally inconsistent false Pass, such as a reply where the critique itself calls an extra field not directly useful. If at least one human Fail case changed correctly while all 11 correct Pass cases remained, the point estimates would reach at least 11/13 TPR (84.6%) and 6/11 TNR (54.5%). The model might change other verdicts unpredictably.
- **Paid batch:** `gpt-4o-mini`, 24 fixed development traces under the student's standing approval. No test batch.
- **Observed:** Support-0065 became a correct Fail and support-0130 a correct Pass, but support-0102, support-0157, and support-0174 became incorrect Fail. TPR fell to 9/13 and TNR rose to 6/11. The unconditional instruction over-applied to useful clarifications, next steps, and supported-help offers. See `dev-unnecessary_messages_or_details-v10-review.md`.

### v9 → v11, tool-fact verdict consistency

- **One change:** Narrow v10's verdict-consistency instruction to an extra fact copied from a tool result that the critique itself finds without a direct purpose. Explicitly preserve relevant blocker explanations, retry clarifications, supported-help offers after refusal, and same-issue next steps. Keep v9's main rules and five training examples unchanged.
- **Hypothesis before run:** The narrower instruction might catch one more unrelated tool fact than v9 without wrongly failing its already-correct Pass cases. If so, TPR would remain at least 11/13 (84.6%) and TNR reach at least 6/11 (54.5%). The prior versions showed that a small wording change could still affect unrelated cases.
- **Paid batch:** `gpt-4o-mini`, 24 fixed development traces under the student's standing approval. No test batch.
- **Observed:** TPR remained 11/13 but TNR fell to 4/11. Support-0130 became a correct Pass, support-0157 an incorrect Fail, and support-0025 an incorrect Pass. The intended extra-field correction did not occur. See `dev-unnecessary_messages_or_details-v11-review.md`.

### v9 → v12, single-property relevance

- **One change:** Add a single-attribute relevance rule to v9's Fail definition: when the user asks for one property of a record, other fields from that record need a direct purpose beyond sharing the record. Keep the v9 Pass boundary and five training examples unchanged.
- **Hypothesis before run:** The rule might catch at least one more human Fail case with unrequested fields while keeping v9's 11/13 correct Pass cases. That would meet the student's preferred point estimates of TPR above 80% and TNR above 50%. Prior prompt sensitivity made the outcome uncertain.
- **Paid batch:** `gpt-4o-mini`, 24 fixed development traces under the student's standing approval. No test batch.
- **Observed:** The aggregate rates stayed 11/13 TPR and 5/11 TNR. Support-0012 and support-0130 improved, while support-0174 and support-0025 worsened. V9 and v12 have identical counts but different error cases. See `dev-unnecessary_messages_or_details-v12-review.md`.

## Review point after v12

None of the evaluated versions has both preferred development point estimates (TPR above 80% and TNR above 50%) at once. V9 and v12 are one correct human Fail case short while preserving 11/13 correct Pass cases. V5 and v10 exceed 50% TNR but fall below 80% TPR. Repeated small edits have moved unrelated verdicts, so continuing until a point estimate crosses both thresholds would increasingly select for this one development set rather than establish a reliable boundary. The human label for support-0176 versus the similar blocked-lookup Pass support-0102, and the support-0128 Pass note's mixed rationale, are candidates for student review. No label was changed. No test predictions were made.

## Freeze state after student review

The student manually changed v4's saved `status` from `frozen` to `draft` and removed its `frozen_at` field. This changed metadata only; the v4 prompt hash and cached development predictions remain. At the student's earlier request, v12 was then frozen through `freeze_judge`. V12 has 24 cached development predictions and no test predictions. The official helper does not offer an unfreeze operation.

## V13 priority boundary

- **Observation:** In v12, human Pass support-0208 and support-0174 were judged Fail. The 0208 critique counted a restriction repeated across turns. The 0174 critique treated a short supported-help offer after an out-of-scope refusal as unrelated. V12 already permitted both in its boundary rules, but used the weaker phrase “can be relevant.”
- **Student priority:** Correct Pass decisions for constrained replies are more important to the student than catching the semantic repetition in human Fail support-0068.
- **Change:** Add one priority rule before the general Pass/Fail definitions. It treats one still-applicable restriction after a challenge, a brief out-of-scope refusal, and one supported-help offer as relevant. It still checks for a separate unnecessary clause. The five training examples and all other v12 text are unchanged. No development or test example was added to the prompt.
- **Hypothesis before run:** The judge may stop counting cross-turn repetition and supported-help offers as this failure, while the independent-extra-detail rule remains available for other traces. A prompt rule cannot guarantee these verdicts; earlier small edits changed unrelated cases.
- **Paid batch:** `gpt-4o-mini` judged the same 24 fixed development traces after the student's approval. No test batch.
- **Observed:** TPR rose from 11/13 to 12/13 and TNR from 5/11 to 6/11. Support-0174 changed correctly to Pass; support-0025 and support-0028 changed correctly to Fail; support-0012 changed incorrectly to Pass. Support-0208 remains an incorrect Fail: its critique still counts a restriction repeated across turns, contrary to the new priority rule. Support-0068 remains an incorrect Pass. See `dev-unnecessary_messages_or_details-v13-review.md`.
- **Status at evaluation:** V13 was draft and v12 was frozen. No test predictions were made.
- **Separate support-0208 replicate:** A fresh, user-approved `gpt-4o-mini` call on this one development trace with the unchanged v13 prompt returned Pass, whereas the original v13 batch returned Fail. The replicate critique applied the priority boundary. It is saved separately and does not alter v13's 24-trace metrics or cache. See `dev-unnecessary_messages_or_details-v13-review.md`.
- **Full v13 rerun:** At the student's request, the first v13 judge record, metrics, and review were archived; the active prediction and critique cache was cleared. A fresh `gpt-4o-mini` batch on all 24 development traces returned the same counts: TP 12, FN 1, TN 6, FP 5; TPR 92.3%, TNR 54.5%. Relative to the first v13 batch, support-0208 and support-0065 changed correctly, while support-0102 and support-0028 changed incorrectly. The active v13 report and cache now contain this rerun. The first run is retained as `dev-unnecessary_messages_or_details-v13-initial.json` and `analysis/state/judges/archive/unnecessary_messages_or_details-v13-initial.json`. No labels, splits, prompt, or test predictions changed.

## Student-selected freeze after v13 rerun

At the student's request, v12 was changed from `frozen` to `draft` and its `frozen_at` field was removed; the helper has no unfreeze operation. V13 was then frozen with `freeze_judge`. Both versions retained their prompts and development caches. At that point, neither had test predictions. The active selected judge is v13.

## Part D held-out test

After the student approved the paid batch, frozen v13 was run once with `gpt-4o-mini` on the 24 test traces (12 human Pass, 12 human Fail). The result was TP 11, FN 1, TN 3, FP 9: TPR 91.7% (95% Wilson CI 64.6–98.5%) and TNR 25.0% (8.9–53.2%). The nine false Pass verdicts are missed failures. The student does not fully trust the judge at this TNR and identifies overacceptance of same-order or possible-future details as the main issue; their personal usefulness criterion is around 40–50% TNR. See `test-unnecessary_messages_or_details-v13-review.md`. No prompt, label, or split was changed after seeing test results.

## Next iteration rule

Keep every evaluated prompt and prior batch available. If rerunning the same version, archive its existing record and metrics before clearing the active cache. Draft any changed prompt as a new version from the best earlier baseline, make one narrow general change, record the predicted effect before running, then compare the saved development verdicts and critiques. Use training examples only in prompts. Do not edit human labels, export, split, or test predictions to improve a development score. A frozen version stays frozen; another candidate gets a new version ID.
