# Source — template_sia

Project-specific SIA wiring: loop configuration and execution adapter, reports,
manuscript tokens, and fixture replay payloads.

`src/loop.py` delegates the Meta → Target → Feedback state machine to
`infrastructure.sia`, then writes the exemplar's reports, variables, figures,
and artifact manifest. CLI scripts import this project API.
