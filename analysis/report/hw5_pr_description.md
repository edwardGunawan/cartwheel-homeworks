# PR title

HW5: Build and evaluate a judge for unnecessary support details

# PR description

## Overview

I built one LLM judge for the `unnecessary_messages_or_details` failure mode. I reused my HW4 review interface and human labels, selected 30 Pass and 30 Fail conversations, and kept the 12/24/24 training, development, and test split fixed throughout prompt development. The judge uses `gpt-4o-mini` through DocETL. This PR saves the input export, prompts, labels, verdicts, critiques, and evaluation reports.

## Prompt iteration

The first prompt detected most Fail cases but marked many useful replies as Fail. I revised the boundary to protect explanations of blocked lookups, access restrictions, policy requirements, and relevant next steps. Those changes raised the rate of correctly judged Pass cases, but sometimes made the judge too willing to accept extra order details. Later versions tested a more specific relevance rule: an added fact must help answer the current request, explain the decision, or advance a practical next step. I chose v13 because its development result met my preferred balance. Its priority rule also clarifies that restating an access restriction after the user challenges it is relevant to the new turn. The five prompt examples come only from training data.

## Development and held-out test

Pass is the positive class. Both rates use 95% Wilson confidence intervals.

| Split | Human Pass / Fail | TP / FN / TN / FP | TPR | TNR |
| --- | --- | --- | --- | --- |
| Development, v13 | 13 / 11 | 12 / 1 / 6 / 5 | 92.3% (66.7–98.6%) | 54.5% (28.0–78.7%) |
| Held-out test, frozen v13 | 12 / 12 | 11 / 1 / 3 / 9 | 91.7% (64.6–98.5%) | 25.0% (8.9–53.2%) |

### Development assessment

The v13 development result met my preferred balance: it accepted 12 of 13 human Pass cases and detected 6 of 11 human Fail cases. That was enough for me to freeze the prompt, although the intervals were wide and different runs changed some individual verdicts.

### Test assessment

The held-out result changed my assessment. The judge still accepted most human Pass cases, but it marked 9 of 12 human Fail cases as Pass. Its critiques often treated information from the same order or a possible future need as relevant even when it did not serve the current request. I would not fully trust this judge at a 25% TNR. I had hoped for roughly 40–50% TNR before considering it useful; that is my own criterion, not a course requirement. The test set is small: one changed verdict among 12 human Fail cases moves TNR by about 8.3 percentage points, and the wide interval shows uncertainty around the point estimate.

## Verification and course note

Offline review-interface, submission, and artifact checks passed. Frozen v13 was run once on the held-out test; I did not change the prompt, labels, or split after seeing those results. The handout asks for at most two revisions, while v3–v13 were additional exploratory versions; the iteration log records that deviation. I will record the required video separately.
