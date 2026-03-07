# External Blind Review Session

Session id: ext_20260307_005819_131f40ee
Session token: ef3ff67f786c9423602dd1f82387a14c
Blind packet: /Users/4d/Documents/GitHub/template/.desloppify/review_packet_blind.json
Template output: /Users/4d/Documents/GitHub/template/.desloppify/external_review_sessions/ext_20260307_005819_131f40ee/review_result.template.json
Claude launch prompt: /Users/4d/Documents/GitHub/template/.desloppify/external_review_sessions/ext_20260307_005819_131f40ee/claude_launch_prompt.md
Expected reviewer output: /Users/4d/Documents/GitHub/template/.desloppify/external_review_sessions/ext_20260307_005819_131f40ee/review_result.json

Happy path:
1. Open the Claude launch prompt file and paste it into a context-isolated subagent task.
2. Reviewer writes JSON output to the expected reviewer output path.
3. Submit with the printed --external-submit command.

Reviewer output requirements:
1. Return JSON with top-level keys: session, assessments, findings.
2. session.id must be `ext_20260307_005819_131f40ee`.
3. session.token must be `ef3ff67f786c9423602dd1f82387a14c`.
4. Include findings with required schema fields (dimension/identifier/summary/related_files/evidence/suggestion/confidence).
5. Use the blind packet only (no score targets or prior context).
