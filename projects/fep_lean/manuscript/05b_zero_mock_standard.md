## The Importance of the Zero-Mock Standard {#sec:the_importance_of_the_zero_mock_standard}

Throughout the development of the pipeline, testing frameworks typically defaulted to mocked text returns to avoid the overhead of spinning up the Lean toolchain. This led to hallucinated validation graphs that shattered upon compilation. The zero-mock standard is our structural response: **every success claim in the pipeline is underwritten by a real computation, a real file, or a real network round-trip** — never by a stubbed return value.

Native checks use the committed Lake workspace under [`lean/`](../lean/): run `lake exe cache get` and `lake build` there, or **`scripts/_maint_bootstrap_lean_toolchain.sh`** (also invoked from repo **`scripts/00_setup_environment.py --project fep_lean`** when Mathlib is missing), so Mathlib `.olean` files exist. Zero-mock compilation means stderr/stdout come from the compiler; summaries belong in run artifacts (and optional math-inc **`gauss`** workflows), not in mocked return values.

### Philosophy: Why No Mocks Anywhere {#sec:philosophy_no_mocks}

The project's test suite contains **zero uses** of `MagicMock`, `mocker.patch`, `unittest.mock.patch`, or any other mocking primitive. This is enforced by the repository-wide `infrastructure/validation/no_mock_enforcer.py` scanner, which is run as part of the infrastructure test gate (§\ref{sec:native_lean_4_compilation_and_zero_mock_verification}). The rationale is both epistemic and engineering:

- **Epistemic**: A mocked test demonstrates only that the code under test calls the mock as expected — it does not demonstrate that the mocked dependency exists, behaves as documented, or continues to behave that way across upstream versions. In a formalisation pipeline, a mocked Lean compiler is an oxymoron: the whole point is that the compiler's type-checker is the *ground truth*.
- **Engineering**: Mocks drift. The moment an upstream API changes its response shape and the mock does not, the mocked test is a false positive. Over years, this accumulates into a test suite that passes reliably but verifies nothing.
- **Scientific**: The zero-mock standard maps directly onto the scientific reproducibility norm that claims must be underwritten by artefacts a peer can inspect, not by declarations the author makes.

The zero-mock standard has implications beyond this project. Any AI-assisted formalisation pipeline that mocks the compiler is fundamentally unreliable — a mocked success proves nothing about the mathematical validity of the generated code. We advocate zero-mock as a minimum baseline for all LLM-ITP (Interactive Theorem Prover) integration research: claims of "formal verification" must be authenticated by active compilation passes over the compiler's type theory, not by declarations that the author intends such passes to succeed.

The motivation is concrete and drawn from recurring failure modes observed during this pipeline's development: **mock-based CI can pass green while production integration fails**, because the mock reflects the test author's *model* of the dependency rather than the dependency itself. When the dependency is an LLM API whose JSON shape drifts across provider updates, or a Lean toolchain whose tactic set changes between minor versions, the mock-based green build is not merely uninformative — it actively misleads reviewers and authors. Replacing mocks with real round-trips (against real Lean, real HTTP, real SQLite, real matplotlib) pushes every such drift into the CI signal where it belongs.

### The Four Zero-Mock Axes {#sec:four_zero_mock_axes}

Zero-mock applies uniformly across four concrete axes in this pipeline:

1. **SQLite persistence** — sessions and turns are written to a real on-disk SQLite database under a `tmp_path` fixture. Tests run the actual schema migrations; no cursor is mocked.
2. **HTTP (OpenRouter)** — the Hermes client uses stdlib `urllib` against a real local `pytest-httpserver` (or, for live integration checks, the real OpenRouter endpoint). Tests that require a real key are **skipped gracefully when `OPENROUTER_API_KEY` is unset**, never mocked into a false pass.
3. **`lake env lean` compilation** — the verifier shells out to the real Lean 4 toolchain against the pinned Mathlib4 cache; there is no stub compiler. Tests that depend on the toolchain **skip gracefully when `lake` is unavailable** rather than substituting a canned success.
4. **Figures / matplotlib** — figure-producing tests render with the real matplotlib backend under `MPLBACKEND=Agg` (headless) and assert against the actual PNG/SVG on disk, not against a mocked `plt`.

Each axis has the same structure: a real artefact on disk or a real byte stream on a socket; a real computation that touches it; an explicit `skip` when the external prerequisite is unavailable; and no `MagicMock` anywhere in the code path.

### Applying Zero-Mock to Lean Verification {#sec:zero_mock_lean}

For Lean sketches specifically, zero-mock means:

