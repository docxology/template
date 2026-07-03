# Story and Graphics

Every page is rendered as a full-page PNG. Some pages place text directly over
the illustration with shadowed lettering; others use a translucent box when the
scene is visually dense. The YAML `overlay_box` value controls that choice per
page.

The renderer uses simple geometric primitives: isometric cubes, shaded
tetrahedra, family clusters, a curved reciprocal symbol, and deterministic star
fields. The new stability page borrows from the Synergetics intuition that
triangulated structure braces square space: a tetrahedron is drawn through four
alternating cube corners so the cube becomes steadier without ceasing to be a
cube [@fuller1975synergetics]. This gives forks a readable baseline. Replacing
the story does not require editing Python; replacing the visual grammar does.
