# Bounded numeric proposal contract

`scripts/run_sia_loop.py --live-proposals` is an opt-in local capability with
an explicit Ollama model and immutable local Docker image ID. Fixture replay
remains the default. `--live-sia` is the unchanged reference subprocess lane.

The new lane has one task: change the fixed classifier's finite `THRESHOLD`
literal within `[0, 1]`. The model returns exactly a numeric threshold and a
bounded rationale. It cannot provide code, paths, tool calls, or executable
patches. The trusted controller materializes the sole literal change and its
unified diff. This is initial numeric proposal capability, with no claim that
it generalizes to arbitrary code generation or reliable improvement.

The baseline and at most two proposals use the fixed public selection dataset.
Only strict public accuracy improvement keeps a candidate in the disposable
sandbox. A frozen synthetic holdout with distinct IDs is evaluated once after
selection. The model receives neither held-out cases nor held-out scores.
The controller parses exactly the dataset bytes bound by its receipt hashes.
Reference source and both datasets are rechecked before each proposal, before
held-out evaluation, and when the run finishes. The shipped public baseline is
already perfect, so a distinct numeric proposal can correctly be rejected.

Each target runs in Docker with `--pull=never`, `--network none`, read-only
root, dropped capabilities, `no-new-privileges`, user `65534:65534`, one CPU,
128 MiB memory, 32 processes, and a 16 MiB no-exec temporary filesystem.
Only the fixed target and controller heartbeat, unlabelled feature files, and disposable prediction
directory are mounted. No Docker socket, home directory, host credential,
or project tree is mounted. The container must run Python 3.14/3.15. The
shared process-group supervisor bounds each target to 60 seconds. A trusted
container PID 1 independently enforces that deadline and exits if its read-only
controller heartbeat stops advancing for two seconds. This also terminates
the container namespace when the complete host controller/client tree is killed.
The exact container name and limits are recorded before launch; normal cleanup
must establish that container's absence. The complete run has a 600-second
deadline, with 30 seconds reserved for container cleanup. Model requests are supervised
to a total 60 seconds and allow only an HTTP loopback origin, without
credentials, redirects, or proxy inheritance. Responses are bounded to 64 KiB
and must identify a completed, nonempty generation by the selected model.
The installed model's unique SHA-256 digest is checked before and after every
generation and must stay identical across proposals.

The fresh run directory under ignored `output/` retains:

| Artifact | Meaning |
| --- | --- |
| `live_proposal_receipt.json` | Overall passed, failed, or blocked status, limits, input hashes, selection, scores, and final rollback verification |
| `gen_1/execution.json` and predictions | Actual baseline Docker execution and independently scored predictions |
| `gen_N/model_request.json`, `model_response.json`, `model_execution.json` | Exact public request, actual provider response, and supervised request outcome |
| `gen_N/model_identity.json` | Selected installed model digest before and after generation; identity drift fails acceptance |
| `gen_N/proposal.diff`, `target_agent.py`, `rollback_target.py` | Exact candidate source diff, candidate bytes, and prior source bytes |
| `gen_N/approval_receipt.json` | Pending proposal approval, diff/rollback hashes, and verified sandbox rollback; source application is forbidden |
| `gen_N/execution.json` and predictions | Actual candidate Docker execution and independently scored predictions |
| `heldout/execution.json` and predictions | Final held-out execution after public-only selection |
| `selected_target.py` | Selected disposable source; the workspace is restored to baseline afterward |

Missing Docker, daemon, pinned image, or selected local model is blocked with
exit 75. There is no host subprocess or deterministic proposal fallback for
this lane. Malformed proposals, incomplete predictions, execution faults,
input drift, failed cleanup, and failed rollback stop acceptance and preserve
available diagnostics. No distinct proposed mutation is also incomplete
acceptance. The command never applies the selected code to production source;
owner approval and an additional application mechanism would be required.

Tests using a controlled loopback server verify transport custody and failure
behavior. Real Docker tests verify container execution, restrictions, and
cleanup, including abrupt whole-controller-tree interruption. A controlled provider is not evidence that an Ollama model ran.
Actual model acceptance requires a separate successful run against the selected
local Ollama service, together with its request/response, Docker, scoring,
diff, and rollback receipts. Paid providers are outside this lane.
