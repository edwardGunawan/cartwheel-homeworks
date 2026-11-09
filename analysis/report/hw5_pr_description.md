# PR title

HW5: Test a judge for unnecessary support details

# PR description

## Summary

I built one judge for the `unnecessary_messages_or_details` failure mode.
I used 60 conversations with human labels: 30 Pass and 30 Fail.
I kept the same data split during the work: 12 training, 24 development, and 24 test conversations.
This PR includes the labels, input traces, prompts, judge results, and reports.

## Prompt changes

- The first prompt found most Fail cases. It also marked many useful replies as Fail.
- I changed the rules to keep short explanations of blocked lookups and access limits. The rules also keep required policy IDs and useful next steps.
- These changes improved TPR. They also let some unrelated order details pass.
- I then made the relevance rule more exact. An extra fact must help answer the current question, explain a decision, or give a useful next step.
- In v13, a reply can state an access limit again when the user challenges that limit. I used only training cases as prompt examples.

## Development result

Pass is the positive class. TPR measures correct Pass results. TNR measures correct Fail results.

| Set | Human Pass / Fail | TPR and 95% Wilson interval | TNR and 95% Wilson interval |
| --- | --- | --- | --- |
| Development, v13 | 13 / 11 | 92.3% (66.7–98.6%) | 54.5% (28.0–78.7%) |
| Test, frozen v13 | 12 / 12 | 91.7% (64.6–98.5%) | 25.0% (8.9–53.2%) |

In development, v13 agreed with 12 of 13 human Pass labels and 6 of 11 human Fail labels.
These results met my preferred balance, so I froze v13.
The small number of cases gave wide confidence intervals. Some individual results also changed when I ran v13 again.

## Test result and use decision

I ran frozen v13 once on the test set.
The judge agreed with 11 of 12 human Pass labels. It agreed with only 3 of 12 human Fail labels.
Thus, the judge missed nine Fail cases.
The judge often treated facts from the same order as useful. It also accepted details that might help with a future question.
These details did not always help with the current question.

I do not fully trust this judge at a TNR of 25%.
I wanted a TNR of about 40% to 50% before I would consider it useful. This is my goal, not a course rule.
The test set is small. One changed result among the 12 human Fail cases changes TNR by about 8.3 percentage points.

## Checks and course note

The offline checks for the review interface, data split, judge status, and saved results passed.
I used `gpt-4o-mini` with DocETL for the live judge runs.
I did not change the prompt, human labels, or data split after the test.

The handout permits two prompt revisions. I made more versions to study the boundary. The iteration log records this extra work.
I will record the required video separately.
