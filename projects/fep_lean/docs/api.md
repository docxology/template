# Public API Reference — fep_lean

**Version**: v0.7.0 | **Status**: Active | **Last Updated**: April 2026

This document is auto-verified against the live `src/` modules. All signatures are extracted via `inspect` from the running code.

---

## catalogue/topics.py

### `TopicEntry` (dataclass)

```python
@dataclass
class TopicEntry:
    id: str              # "fep-001" format
    title: str           # Short human title
    area: str            # One of 5 valid areas
    mathlib: str         # Comma-separated Mathlib4 module names
    mathlib_status: str  # "real" | "partial" | "aspirational" (loader default if omitted: "partial"; all 50 shipped rows are "real" in v0.7.0)
    nl: str              # Natural language mathematical statement
    lean_sketch: str     # Lean4 theorem sketch
```

The shipped **`config/topics.yaml`** tags all rows **`real`** today; counts in `summary()` reflect whatever is in YAML.

### `FEPTopicCatalogue`

```python
class FEPTopicCatalogue:
    topics: list[TopicEntry]   # All 50 loaded topics (property)

    @classmethod
    def from_yaml(cls, path: Path | None = None) -> "FEPTopicCatalogue"
    # path defaults to {project_root}/config/topics.yaml when None

    def summary(self) -> dict
    # Returns {total_topics: int, areas: {area: count}, maturity: {status: count},
    #          area_maturity: {area: {status: count}}}
```

**Catalogue size**: 50 topics (verified), 5 areas.

---

## gauss/client.py

### `OpenGaussClient`

```python
class OpenGaussClient:
    def __init__(self, gauss_home: str | Path | None = None) -> None
    # Context manager: __enter__ / __exit__ / .close()

    # Session management
    def create_session(
        self, topic_id: str, area: str, lean_sketch_original: str = '', *,
        source: str = 'fep_lean'
    ) -> str                                           # Returns session_id

    def update_session(
        self, session_id: str, turn_index: int, role: str, content: str, tokens: int = 0
    ) -> None

    def close_session(
        self, session_id: str, status: str = 'success',
        hermes_success: bool = False, lean_compiles: int = -1
    ) -> None

    def set_refined_sketch(self, session_id: str, refined_sketch: str) -> None

    # Export
    def export_session(self, session_id: str) -> dict      # KeyError if not found
    def export_all_sessions(self, source: str = 'fep_lean') -> list[dict]
    def write_artifact(self, session_id: str, payload: dict, *, label: str = 'result') -> Path
    def write_bulk_jsonl(self, sessions: list[dict], out_path: Path) -> Path

    # Hermes result cache (keyed by SHA-256 of topic_id:lean_sketch:model:stage)
    def get_cached_hermes(self, cache_key: str) -> dict | None
    # Returns stored HermesResult.as_dict() or None on miss

    def set_cached_hermes(
        self,
        cache_key: str,
        topic_id: str,
        stage: str,
        model: str,
        result_json: str,
        lean_sketch_hash: str,
    ) -> None
    # Insert or replace a cache entry; commits immediately

    def prune_hermes_cache(self, ttl_hours: float = 24.0) -> int
    # Delete entries older than ttl_hours; returns row count deleted

    # Logging + stats
    def log_event(self, event: str, *, session_id: str | None = None, **kwargs) -> None
    def get_stats(self) -> dict   # {total_sessions, lean_compiles, hermes_ok, db_path, ...}
```

**Storage layout**:

```text
{GAUSS_HOME}/
├── fep_lean_state.db            ← SQLite (sessions, turns, artifacts, logs, hermes_cache tables)
├── fep_artifacts/
│   ├── session_{id}_{label}.json  ← Per-session artifact
│   └── sessions_fep_lean_*.jsonl  ← Bulk JSONL export
└── fep_logs/
    └── operations.jsonl           ← Structured event log
```

**`hermes_cache` table** (7 columns):

| Column | Type | Description |
|--------|------|-------------|
| `cache_key` | TEXT PK | SHA-256(`topic_id:lean_sketch:model:stage`) |
| `topic_id` | TEXT | e.g. `fep-001` |
| `stage` | TEXT | `verify` / `draft` / `prove` / `review` |
| `model` | TEXT | Model ID used for this result |
| `hermes_result` | TEXT | JSON-serialised `HermesResult.as_dict()` |
| `lean_sketch_hash` | TEXT | SHA-256 of lean sketch at cache time |
| `created_at` | REAL | Unix timestamp (used for TTL pruning) |