- Every claim of "the sketch compiles" is the result of a *real* `lake env lean` invocation against the pinned toolchain. The verifier (`src/verification/lean_verifier.py`) writes a temporary `.lean` file, prepends the project preamble, and shells out to `lake env lean`; it captures stderr/stdout verbatim in memory. After a full pipeline run, **`Reporter`** aggregates outcomes into **`output/reports/run_*/verification_manifest.json`**, which feeds the `verify.*` fields in `manuscript_vars.yaml` (e.g., `verify.compiles_true`, `verify.failed_topic_ids`). As of the 2026-04-18 `scripts/03_lean_verify_only.py` sweep: `verify.compiles_true=50; verify.compiles_false=0; verify.verify_lean_ran=true`.
- There is no stub verifier. If `lake` is unavailable, the verifier raises, it does not silently succeed; callers can then explicitly opt into a *catalogue-only* mode (no verification claim) rather than receiving a false confirmation.
- The Mathlib `.olean` cache is a real on-disk artefact; if it is missing, the verifier's first error surfaces that fact, rather than masking it behind a pre-canned "compiler happy" response.

### Applying Zero-Mock to HTTP (OpenRouter) {#sec:zero_mock_http}

Hermes commentary is obtained via HTTP calls to OpenRouter using the `moonshotai/kimi-k2.6` primary model (with a 6-model fallback chain that retains `z-ai/glm-5.1` as a demoted entry). The test suite never monkey-patches `requests.post`. Instead, the integration tests use the `pytest-httpserver` fixture to spin up a **real local HTTP server** that speaks the OpenRouter wire protocol. For example:

```python
def test_hermes_streaming_parses_openrouter_chunks(httpserver):
    # Real local server replays a real OpenRouter response shape
    httpserver.expect_request("/chat/completions").respond_with_data(
        # Real SSE frames captured from a prior OpenRouter call
        "data: {\"choices\":[{\"delta\":{\"content\":\"Hello\"}}]}\n\n"
        "data: {\"choices\":[{\"delta\":{\"content\":\" world\"}}]}\n\n"
        "data: [DONE]\n\n",
        content_type="text/event-stream",
    )
    client = HermesClient(base_url=httpserver.url_for(""), api_key="test")
    out = client.complete_streaming(prompt="ping")
    assert out == "Hello world"  # Real parse of real bytes over real socket
```

The server is a real TCP listener on `127.0.0.1`; the client opens a real socket; the SSE parser sees real bytes. What changes between production and test is only *which host* is contacted, not *whether* bytes are actually exchanged.

### Applying Zero-Mock to Files and Databases {#sec:zero_mock_files}

File I/O uses `tmp_path` fixtures for real on-disk files. SQLite persistence (sessions, turns) uses a real SQLite file under `GAUSS_HOME`; tests construct a fresh temp path and run the actual schema migrations rather than mocking the DB cursor. PDF inputs in the validation test suite are generated on-the-fly with `reportlab` so that the validator exercises the real `pypdf`/`pdfplumber` parsing path, not a stubbed byte stream.

### Catalogue ↔ SKETCHES Agreement and Live Compilation {#sec:ssot_compile_tests}

Two project-level mechanisms encode the zero-mock standard at its most load-bearing point:

- **`test_catalogue_sketches_ssot.py`** checks that `config/topics.yaml` and the `SKETCHES` dictionary in `scripts/catalogue_sketches.py` are bit-for-bit consistent — a real YAML load against a real Python dict, with no mocked parsing. This guards against drift between the YAML single source of truth and the generator that emits it.
- **Per-row `lake env lean` compilation** is performed by `scripts/03_lean_verify_only.py` (logs only) and, when workflows are enabled, the **Gauss Sessions** stage (**`GaussRunner`** + **`LeanVerifier`**), which record per-topic exit code, error text, and `has_sorry` in the run bundle and in **`verification_manifest.json`**. The headline rate (**`{{compile_rate.total}}`**, see §`04e`) is compiled from that manifest; the `LeanVerifier` itself is exercised on representative sketches by `test_lean_verifier.py` (22 tests) and `test_lean_verifier_sad_paths.py` (15 tests).

Full-catalogue compile coverage is exercised via opt-in environments (CI / long jobs) and `scripts/03_lean_verify_only.py`, which writes per-topic outcomes to **`verification_manifest.json`**; the default pytest suite focuses on **`LeanVerifier`** behaviour and integration paths without an all-or-nothing gate that would blur environment failures with code defects. Per-row manifest entries remain the audit trail for headline **`{{compile_rate.total}}`**.

Both the SSOT test and the per-row verification honour the zero-mock axes: YAML is a real file, the SKETCHES module is really imported, and Lean really runs. They also honour a **`pytest-timeout` default of 900 seconds** (configured in `pyproject.toml` and overridable per test), so a wedged Lean subprocess fails loudly rather than blocking the CI queue indefinitely.

