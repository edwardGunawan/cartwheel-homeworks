# HW5 Part B: close-variant review

Selected mode: `unnecessary_messages_or_details`.

The current HW4 labels contain 45 failure-present turns in 44 conversations. The
source export has 250 conversations across 263 turns. This review uses scenario metadata
only to find candidates for exclusion; none of that metadata belongs in judge
inputs.

The student approved treating the nine Fail subsets below as close variants.
One Fail conversation from each subset is included in the judge input. The
provisional representative scenario IDs are recorded in
`analysis/state/hw5_fail_variant_selections.json`; the original labels and
traces remain intact. The student can change which representative is kept
before the first prompt run. This leaves **31 distinct Fail conversations**.
The student also approved the Pass variant groups. Their provisional
representatives are in `analysis/state/hw5_pass_variant_selections.json`.

The groups below have the same role, intent, record state, information
completeness, resource relationship, policy, tool workflow, difficulty, and turn
count in `scenarios/support_scenarios.jsonl`. These metadata matches flagged
cases for review. The student's approval applies to the Fail subsets below and
the Pass selections in the separate manifest. In a mixed group, the approved
Fail representative is kept as that group's single judge input.

| Approved Fail group | Scenario IDs | Fail conversations |
| --- | --- | ---: |
| Multi-turn order status with a product clarification | `support-0217`–`support-0221` | 5 |
| Support lookup of a shipped order | `support-0003`, `support-0006`, `support-0009` | 3 |
| Merchant lookup of a shipped order | `support-0005`, `support-0008` | 2 |
| Shopper lookup of a delivered order | `support-0011`, `support-0017` | 2 |
| Merchant lookup of a delivered order | `support-0012`, `support-0015` | 2 |
| Shopper lookup of a refunded order | `support-0026`, `support-0029` | 2 |
| Shopper return eligibility with a Juniper policy | `support-0068`, `support-0224` | 2 |
| Merchant delivery dispute | `support-0157`, `support-0163` | 2 |
| Merchant review of the same damaged order link | `support-0202`, `support-0205` | 2 |

New Fail labels in distinct, currently single-Fail candidate groups are
`support-0025` (G039), `support-0127` (G050), and `support-0158` (G053).

The nine approved Fail groups contain 22 Fail conversations. Keeping one from
each removes 13 of the original 44 Fail conversations, leaving 31 eligible
Fail conversations. The approved Pass variant selections remove 116 of the
original 206 Pass conversations, leaving 90 eligible Pass conversations.
The student then requested exactly 30 of each. The fixed-seed selection in
`analysis/state/hw5_balanced_selection.json` produces **60 judge inputs:
30 Fail and 30 Pass** in `analysis/state/hw5_trace_inputs.json`.
Representative choices and the balanced subset can still be reviewed before
the first prompt run; no labels were changed.

## Part B split check

`analysis/state/splits.json` now has a split for
`unnecessary_messages_or_details` with seed 7 and fractions 20% training,
40% development, and 40% test. The split IDs are disjoint and exactly match
the 60 selected judge inputs.

| Split | Pass | Fail | Total |
| --- | ---: | ---: | ---: |
| Training | 6 | 6 | 12 |
| Development | 12 | 12 | 24 |
| Test | 12 | 12 | 24 |

Keep the saved inputs and split fixed during prompt development. Use only
training examples in the prompt.