### `SessionRecord` (dataclass)

```python
@dataclass
class SessionRecord:
    session_id: str
    topic_id: str
    area: str
    lean_sketch: str
    refined_sketch: str | None
    status: str              # 'open' | 'success' | 'failed' | 'error' | 'skipped'
    hermes_success: bool
    lean_compiles: int       # -1 = not attempted; 0 = fail; 1 = ok
    source: str
    created_at: float        # Unix timestamp
    closed_at: float | None
    duration_s: float | None
    turns: list[dict]        # [{turn_index, role, content, tokens}]
```

---

## verification/preflight.py

Optional toolchain checks before full pipeline runs: `gauss doctor` (when required), `lake`/`lean` availability and versions, and Mathlib `.olean` build status via `LeanVerifier.check_mathlib_built`.

### `run_preflight`

```python
def run_preflight(*, require_gauss: bool | None = None) -> int
# Returns 0 if all checks pass, 1 otherwise. Prints human-readable lines to stdout.
```

### CLI (`pyproject` entry point)

Console script **`fep-lean-preflight`** → `verification.preflight:main`.

```bash
uv run fep-lean-preflight
uv run fep-lean-preflight --require-gauss   # fail if gauss doctor fails
```

---

## verification/lean_verifier.py

### `VerifyResult` (dataclass)

```python
@dataclass
class VerifyResult:
    topic_id: str
    compiles: bool       # True if lake env lean exits 0
    has_sorry: bool      # True if sketch contains 'sorry'
    errors: list[str]    # Compiler error lines
    warnings: list[str]  # Compiler warning lines
    stdout: str          # Combined stdout+stderr (truncated to ~8000 chars)
    stderr: str          # Raw stderr (populated on timeout)
    duration_s: float
    lean_version: str    # From 'lean --version' (cached)
    lean_file: Path | None
    skip_reason: str     # Non-empty when verification skipped (lake missing, etc.)

    @property
    def status(self) -> str:
        # 'compiles_clean' | 'compiles_with_sorry' | 'compile_error' | 'skipped(...)'
    def as_dict(self) -> dict
```

### `LeanVerifier`

```python
class LeanVerifier:
    def __init__(
        self,
        lean_dir: Path | str | None = None,       # defaults to {project_root}/lean/
        project_root: Path | str | None = None,   # defaults to cwd
    ) -> None

    def check_lake_available(self) -> bool
    def lean_version(self) -> str | None          # Cached; elan-aware

    def verify_sketch(self, topic_id: str, lean_code: str) -> VerifyResult
    # Writes temp file to lean/FepSketches/, runs lake env lean, removes file

    def verify_batch(self, items: list[tuple[str, str]]) -> list[VerifyResult]
    # Executed sequentially [(topic_id, lean_code), ...] (max_workers=1)
    # Explicitly avoids MacOS ELAN proxy sandbox deadlock contention caused by parallel execution

    def _wrap_lean_code(self, lean_code: str) -> str
    # Prepends Mathlib import preamble if missing
```

**Environment variables** (all read at `LeanVerifier` import / call time):

- `FEP_LEAN_VERIFY_TIMEOUT` — per-sketch timeout in seconds (default: 300)
- `FEP_LEAN_LAKE_EXE` — explicit path to the `lake` binary (bypasses PATH + elan proxy)
- `FEP_LEAN_LEAN_EXE` — explicit path to the `lean` binary (bypasses PATH + elan proxy)

---

## llm/hermes.py

### `HermesConfig` (dataclass)

```python
@dataclass
class HermesConfig:
    model: str = 'moonshotai/kimi-k2.6'
    base_url: str = 'https://openrouter.ai/api/v1'
    api_key: str = ''
    max_tokens: int = 16384
    timeout_s: int = 150
    reasoning_max_tokens: int = 65536   # For reasoning models (DeepSeek-R1, o1)
    reasoning_timeout_s: int = 300
    enabled: bool = True
    fallback_models: list[str] = field(default_factory=list)  # Overrides _FREE_MODEL_CHAIN when non-empty
    http_referer: str = 'https://github.com/docxology/template'
    x_title: str = 'FEP-Lean Formalization'
    cache_ttl_hours: float = 24.0       # SQLite hermes_cache TTL; 0 disables caching

    @classmethod
    def from_settings(cls, project_root: Path | str | None = None,
                      *, settings_path: Path | None = None) -> HermesConfig

    def is_reasoning_model(self) -> bool      # True for Nemotron, DeepSeek-R1, o1, o3
    def effective_max_tokens(self) -> int     # reasoning_max_tokens if reasoning model
    def effective_timeout(self) -> int        # reasoning_timeout_s if reasoning model
```

