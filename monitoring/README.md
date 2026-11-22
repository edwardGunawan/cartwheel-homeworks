# Homework 7 interpretation

1. **Did the corrected failure estimate move?** The point estimate for `unnecessary_messages_or_details` moved from 10% before to 100% after. Both periods used 10 random conversations. This change does not establish that the true failure rate increased.

2. **Do the intervals support a conclusion?** No. Both 95% intervals span 0% to 100%. The random samples are small, and the frozen judge detected only 25% of the human-labeled failures in its Homework 5 test set. The corrected estimates are too uncertain to support a conclusion about the change.

3. **What did the risk group reveal?** The judge flagged no `policy_lookup` conversations: 0 of 6 before and 0 of 5 after. These extra reviews found no additional flagged cases. They do not prove that the group had no failures, and they do not estimate the overall failure rate.

4. **What happens after a threshold crossing?** Crossing the 15% threshold starts error analysis of the flagged traces. Confirm real failures, add them as evaluation cases to the Homework 6 suite, fix the agent, and rerun the suite to check the fix.
