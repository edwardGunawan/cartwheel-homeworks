# HW5 development review: unnecessary_messages_or_details v2

The `gpt-4o-mini` judge ran on the fixed 24-trace development split. The current human labels contain 13 Pass and 11 Fail cases. The UI labels and notes matched all 263 live records in `analysis/state/hw5_labels/unnecessary_messages_or_details.jsonl` before this run; no label copy or split change was needed.

| Version | TP | FN | TN | FP | TPR (95% Wilson CI) | TNR (95% Wilson CI) | Agreement |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: |
| v1 | 7 | 6 | 10 | 1 | 53.8% (29.1–76.8%) | 90.9% (62.3–98.4%) | 70.8% |
| v2 | 8 | 5 | 8 | 3 | 61.5% (35.5–82.3%) | 72.7% (43.4–90.3%) | 66.7% |

Here, Pass is the positive class: TPR measures correct Pass verdicts, and TNR measures correct Fail verdicts. The intervals quantify sampling uncertainty from these small denominators; they do not come from running the judge multiple times.

## Verdicts changed from v1 to v2

| Trace | Human label | v1 | v2 |
| --- | --- | --- | --- |
| support-0177 | Pass | Fail | Pass |
| support-0166 | Pass | Fail | Pass |
| support-0157 | Pass | Pass | Fail |
| support-0011 | Fail | Fail | Pass |
| support-0176 | Fail | Fail | Pass |

V2 disagrees with the current human labels on support-0068, support-0102, support-0208, support-0157, support-0174, support-0011, support-0149, and support-0176. These are review candidates, not automatic label changes. The human labels and final judge choice remain the student's decisions.

The v2 cache contains all 24 development predictions and critiques, with no test predictions. Raw results: `analysis/report/dev-unnecessary_messages_or_details-v2.json`. Prompt: `analysis/prompts/unnecessary_messages_or_details-v2.txt`.