**Model fallback chain** (`_FREE_MODEL_CHAIN` in `src/llm/hermes.py`; tried in order, primary first):

```
1. moonshotai/kimi-k2.6                     (primary, Moonshot Kimi K2.6, 262K ctx; member of _REASONING_MODELS)
2. moonshotai/kimi-k2-thinking              (extended-thinking K2 variant)
3. qwen/qwen3-next-80b-a3b-instruct:free    (fast instruct fallback)
4. z-ai/glm-5.1                             (ZhipuAI GLM-5.1, demoted from primary; in _REASONING_MODELS)
5. openai/gpt-oss-120b:free                 (OpenAI 120B distilled)
6. nvidia/nemotron-3-super-120b-a12b:free   (reasoning model fallback; in _REASONING_MODELS)
7. nousresearch/hermes-3-llama-3.1-405b:free (NL-strong, 8 req/min limit)
8. arcee-ai/trinity-large-preview:free      (reasoning-focused)
```

**Config priority** (highest → lowest):
```
OPENROUTER_API_KEY / ANTHROPIC_API_KEY / OPENAI_API_KEY (env)
HERMES_MODEL / HERMES_API_BASE / GAUSS_DEFAULT_MODEL (env)
config/settings.yaml  hermes: block
Code defaults
```

### `HermesResult` (dataclass)

```python
@dataclass
class HermesResult:
    success: bool
    model_used: str
    explanation: str = ''         # Plain-text FEP explanation
    refined_lean_sketch: str = '' # Extracted ```lean block
    reasoning: str = ''           # From <think>...</think> or reasoning field
    tokens_used: int = 0
    duration_s: float = 0.0
    error: str = ''               # Empty on success
    topic_id: str = ''
    cache_hit: bool = False       # True when result was served from SQLite cache (no network call)

    def as_dict(self) -> dict
```

### `HermesExplainer`

```python
class HermesExplainer:
    def __init__(self, config: HermesConfig | None = None) -> None

    def explain_topic(self, topic: TopicEntry, *, preamble: str = "") -> HermesResult
    # Returns immediately (no network) if enabled=False or api_key=''
    # ``preamble`` is prepended to the system message (used by GaussRunner workflow stages)
    # Uses _try_fetch_raw: HTTP 429 → exponential backoff retries (HERMES_429_MAX_RETRIES)
    # then next model; other 4xx (not 429) may disable Hermes for the remainder of the run

    def _try_fetch_raw(
        self, messages: list[dict[str, str]], model: str, topic_id: str
    ) -> tuple[dict[str, Any] | None, bool, str]
    # Returns (json_body, fatal_stop_outer_loop, last_error_message)
```

Optional env caps (see [`hermes.md`](hermes.md), [`configuration.md`](configuration.md)): `HERMES_MAX_MODEL_ATTEMPTS` limits how many models from the chain are tried per topic.

### `HermesAPIError`

```python
class HermesAPIError(Exception):
    """Raised by ``HermesExplainer._call_api`` for API/transport failures."""
    status_code: int | None
    transient: bool        # True for retryable transport errors (IncompleteRead, URLError)
```

---

## gauss/runner.py

### `TopicRunResult` (dataclass)

```python
@dataclass
class TopicRunResult:
    topic_id: str
    session_id: str
    success: bool
    status: str
    hermes_success: bool = False
    lean_compiles: bool = False
    lean_has_sorry: bool = False
    duration_s: float = 0.0
    error: str = ''
    workflow: str = 'verify'                        # Stage used: 'verify'|'draft'|'prove'|'review'
    stage_results: list[dict[str, Any]] = field(default_factory=list)
    # Each entry: {stage, hermes_success, model_used, tokens_used, duration_s, cache_hit}
    # Hermes-derived fields surfaced for downstream reporters (Reporter._gen_topic_md
    # and output.manuscript.build_manuscript_vars consume these without re-reading SQLite):
    explanation: str = ''
    refined_lean_sketch: str = ''
    tokens_used: int = 0
    hermes_model: str = ''
    cache_hit: bool = False
    hermes_lean_compiles: bool = False              # Hermes-refined sketch compiled directly
                                                    # (False → either Hermes failed OR baseline-fallback path was used)

    def as_dict(self) -> dict
