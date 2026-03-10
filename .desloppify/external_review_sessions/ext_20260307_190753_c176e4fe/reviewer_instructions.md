# External Blind Review Session

Session id: ext_20260307_190753_c176e4fe
Session token: 1050eaa8f8224fa590727bca05c843eb
Blind packet: /Users/4d/Documents/GitHub/template/.desloppify/review_packet_blind.json
Template output: /Users/4d/Documents/GitHub/template/.desloppify/external_review_sessions/ext_20260307_190753_c176e4fe/review_result.template.json
Claude launch prompt: /Users/4d/Documents/GitHub/template/.desloppify/external_review_sessions/ext_20260307_190753_c176e4fe/claude_launch_prompt.md
Expected reviewer output: /Users/4d/Documents/GitHub/template/.desloppify/external_review_sessions/ext_20260307_190753_c176e4fe/review_result.json

Happy path:
1. Open the Claude launch prompt file and paste it into a context-isolated subagent task.
2. Reviewer writes JSON output to the expected reviewer output path.
3. Submit with the printed --external-submit command.

Reviewer output requirements:
1. Return JSON with top-level keys: session, assessments, findings.
2. session.id must be `ext_20260307_190753_c176e4fe`.
3. session.token must be `1050eaa8f8224fa590727bca05c843eb`.
4. Include findings with required schema fields (dimension/identifier/summary/related_files/evidence/suggestion/confidence).
5. Use the blind packet only (no score targets or prior context).
