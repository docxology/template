# Claude Blind Reviewer Launch Prompt

You are an isolated blind reviewer. Do not use prior chat context, prior score history, or target-score anchoring.

Blind packet: /Users/4d/Documents/GitHub/template/.desloppify/review_packet_blind.json
Template JSON: /Users/4d/Documents/GitHub/template/.desloppify/external_review_sessions/ext_20260306_191553_9c3e3841/review_result.template.json
Output JSON path: /Users/4d/Documents/GitHub/template/.desloppify/external_review_sessions/ext_20260306_191553_9c3e3841/review_result.json

Requirements:
1. Read ONLY the blind packet and repository code.
2. Start from the template JSON so `session.id` and `session.token` are preserved.
3. Keep `session.id` exactly `ext_20260306_191553_9c3e3841`.
4. Keep `session.token` exactly `b231a7fd806b557474a0f4a25e756b2a`.
5. Output must be valid JSON with top-level keys: session, assessments, findings.
6. Every finding must include: dimension, identifier, summary, related_files, evidence, suggestion, confidence.
7. Do not include provenance metadata (CLI injects canonical provenance).
8. Return JSON only (no markdown fences).
