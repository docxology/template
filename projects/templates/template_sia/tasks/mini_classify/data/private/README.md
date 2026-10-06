# Private task data

Evaluation-only labels for `mini_classify`. Not visible to target agents during runs.

`proposal_holdout.csv` is a frozen public synthetic fixture for the numeric
proposal lane. Its IDs are disjoint from the public selection dataset. The
controller scores it once after selection; neither its labels nor cases enter
model prompts, and Docker receives only its unlabelled features.
