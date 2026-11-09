# HW5 v1 development review: unnecessary_messages_or_details

V1 used `gpt-4o-mini` on the 24 fixed development traces. The student later changed support-0157 and support-0128 to Pass. The tables below rescore the cached v0 and v1 verdicts against the current human labels; no model rerun was needed. Pass is the positive class. Test predictions remain unrun.

| Prompt | Human Pass | Human Fail | TP | FN | TN | FP | TPR and 95% Wilson interval | TNR and 95% Wilson interval |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| v0, rescored with current labels | 13 | 11 | 5 | 8 | 10 | 1 | 38.5% (17.7–64.5%) | 90.9% (62.3–98.4%) |
| v1 | 13 | 11 | 7 | 6 | 10 | 1 | 53.8% (29.1–76.8%) | 90.9% (62.3–98.4%) |

V1 changed two verdicts relative to v0: `support-0157` and `support-0128` changed from Judge Fail to Judge Pass. Both now have human Pass labels, so v1 agrees with those decisions. The other 22 development verdicts were unchanged. V1 has seven disagreements:

| Human label | Judge verdict | Scenarios |
| --- | --- | --- |
| Pass | Fail | `support-0102`, `support-0177`, `support-0166`, `support-0208`, `support-0174`, `support-0149` |
| Fail | Pass | `support-0068` |

The judge verdicts and critiques are cached under `analysis/state/judges/unnecessary_messages_or_details-v1.json`; the full metrics are in `analysis/report/dev-unnecessary_messages_or_details-v1.json`. The review interface shows the critiques beside the human labels and can filter to disagreements. The student decides whether each disagreement calls for a label correction, prompt revision, or no change. There is no required score threshold.
