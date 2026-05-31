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

def finitePolicies : List (List Nat) := [[0, 0, 0], [0, 1, 0], [1, 0, 0], [1, 1, 1]]

theorem policy_enumeration_contains_forward :
    [0, 0, 0] ∈ finitePolicies := by
  simp [finitePolicies]

end TemplateActiveInference