```

`workflow` is always `"verify"` unless the caller passes an explicit `workflow=` kwarg to `run_topic()`.
`stage_results` is populated for non-verify workflows and for the review second-pass when
`workflow="review"` and the first compilation succeeds.

### `GaussRunner`

```python
class GaussRunner:
    def __init__(
        self,
        lean_verifier: LeanVerifier,
        hermes: HermesExplainer,
        client: OpenGaussClient,
        project_root: Path,
    ) -> None

    def run_topic(self, topic: TopicEntry, *, workflow: str = 'verify') -> TopicRunResult
    # 4-step: create_session → Hermes explain (with preamble) → Lean verify → close + artifact
    # workflow: one of 'verify' | 'draft' | 'prove' | 'review'
    # Non-verify workflows require FEP_LEAN_GAUSS_WORKFLOWS=1; silently downgrade to 'verify' otherwise.
    # 'review' stage runs a second Hermes call after compilation succeeds (commentary, no lean block).

    def run_topics_batch(
        self,
        topics: list[TopicEntry],
        *,
        max_topics: int | None = None,
        workflow: str = 'verify',
    ) -> list[TopicRunResult]

    @classmethod
    def create_default(
        cls, project_root: Path, *, require_cli: bool = False
    ) -> "GaussRunner"
    # Convenience constructor using defaults; raises RuntimeError if require_cli and gauss missing
```

**Workflow preambles** (`_WORKFLOW_PREAMBLES`): each workflow injects a task directive as a system-message prefix before the Hermes call:

| Workflow | Directive injected |
|----------|--------------------|
| `verify` | *(empty — vanilla explain)* |
| `draft`  | Draft a new Lean 4 theorem skeleton; use `sorry` freely |
| `prove`  | Attempt a full proof; fill sorry-holes with Mathlib4 tactics |
| `review` | Review compiled sketch; no new `\`\`\`lean` block |

**Hermes result cache**: before every Hermes call, `GaussRunner` checks
`OpenGaussClient.get_cached_hermes()` using a SHA-256 key of `topic_id:lean_sketch:model:stage`.
On a cache hit the network call is skipped; `HermesResult.cache_hit` is set `True`.
Cache TTL is `HermesConfig.cache_ttl_hours` (default 24 h); entries are pruned via
`OpenGaussClient.prune_hermes_cache()`.

---

## pipeline/core.py

### `StepResult` (dataclass)

```python
@dataclass
class StepResult:
    name: str
    status: str             # 'ok' | 'error' | 'skipped' | 'warning' (required)
    message: str = ""
    duration_s: float = 0.0
    payload: Any = None
    error: str | None = None

    def as_dict(self) -> dict
```

### `PipelineResult` (dataclass)

```python
from dataclasses import dataclass, field

@dataclass
class PipelineResult:
    status: str
    total_duration: float = 0.0
    run_dir: str = ""
    stages: list[StepResult] = field(default_factory=list)
    lean_stats: dict[str, Any] = field(default_factory=dict)
    _topic_results: list[Any] = field(default_factory=list)

    # Properties: steps (alias of stages), topic_results, hermes_count,
    # lean_verified_count, lean_compile_ok, topics_ok, duration_s, stats

    def as_dict(self) -> dict
```

### `FEPPipeline`

```python
class FEPPipeline:
    def __init__(self, project_root: Path) -> None

    def run(
        self,
        topic_filter: list[str] | None = None,
        area_filter: str | None = None,
    ) -> PipelineResult
    # Stages: Load Catalogue, Environment Validation, Gauss Sessions (if workflows on),
    # Manuscript Artifacts. Reporting is done in pipeline/orchestrator.run_pipeline.
```

After filters, the catalogue batch may be capped by env **`FEP_LEAN_MAX_TOPICS`** (positive integer); see `_max_topics_from_env()` in `pipeline/core.py`.

---

## output/manuscript.py

