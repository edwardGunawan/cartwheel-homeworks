# PR title

Complete HW5 judge for unnecessary messages or details

# Summary

- Reuse the HW4 review interface and human evidence comments for `unnecessary_messages_or_details`. Export 60 labeled conversations with the original trace evidence and a fixed 12/24/24 training, development, and test split. The selected set contains 30 human Pass and 30 human Fail labels.
- Add the judge input, development, and test runners. DocETL applies the saved `gpt-4o-mini` prompt, caches verdicts and critiques, and the Cartwheel helpers compute confusion counts, TPR, TNR, and 95% Wilson intervals. The interface shows development disagreements beside human labels without exposing test predictions during prompt development.
- Preserve every evaluated prompt and judge record, the prompt iteration log, development reviews, the archived initial v13 run, and the one held-out v13 test. The student selected and froze v13 before the test.

# Results

Pass is the positive class. The final development batch used 13 human Pass and 11 human Fail traces. The held-out test used 12 of each.

| Split | TP / FN / TN / FP | TPR (95% Wilson CI) | TNR (95% Wilson CI) |
| --- | --- | --- | --- |
| Development, v13 | 12 / 1 / 6 / 5 | 92.3% (66.7–98.6%) | 54.5% (28.0–78.7%) |
| Held-out test, v13 | 11 / 1 / 3 / 9 | 91.7% (64.6–98.5%) | 25.0% (8.9–53.2%) |

The judge correctly accepts most human Pass cases, but on test it misses 9 of 12 human Fail cases. Its critiques often treat same-order facts or a possible future need as relevant even when those details do not serve the current request. The student would not fully trust the judge at this TNR and considers roughly 40–50% TNR a personal minimum for usefulness, not a course requirement. With only 12 Fail test cases, one changed verdict shifts TNR by about 8.3 percentage points.

# Checks

- Offline: review-app and replay-harness tests passed (the one HTTP test passed on rerun with local loopback access); submission split and frozen-judge checks passed; fixed split, label mapping, cached coverage, and test metrics were verified.
- Live: `gpt-4o-mini` judged the development batches and one held-out 24-trace test batch through DocETL. No prompt, human label, or split was changed after seeing test results.

# Course notes

- The handout asks for at most two prompt revisions. Versions v3–v13 are documented exploratory iterations beyond that limit; the deviation is visible in the iteration log.
- The required up-to-five-minute video is for the student to record. It is not part of this commit.
