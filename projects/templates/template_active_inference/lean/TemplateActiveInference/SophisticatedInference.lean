namespace TemplateActiveInference

/-- Planning horizon for sophisticated inference (policy length > 1). -/
def defaultPolicyLen : Nat := 3

theorem sophisticated_requires_horizon :
    defaultPolicyLen > 1 := by decide

inductive TMazeState where
  | start
  | cue
  | goal
  deriving DecidableEq, Repr

/-- Deterministic finite T-maze transition boundary used by the Python harness. -/
def tmazeStep : TMazeState -> Nat -> TMazeState
  | TMazeState.start, 0 => TMazeState.cue
  | TMazeState.start, _ => TMazeState.start
  | TMazeState.cue, 0 => TMazeState.goal
  | TMazeState.cue, _ => TMazeState.cue
  | TMazeState.goal, _ => TMazeState.goal

theorem tmaze_two_forward_steps_reach_goal :
    tmazeStep (tmazeStep TMazeState.start 0) 0 = TMazeState.goal := by
  rfl

theorem tmaze_goal_absorbing (action : Nat) :
    tmazeStep TMazeState.goal action = TMazeState.goal := by
  rfl

inductive GraphWorldState where
  | start
  | cue
  | choice
  | goal
  deriving DecidableEq, Repr

/-- Deterministic four-node graph-world transition used by the extension artifact. -/
def graphWorldStep : GraphWorldState -> Nat -> GraphWorldState
  | GraphWorldState.start, 0 => GraphWorldState.cue
  | GraphWorldState.start, _ => GraphWorldState.start
  | GraphWorldState.cue, 0 => GraphWorldState.choice
  | GraphWorldState.cue, _ => GraphWorldState.cue
  | GraphWorldState.choice, 0 => GraphWorldState.goal
  | GraphWorldState.choice, _ => GraphWorldState.choice
  | GraphWorldState.goal, _ => GraphWorldState.goal

theorem graph_world_three_steps_reach_goal :
    graphWorldStep (graphWorldStep (graphWorldStep GraphWorldState.start 0) 0) 0 = GraphWorldState.goal := by
  rfl

inductive BranchGraphWorldState where
  | start
  | cue
  | branch
  | goal
  deriving DecidableEq, Repr

/-- Deterministic four-node branch topology used by the topology sweep. -/
def branchGraphWorldStep : BranchGraphWorldState -> Nat -> BranchGraphWorldState
  | BranchGraphWorldState.start, 0 => BranchGraphWorldState.cue
  | BranchGraphWorldState.start, _ => BranchGraphWorldState.start
  | BranchGraphWorldState.cue, 0 => BranchGraphWorldState.branch
  | BranchGraphWorldState.cue, _ => BranchGraphWorldState.cue
  | BranchGraphWorldState.branch, 0 => BranchGraphWorldState.goal
  | BranchGraphWorldState.branch, _ => BranchGraphWorldState.branch
  | BranchGraphWorldState.goal, _ => BranchGraphWorldState.goal

theorem branch_graph_world_three_steps_reach_goal :
    branchGraphWorldStep
      (branchGraphWorldStep (branchGraphWorldStep BranchGraphWorldState.start 0) 0) 0
        = BranchGraphWorldState.goal := by
  rfl

inductive LoopGraphWorldState where
  | start
  | cue
  | loop
  | choice
  | goal
  deriving DecidableEq, Repr

/-- Deterministic five-node loop topology used by the topology sweep. -/
def loopGraphWorldStep : LoopGraphWorldState -> Nat -> LoopGraphWorldState
  | LoopGraphWorldState.start, 0 => LoopGraphWorldState.cue
  | LoopGraphWorldState.start, _ => LoopGraphWorldState.start
  | LoopGraphWorldState.cue, 0 => LoopGraphWorldState.loop
  | LoopGraphWorldState.cue, _ => LoopGraphWorldState.cue
  | LoopGraphWorldState.loop, 0 => LoopGraphWorldState.choice
  | LoopGraphWorldState.loop, _ => LoopGraphWorldState.loop
  | LoopGraphWorldState.choice, 0 => LoopGraphWorldState.goal
  | LoopGraphWorldState.choice, _ => LoopGraphWorldState.choice
  | LoopGraphWorldState.goal, _ => LoopGraphWorldState.goal

theorem loop_graph_world_four_steps_reach_goal :
    loopGraphWorldStep
      (loopGraphWorldStep
        (loopGraphWorldStep (loopGraphWorldStep LoopGraphWorldState.start 0) 0) 0) 0
        = LoopGraphWorldState.goal := by
  rfl

inductive DiamondGraphWorldState where
  | start
  | cue
  | left
  | merge
  | goal
  deriving DecidableEq, Repr

/-- Deterministic five-node diamond topology used by the topology sweep. -/
def diamondGraphWorldStep : DiamondGraphWorldState -> Nat -> DiamondGraphWorldState
  | DiamondGraphWorldState.start, 0 => DiamondGraphWorldState.cue
  | DiamondGraphWorldState.start, _ => DiamondGraphWorldState.start
  | DiamondGraphWorldState.cue, 0 => DiamondGraphWorldState.left
  | DiamondGraphWorldState.cue, _ => DiamondGraphWorldState.cue
  | DiamondGraphWorldState.left, 0 => DiamondGraphWorldState.merge
  | DiamondGraphWorldState.left, _ => DiamondGraphWorldState.left
  | DiamondGraphWorldState.merge, 0 => DiamondGraphWorldState.goal
  | DiamondGraphWorldState.merge, _ => DiamondGraphWorldState.merge
  | DiamondGraphWorldState.goal, _ => DiamondGraphWorldState.goal

theorem diamond_graph_world_four_steps_reach_goal :
    diamondGraphWorldStep
      (diamondGraphWorldStep
        (diamondGraphWorldStep (diamondGraphWorldStep DiamondGraphWorldState.start 0) 0) 0) 0
        = DiamondGraphWorldState.goal := by
  rfl

def finitePolicies : List (List Nat) := [[0, 0, 0], [0, 1, 0], [1, 0, 0], [1, 1, 1]]

theorem policy_enumeration_contains_forward :
    [0, 0, 0] ∈ finitePolicies := by
  simp [finitePolicies]

/-- Integer-weight witness for a two-state normalized toy belief denominator. -/
def twoStateBeliefWeights : List Nat := [1, 1]

theorem two_state_belief_weights_sum_to_two :
    twoStateBeliefWeights.foldl Nat.add 0 = 2 := by
  rfl

/-- Integer-weight witness for a two-policy posterior denominator. -/
def twoPolicyPosteriorWeights : List Nat := [1, 1]

theorem two_policy_posterior_weights_sum_to_two :
    twoPolicyPosteriorWeights.foldl Nat.add 0 = 2 := by
  rfl

end TemplateActiveInference