Manuscript injection for Pandoc: builds YAML consumed as `manuscript/manuscript_vars.yaml` and regenerates the single-appendix Lean catalogue markdown.

### `build_manuscript_vars`

```python
def build_manuscript_vars(
    catalogue: FEPTopicCatalogue,
    project_root: Path,
) -> dict[str, Any]:
    """Return a dict suitable for YAML serialisation (not written to disk)."""
```

Top-level keys include:

- `total_topics`, `total_areas`, `topic_ids`
- `topics`: per-id dicts with `area`, `mathlib_status`, `maturity`, `maturity_icon`, `nl_statement`, `lean_chars`, `lean_sketch`
- `areas`: **nested** for template substitution — each area maps to `{"count": int}` so `{{areas.FEP.count}}` resolves in the manuscript
- `maturity`: counts by status (`real`, `partial`, `aspirational`)
- `verify`: aggregate block from the latest `output/reports/run_*/verification_manifest.json` if present (`manifest_present`, `compiles_true`, …)
- `date`: UTC `YYYY-MM-DD`

Contrast with `FEPTopicCatalogue.summary()`: that API returns **flat** `areas: {area_name: count}`. Only `build_manuscript_vars` / `write_manuscript_vars` nest counts under `.count` for Pandoc.

### `write_manuscript_vars`

```python
def write_manuscript_vars(
    project_root: Path,
    catalogue: FEPTopicCatalogue | None = None,
) -> Path:
    """Write ``manuscript/manuscript_vars.yaml`` (auto-generated header)."""
```

### `build_full_topic_lean_catalogue_markdown` / `write_full_topic_lean_catalogue_markdown`

```python
def build_full_topic_lean_catalogue_markdown(catalogue: FEPTopicCatalogue) -> str

def write_full_topic_lean_catalogue_markdown(
    project_root: Path,
    catalogue: FEPTopicCatalogue | None = None,
) -> Path:
    """Write ``manuscript/09z_appendix_b_lean_catalogue.md`` (gitignored)."""
```

---

## output/reporter.py

### `ReportPaths` (dataclass)

```python
@dataclass
class ReportPaths:
    index_md: Path       # Master pipeline report
    summary_json: Path   # Machine-readable PipelineResult
    hermes_md: Path      # Per-topic Hermes explanation table
    lean_md: Path        # Per-topic Lean compilation status
    validation_md: Path  # 13-check environment validation (see verification/environment.py:328-343)
    topics_dir: Path     # Per-topic individual reports

    def all_paths(self) -> list[Path]
    def as_dict(self) -> dict[str, str]
```

### `Reporter`

```python
class Reporter:
    def __init__(self, project_root: Path, run_id: str | None = None) -> None
    # run_id defaults to strftime("%Y%m%d_%H%M%S") when None

    def generate(
        self,
        catalogue: FEPTopicCatalogue,
        result: PipelineResult,
    ) -> ReportPaths
```

Output layout (filenames on disk; `ReportPaths` fields point to these paths):

```text
output/reports/run_YYYYMMDD_HHMMSS/
├── index.md                  ← Pipeline summary + stage table
├── summary.json              ← Full PipelineResult as JSON
├── hermes_report.md          ← Per-topic Hermes status + explanations
├── lean_report.md            ← Per-topic Lean compilation status
├── validation_report.md      ← 13 environment checks
└── topics/                   ← Per-topic `fep-NNN.md`
```

Bulk session JSONL under `{GAUSS_HOME}/fep_artifacts/` is from `OpenGaussClient`, not this run tree.

---

## pipeline/orchestrator.py

### `run_pipeline()`

```python
def run_pipeline(
    *,
    interactive: bool = False,
    area_filter: str | None = None,
    topic_filter: list[str] | None = None,
) -> PipelineResult:
    """Run ``FEPPipeline`` then ``Reporter.generate`` when catalogue loads."""
```

### `run_single_topic()`

```python
def run_single_topic(topic_id: str, *, interactive: bool = False) -> dict[str, Any]:
    """Run ``FEPPipeline`` for one id; returns a topic dict (no full Reporter bundle)."""
```

---

## Navigation

- [verification/preflight.py](#verificationpreflightpy) (toolchain CLI)
- [← Development](development.md)
- [Architecture →](architecture.md)
- [← docs/README.md](README.md)