### Coverage Requirements and Observed Test Volume {#sec:coverage_requirements}

Zero-mock is paired with a strict *coverage floor*: **60% infrastructure coverage, 90% project coverage**, enforced in CI via `--cov-fail-under`. The two policies interlock:

- Without zero-mock, a high coverage number is meaningless — it counts lines executed against a mock.
- Without coverage floors, zero-mock is brittle — code that is never exercised is never verified.

Combined, they ensure that a green build represents code that (a) was actually executed end-to-end, (b) against real dependencies, and (c) at a density that would expose regressions.

**Observed status**: **{{tests.collected}} tests collected** under `tests/`, with project line coverage **≥89%** against the project gate (`pyproject.toml`'s `fail_under = 89`). Every one of those passes reflects a real round-trip against one of the four zero-mock axes above — there is no `MagicMock`, `mocker.patch`, or `unittest.mock.patch` in the test tree, as the `infrastructure/validation/no_mock_enforcer.py` scanner verifies on every CI run.

### A Worked Example: Real Numerical Computation {#sec:zero_mock_example}

The following test — drawn from the `fep-028` softmax catalogue row — illustrates zero-mock end-to-end. There is no mock; the test constructs real logits, computes a real softmax, and asserts real algebraic invariants that the Lean sketch also proves:

```python
import math
import pytest

from projects.fep_lean.src.catalogue import build_softmax_policy

def test_softmax_sums_to_one_and_is_nonneg():
    """Mirrors fep-028: compiler proves these; Python cross-checks numerically."""
    logits = [-2.0, 0.0, 1.5, 3.0]
    probs = build_softmax_policy(logits)

    # Non-negativity (Lean: fep028_softmax_nonneg)
    assert all(p >= 0.0 for p in probs)

    # Normalisation (Lean: fep028_softmax_probs_sum_one)
    assert math.isclose(sum(probs), 1.0, rel_tol=1e-12, abs_tol=1e-12)

    # Monotonicity in logits (Lean: fep028_softmax_monotone)
    sorted_by_logit = sorted(zip(logits, probs))
    probs_sorted = [p for _, p in sorted_by_logit]
    assert probs_sorted == sorted(probs_sorted)
```

Three features of this test are characteristic of the zero-mock standard. First, *every* value is computed, not asserted against a frozen expected dictionary. Second, the three assertions mirror three distinct Lean theorems from fep-028, giving a cross-language consistency check between the Python implementation and the Lean specification. Third, the test exhibits no `@patch`, no `Mock`, no side-effect stubs — if `build_softmax_policy` ever starts returning stubbed values, the test fails, which is the point.

## Bridging Natural Language and Axiomatic Truth {#sec:bridging_natural_language_and_axiomatic_truth}

The catalogue in `config/topics.yaml` and the narrative `docs/topics-reference.md` (pedagogical) provide a stepping stone between informal physics and type-checked specification. Placing a natural-language explanation (the Hermes commentary) directly adjacent to a catalogue `theorem` sketch compiled against Mathlib constraints forces a discipline that informal papers do not: every mathematical claim must be decomposed into its constituent type-level obligations. This structural discipline aligns with recent calls for precision in Active Inference formulation [@sajid2021active; @parr2022active] and answers criticisms that FEP derivations conflate distinct mathematical objects [@andrews2021math; @biehl2021critique].

The pedagogical value transcends verification: in general ITP pedagogy, a `sorry` in a partial proof pinpoints remaining obligations. **This repository's shipped 50-topic catalogue is `sorry`-free** under current policy (§\ref{sec:the_sorry_mechanism_and_formalization_maturity}); the contrast below illustrates how `sorry` would expose gaps in hypothetical extensions.

### The `sorry` as Pedagogical Device {#sec:the_sorry_as_pedagogical_device}

The `sorry` mechanism serves an unexpectedly valuable pedagogical role in FEP formalization. Consider the contrast:

- **Informal paper**: "By the non-negativity of KL divergence, we have $\FE \geq -\log p(s|m)$."
- **Lean 4 with `sorry`**: The proof requires establishing that `∫ x, rnDeriv q p x * Real.log (rnDeriv q p x) ∂p ≥ 0`, which decomposes into showing that `x * log(x) ≥ 0` for `x ≥ 0`—a specific analytical fact about the function $t \mapsto t \log t$.

The `sorry` exposes the *exact* gap: not a vague appeal to a known inequality, but a precise statement about a specific real-valued function. This precision is itself a contribution to FEP scholarship, independent of whether the gap is eventually filled. Under zero-mock there is no temptation to paper the gap over with a stub: the compiler flags the `sorry`, and the pipeline reports it faithfully rather than burying it in a mocked success.
