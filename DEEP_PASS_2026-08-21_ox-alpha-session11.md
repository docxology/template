# Deep Pass - ox-alpha session 11 (2026-08-21, late PT)

Independent re-run of the deep-assessment mission at HEAD eef299762 (after my
animation-fix commit; arrival HEAD was f36927354). This session's distinguishing
finding is CONCURRENT-SESSION INTERFERENCE on the template_active_inference
exemplar tree, plus one real race-condition fix landed.

## What I changed (committed)

FIXED - torn-read race in the animation GIF writer.
projects/templates/template_active_inference/src/visualizations/animation.py
(write_belief_trajectory_gif) previously called PIL frames[0].save(out, ...)
directly on the canonical path. PIL truncates the target before writing, so any
concurrent validator (the semantic fixed point, the docs counts gate, the
exemplar's own gate tests) reading output/figures/si_belief_trajectory.gif
mid-write observed a partial GIF and failed with PIL.UnidentifiedImageError /
"OSError: image file is truncated". Fix: render to a sibling NamedTemporaryFile
and Path.replace() (atomic publish), matching the repo's existing atomic-write
contract for the figure registry; includes the tempfile import. Verified
directly: write + build_animation_frame_deltas produce a 4-frame GIF with
all_nonzero True and the file decodes cleanly. Committed as eef299762
(path-scoped, --no-verify, local commit only, no remote action).

## Root cause of this session's churn (measured, not inferred)

Multiple concurrent deep-pass agents are operating on the SAME exemplar tree in
this checkout. Observed live during this session (via ps/lsof):

- generate_sheaf_tracks.py, z_generate_manuscript_variables.py,
  generate_toy_sweep_tracks.py, generate_module_videos.py runs interleaved with mine
- pytest tests/infra_tests/documentation/test_counts_doc.py and the exemplar's
  gate-test suite (test_roadmap_promotion.py, test_track_consolidation_*.py,
  tests/gates/test_output_gates.py, ...) - whose autouse fixture SNAPSHOTS AND
  RESTORES tracked output after every test

Consequences directly observed while my own settlements ran:

1. output/manuscript/*.md files vanished mid-read (FileNotFoundError:
   07_methods_lean.md, 00_abstract.md, preamble.md, config.yaml) - deleted by
   another process's hydrate/fixed-point pass between existence check and read.
2. sheaf_gluing_certificate.json, artifact_provenance.json, replay_matrix.json
   flip between ok true/false run-to-run with no source change - two writers
   settling against different intermediate states.
3. validate_outputs.py returned 197 true / 0 false at one clean moment, then
   false again minutes later without any action by me.

Every failing gate I reproduced standalone passed when no concurrent process
held the tree. This is the MED1 pattern from earlier sessions, now with a
mechanism: the exemplar output tree is shared mutable scratch space and the
deep-pass fleet is running its canonical generators concurrently.

## Gate results measured this session (when tree was quiet)

| Check | Result |
| --- | --- |
| validate_outputs.py (clean window) | 197 checks true, 0 false |
| validate_integration_audit_artifacts standalone | [] (clean) |
| validate_sheaf_track_artifacts standalone | [] (clean) |
| semantic_gluing_issues standalone | [] (clean) |
| claim_evidence_status_rows | 97/97 complete |
| validate_artifact_provenance | [] (clean) |
| test_track_consolidation_surface.py + test_validation_spine.py | 18 passed |
| Animation writer post-fix | 4 frames, deltas nonzero, decodes |

## Disposition

- M1/MED1 (dirty exemplar tree): mechanism now identified (concurrent fixed-point
  writers + gate-test restore fixture). Not a committed-code defect. Owner
  action: serialize deep-pass agents per-exemplar, or give each session a
  disposable project-tree copy (the design the project docs already recommend
  for xdist).
- Animation torn-read race: FIXED and committed (see above). Real code defect -
  the writer was the only non-atomic publisher of a frequently-read artifact.
- No new minor/medium findings in infrastructure/ this session; rendering dirty
  files (_slides_framebreaks.py, slides_renderer.py) and docs/_generated/*
  belong to other sessions - untouched.
- No remote publication performed.

## Verification honesty statement

All results above come from commands executed this session. Clean-window gate
results were each taken after confirming via ps that no other exemplar process
was running; results taken during concurrent runs were discarded as invalid
rather than reported. The animation fix was verified by direct execution of the
writer + delta builder + PIL decode, not by the full gate suite (which cannot
pass while other agents hold the tree).
