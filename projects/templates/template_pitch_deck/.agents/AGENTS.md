# Agent guidance for `template_pitch_deck`

Use the project-local skill bundle in `.agents/skills/template-pitch-deck/` for
routing. Keep slide and layout logic in `src/`, keep scripts thin, and validate
rendered slides after any manuscript or theme change. Public-project checks use
the generated roster; do not commit private workspaces or credentials.
