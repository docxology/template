# Methodology

Each node carries a status from the ladder {provisional, frozen, answered}. A provisional node may be frozen (preregistered, immutable) or answered directly. Answering a frozen node is refused by construction: preregistered commitments may not be back-filled. Within one tree, each run_command may be declared by at most one node, so an experiment identity maps one-to-one onto the command that runs it.
