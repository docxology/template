"""hermes — LLM-backed FEP theorem explainer for fep_lean.

Sends each FEP topic through a structured system+user prompt pair to an LLM
(via OpenRouter or Anthropic APIs) to produce:
  - A human-readable explanation of the proof strategy
  - A refined Lean 4 theorem sketch
  - Raw reasoning text (for reasoning models like DeepSeek-R1)

Uses only standard-library HTTP (``urllib.request``) so no extra dependencies
beyond the ones already in the project environment. On failure of the primary
model, the implementation may advance along ``fallback_models`` from settings
or ``_FREE_MODEL_CHAIN``. Transient transport failures (chunked ``IncompleteRead``,
dropped connections, ``URLError``) are retried with backoff (see
``HERMES_NETWORK_MAX_RETRIES``); HTTP **429** is retried on the **same** model up
to ``HERMES_429_MAX_RETRIES`` before advancing to the next model in the chain.

Public API:
    HermesConfig               — configuration dataclass (from settings.yaml)
    HermesExplainer(config)    — main explainer class
    .explain_topic(topic)      → HermesResult
    HermesResult               — result dataclass

Configuration priority (highest → lowest):
    1. Environment variables (OPENROUTER_API_KEY, ANTHROPIC_API_KEY, HERMES_MODEL,
       HERMES_429_MAX_RETRIES, HERMES_NETWORK_MAX_RETRIES, HERMES_MAX_MODEL_ATTEMPTS, …)
    2. config/settings.yaml  hermes: block
    3. Built-in defaults

Supported API backends:
    - OpenRouter  (base_url = https://openrouter.ai/api/v1)
    - Anthropic (via OpenRouter proxy or direct; native Messages API not implemented)
    - Any OpenAI-compatible endpoint (base_url = YOUR_URL)
"""

from __future__ import annotations

import http.client
import json
import logging
import os
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from catalogue.topics import TopicEntry

log = logging.getLogger(__name__)

# ── System prompt ─────────────────────────────────────────────────────────────

_FEP_SYSTEM_PROMPT = """\
You are Hermes, an expert in the Free Energy Principle (FEP), Active Inference, \
Bayesian Mechanics, Information Geometry, and Thermodynamics.  You are also a \
skilled formal mathematics assistant specialising in Lean 4 and Mathlib4.

Your task is to help formalize FEP theorems in Lean 4.  When given a theorem:
1. Explain the mathematical content and proof strategy clearly in 2–4 sentences.
2. Provide a refined Lean 4 theorem sketch that:
   - Uses real Mathlib4 declarations (MeasureTheory, Probability, Analysis).
   - Names hypotheses explicitly (e.g. `hac : q ≪ p`).
   - Uses `sorry` only for genuinely open sub-goals, not as a blanket placeholder.
   - Is syntactically correct Lean 4 (namespace, `open` statements, correct types).
3. If the original sketch is already good, improve the hypothesis names and inline
   documentation only.

⚠ CRITICAL PRESERVATION RULES — violating these causes compilation failures:
A. COPY ALL `import Mathlib.*` lines from the original sketch VERBATIM to the very
   top of your refined sketch (before `namespace`).  Do NOT drop or replace any import.
B. PRESERVE the `namespace FEPxxx ... end FEPxxx` wrapper exactly.
C. If the original proof tactic uses explicit hint lists such as
   `nlinarith [sq_nonneg x, mul_nonneg h1 h2]` or `simp [lemma1, lemma2]`,
   KEEP those hint lists exactly — do not remove hints or simplify to bare `nlinarith`/`simp`.
D. If the original sketch contains NO `sorry`, DO NOT introduce sorry.  Only add
   `-- [proof strategy: ...]` comments and improve hypothesis names; leave proof
   steps unchanged.

Schema for the refined sketch block (mandatory):
  ```lean
  import Mathlib.Xxx   -- copy ALL original imports here first
  namespace FEPxxx     -- preserve namespace from original
  -- [proof strategy: one line]
  theorem <name> ... : <statement> := by
    <tactic proof — preserve hint lists>
  end FEPxxx
  ```

Be concise.  Prioritise correctness over completeness.  Use Mathlib4 lemma names \
when you know them.  Do not hallucinate non-existent Mathlib lemmas.
"""

# ── Defaults & fallback model chain ──────────────────────────────────────────

_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
_DEFAULT_MODEL = "moonshotai/kimi-k2.6"

# Fallback chain — tried in order if the primary model fails. Ordered to keep
# wall-clock latency low: instruct/non-reasoning models first (fast TTFT),
# heavier reasoning models last. Updated 2026-04 after observing 10-minute
# stalls on GLM-5.1 with empty content (the wall-clock-timeout fix in
# ``_make_request`` will now abandon the request and advance the chain).
_FREE_MODEL_CHAIN = [
    "moonshotai/kimi-k2.6",
    "moonshotai/kimi-k2-thinking",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "z-ai/glm-5.1",
    "openai/gpt-oss-120b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "arcee-ai/trinity-large-preview:free",
]

def _env_positive_int(name: str) -> int | None:
    """Parse ``name`` as a positive int, or return ``None`` if unset/invalid."""
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    try:
        n = int(raw, 10)
        return n if n >= 1 else None
    except ValueError:
        return None


def _hermes_429_max_retries() -> int:
    """Retries after 429 before trying the next model (default 2 → up to 3 HTTP attempts)."""
    raw = os.environ.get("HERMES_429_MAX_RETRIES", "").strip()
    if not raw:
        return 2
    try:
        n = int(raw, 10)
        return max(0, min(n, 10))
    except ValueError:
        return 2


def _hermes_network_max_retries() -> int:
    """Retries after transient transport errors (IncompleteRead, URLError, etc.)."""
    raw = os.environ.get("HERMES_NETWORK_MAX_RETRIES", "").strip()
    if not raw:
        return 2
    try:
        n = int(raw, 10)
        return max(0, min(n, 10))
    except ValueError:
        return 2


# Models that return a `reasoning` field (extended thinking) and therefore
# need the larger ``reasoning_max_tokens`` / ``reasoning_timeout_s`` budgets so
# the trace does not consume the full token allowance before any ``content``
# is emitted. GLM-5.1 was observed returning empty ``content`` under the
# standard 16K / 150 s budget; promoting it here lets the trace finish.
_REASONING_MODELS = {
    "z-ai/glm-5.1",
    "moonshotai/kimi-k2.6",  # confirmed via live ping 2026-04-20: emits reasoning_tokens
    "moonshotai/kimi-k2.5",
    "moonshotai/kimi-k2-thinking",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "deepseek/deepseek-r1",
    "deepseek/deepseek-r1:free",
    "deepseek/deepseek-r1-0528",
    "openai/o1",
    "openai/o3",
}


@dataclass
class HermesConfig:
    """Configuration for the Hermes LLM explainer.

    All fields can be set from environment variables (see docstring priority order).
    Use ``HermesConfig.from_settings(project_root)`` to load from ``config/settings.yaml``.
    """

    model: str = _DEFAULT_MODEL
    base_url: str = _DEFAULT_BASE_URL
    api_key: str = ""
    max_tokens: int = 16384
    timeout_s: int = 150
    reasoning_max_tokens: int = 65536
    reasoning_timeout_s: int = 300
    enabled: bool = True
    cache_ttl_hours: float = 24.0
    # Ordered list of model slugs to try when the primary model fails with 429
    # or transient errors (OpenRouter only; Anthropic base_url ignores this).
    # Empty list ⇒ use the built-in ``_FREE_MODEL_CHAIN`` default.
    fallback_models: list[str] = field(default_factory=list)
    # Shared by all HermesExplainer instances using this config (prefetch worker + main).
    _enabled_lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)
    # Extra OpenRouter headers
    http_referer: str = "https://github.com/docxology/template"
    x_title: str = "FEP-Lean Formalization"

    @classmethod
    def _load_gauss_dotenv(cls) -> None:
        """Load ``~/.gauss/.env`` into ``os.environ`` if it exists.

        The OpenGauss CLI stores API keys in ``~/.gauss/.env`` (or ``$GAUSS_HOME/.env``).
        Standard Python ``os.environ`` does NOT automatically source shell dotenv
        files, so this method reads the file and injects any ``KEY=VALUE`` pairs
        that are not already present in the environment.

        Parsing is intentionally simple (no shell expansion, no multiline values)
        because the file format is ``KEY=VALUE`` with optional quoting.
        """
        gauss_home = os.environ.get("GAUSS_HOME", str(Path.home() / ".gauss"))
        dotenv_path = Path(gauss_home).expanduser() / ".env"
        if not dotenv_path.is_file():
            return
        try:
            for line in dotenv_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = value
                    log.debug("Loaded %s from %s", key, dotenv_path)
        except OSError as exc:
            log.warning("Could not read %s: %s", dotenv_path, exc)

    @classmethod
    def from_settings(
        cls, project_root: Path | str | None = None, *, settings_path: Path | None = None
    ) -> "HermesConfig":
        """Load config from ``config/settings.yaml``, then apply env overrides.

        Resolution order (highest → lowest):
          1. Explicit ``HERMES_*`` process env vars (project-scoped overrides)
             — ``HERMES_MODEL``, ``HERMES_API_BASE``
          2. ``config/settings.yaml``  ``hermes:`` block (committed project config)
          3. Shared gauss-level fallback env vars (``GAUSS_DEFAULT_MODEL``,
             ``OPENAI_BASE_URL``) — may come from the shell or ``~/.gauss/.env``
          4. Built-in defaults

        API keys (``OPENROUTER_API_KEY``, ``ANTHROPIC_API_KEY``,
        ``OPENAI_API_KEY``) follow the env-first convention and may be
        sourced from the shell OR ``~/.gauss/.env``; the ``hermes.api_key``
        yaml field is the lowest-priority fallback.

        After resolving the API key, the method validates that the key
        matches the configured ``base_url`` (e.g. an ``sk-ant-`` key must not
        be sent to OpenRouter, and an ``sk-or-`` key must not be sent to
        Anthropic).  A mismatch is logged as an error and Hermes is disabled.
        """
        # ── Step 0: hydrate environment from ~/.gauss/.env ────────────────
        cls._load_gauss_dotenv()

        # ── Step 1: load settings.yaml ────────────────────────────────────
        cfg: dict[str, Any] = {}
        if settings_path is None and project_root is not None:
            settings_path = Path(project_root) / "config" / "settings.yaml"
        if settings_path and settings_path.is_file():
            try:
                import yaml  # available via PyYAML in project deps
                raw = yaml.safe_load(settings_path.read_text(encoding="utf-8")) or {}
                cfg = raw.get("hermes", {})
            except Exception as exc:
                log.warning("Could not load settings.yaml: %s", exc)

        raw_fallbacks = cfg.get("fallback_models") or []
        fallbacks = [str(m).strip() for m in raw_fallbacks if str(m).strip()]

        inst = cls(
            model=cfg.get("model") or _DEFAULT_MODEL,
            base_url=cfg.get("base_url") or _DEFAULT_BASE_URL,
            max_tokens=int(cfg.get("max_tokens", 16384)),
            timeout_s=int(cfg.get("timeout_s", 150)),
            reasoning_max_tokens=int(cfg.get("reasoning_max_tokens", 65536)),
            reasoning_timeout_s=int(cfg.get("reasoning_timeout_s", 300)),
            enabled=bool(cfg.get("enabled", True)),
            cache_ttl_hours=float(cfg.get("cache_ttl_hours", 24.0)),
            fallback_models=fallbacks,
        )

        # ── Step 2: apply env overrides ───────────────────────────────────
        # Explicit HERMES_* vars win over yaml; shared gauss-level fallbacks
        # (GAUSS_DEFAULT_MODEL / OPENAI_BASE_URL) only apply when neither an
        # explicit override nor a yaml value is present.
        if os.environ.get("HERMES_MODEL"):
            inst.model = os.environ["HERMES_MODEL"]
        elif not cfg.get("model") and os.environ.get("GAUSS_DEFAULT_MODEL"):
            inst.model = os.environ["GAUSS_DEFAULT_MODEL"]

        if os.environ.get("HERMES_API_BASE"):
            inst.base_url = os.environ["HERMES_API_BASE"]
        elif not cfg.get("base_url") and os.environ.get("OPENAI_BASE_URL"):
            inst.base_url = os.environ["OPENAI_BASE_URL"]

        # ── Step 3: resolve API key with provenance logging ───────────────
        key_source = "none"
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        if api_key:
            key_source = "OPENROUTER_API_KEY"
        if not api_key:
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if api_key:
                key_source = "ANTHROPIC_API_KEY"
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if api_key:
                key_source = "OPENAI_API_KEY"
        if not api_key:
            api_key = cfg.get("api_key", "")
            if api_key:
                key_source = "settings.yaml"
        inst.api_key = api_key.strip().strip("'\"") if api_key else ""

        if inst.api_key:
            log.info(
                "Hermes API key resolved from %s (prefix=%s…)",
                key_source,
                inst.api_key[:12],
            )

        # ── Step 4: validate key ↔ endpoint affinity ──────────────────────
        if "api.anthropic.com" in inst.base_url:
            inst.base_url = "https://api.anthropic.com/v1"

        if inst.api_key and inst.enabled:
            is_openrouter = "openrouter.ai" in inst.base_url
            is_anthropic_url = "api.anthropic.com" in inst.base_url

            if is_openrouter and inst.api_key.startswith("sk-ant-"):
                log.error(
                    "API key mismatch: Anthropic key (sk-ant-…) sent to OpenRouter. "
                    "Set OPENROUTER_API_KEY or check ~/.gauss/.env. Disabling Hermes."
                )
                inst.enabled = False
            elif is_anthropic_url and inst.api_key.startswith("sk-or-"):
                log.error(
                    "API key mismatch: OpenRouter key (sk-or-…) sent to Anthropic. "
                    "Check your HERMES_API_BASE or ANTHROPIC_API_KEY. Disabling Hermes."
                )
                inst.enabled = False

        return inst

    def is_reasoning_model(self) -> bool:
        """Return True for models that expose a ``reasoning`` response field."""
        return self.model in _REASONING_MODELS

    def effective_max_tokens(self) -> int:
        """Return model-appropriate max_tokens (larger for reasoning models)."""
        return self.reasoning_max_tokens if self.is_reasoning_model() else self.max_tokens

    def effective_timeout(self) -> int:
        """Return model-appropriate timeout (longer for reasoning models)."""
        return self.reasoning_timeout_s if self.is_reasoning_model() else self.timeout_s


@dataclass
class HermesResult:
    """Result of one Hermes LLM call, including refined sketch and metadata."""
    success: bool
    model_used: str
    explanation: str = ""
    refined_lean_sketch: str = ""
    reasoning: str = ""  # from <think> / reasoning field
    tokens_used: int = 0
    duration_s: float = 0.0
    error: str = ""
    topic_id: str = ""
    cache_hit: bool = False

    def as_dict(self) -> dict[str, Any]:
        """Return serializable dict, truncating long reasoning for storage."""
        return {
            "success": self.success,
            "model_used": self.model_used,
            "explanation": self.explanation,
            "refined_lean_sketch": self.refined_lean_sketch,
            "reasoning": self.reasoning[:2000] if self.reasoning else "",
            "tokens_used": self.tokens_used,
            "duration_s": round(self.duration_s, 3),
            "error": self.error,
            "topic_id": self.topic_id,
            "cache_hit": self.cache_hit,
        }


class HermesExplainer:
    """LLM-backed explainer for FEP/Active Inference theorems.

    Sends a 2-message prompt (system + user) to a chat completions endpoint:
      [0] system — FEP domain expert + Lean 4 / Mathlib4 specialist persona
      [1] user   — NL statement, area context, current Lean sketch, refinement request

    The response is parsed into an explanation (plain text) and a refined
    Lean 4 sketch (extracted from the first fenced ``lean`` code block).

    When the primary model fails (4xx/5xx or transient error), the client tries
    models from ``fallback_models`` (from settings) or ``_FREE_MODEL_CHAIN``
    (when base_url contains openrouter.ai).

    Parameters
    ----------
    config:
        ``HermesConfig`` instance.  If not provided, loads from environment variables.
    """

    def __init__(self, config: HermesConfig | None = None) -> None:
        self._cfg = config or HermesConfig.from_settings()

    @property
    def is_live(self) -> bool:
        """Return True if enabled and an API key is present."""
        return bool(self._cfg.enabled and self._cfg.api_key)

    def preflight(self) -> bool:
        """Probe the API with a minimal request to surface credential failures fast.

        Sends one ``max_tokens=1`` completion against the configured primary
        model.  On any 4xx (except 429) the shared ``HermesConfig`` is flipped
        to ``enabled=False`` with an actionable log line, so a subsequent
        batch skips Hermes entirely instead of degrading mid-run.

        Returns
        -------
        bool
            ``True`` if the probe succeeded (or Hermes was already disabled /
            keyless — in which case there is nothing to probe).  ``False`` if
            the probe failed and Hermes was just disabled.

        Notes
        -----
        This is a real HTTP call (no mocks).  Safe to call repeatedly: if
        ``cfg.enabled`` is already ``False``, returns ``True`` immediately.
        """
        with self._cfg._enabled_lock:
            enabled = self._cfg.enabled
        if not enabled or not self._cfg.api_key:
            return True
        probe_messages = [
            {"role": "system", "content": "ping"},
            {"role": "user", "content": "ping"},
        ]
        original_max = self._cfg.max_tokens
        original_timeout = self._cfg.timeout_s
        self._cfg.max_tokens = 1
        self._cfg.timeout_s = min(30, original_timeout)
        try:
            self._call_api(probe_messages, self._cfg.model)
            log.info(
                "Hermes preflight OK (model=%s, base_url=%s)",
                self._cfg.model, self._cfg.base_url,
            )
            return True
        except HermesAPIError as exc:
            if exc.status_code and 400 <= exc.status_code < 500 and exc.status_code != 429:
                with self._cfg._enabled_lock:
                    self._cfg.enabled = False
                log.error(
                    "Hermes preflight FAILED (HTTP %d, model=%s). Disabling "
                    "Hermes for this run. Manage the OpenRouter key at "
                    "https://openrouter.ai/settings/keys, or set "
                    "HERMES_API_BASE=https://api.anthropic.com/v1 with "
                    "ANTHROPIC_API_KEY to fall back to Anthropic. See "
                    "projects/fep_lean/docs/troubleshooting.md#hermes-http-403.",
                    exc.status_code, self._cfg.model,
                )
                return False
            log.warning(
                "Hermes preflight returned %s — continuing (will retry per-topic).",
                exc,
            )
            return True
        except Exception as exc:
            log.warning("Hermes preflight transport error: %s — continuing.", exc)
            return True
        finally:
            self._cfg.max_tokens = original_max
            self._cfg.timeout_s = original_timeout

    # ── Public ────────────────────────────────────────────────────────────────

    def explain_topic(
        self, topic: "TopicEntry", *, preamble: str = ""
    ) -> HermesResult:
        """Explain ``topic`` and return a refined Lean 4 sketch.

        If ``HermesConfig.enabled`` is False, or if no API key is set, returns
        a disabled/skipped result immediately — no network calls.

        Parameters
        ----------
        preamble:
            Optional instruction prepended to the user message (used by
            ``GaussRunner`` to inject workflow-specific task directives such as
            "draft", "prove", or "review" before the theorem statement).
        """
        t0 = time.monotonic()
        with self._cfg._enabled_lock:
            enabled = self._cfg.enabled
        if not enabled:
            return HermesResult(
                success=False,
                model_used=self._cfg.model,
                error="hermes disabled in config",
                topic_id=topic.id,
            )
        if not self._cfg.api_key:
            return HermesResult(
                success=False,
                model_used=self._cfg.model,
                error="no API key (set OPENROUTER_API_KEY or ANTHROPIC_API_KEY)",
                topic_id=topic.id,
            )

        messages = self.build_messages(topic, preamble=preamble)
        models_to_try = self._build_model_chain()
        cap = _env_positive_int("HERMES_MAX_MODEL_ATTEMPTS")
        if cap is not None:
            models_to_try = models_to_try[:cap]

        last_err = ""
        last_model = models_to_try[0] if models_to_try else self._cfg.model
        for model in models_to_try:
            last_model = model
            try:
                raw, fatal_stop, fetch_err = self._try_fetch_raw(messages, model, topic.id)
                if fatal_stop:
                    if fetch_err:
                        last_err = fetch_err
                    break
                if raw is None:
                    if fetch_err:
                        last_err = fetch_err
                    continue

                elapsed = time.monotonic() - t0
                result = self._parse_response(raw, model, elapsed, topic.id)
                if result.success:
                    log.info("Hermes OK: %s via %s (%.2fs, %d tok)",
                             topic.id, model, elapsed, result.tokens_used)
                    return result
                last_err = result.error
                log.warning("Hermes model %s returned no content for %s: %s",
                            model, topic.id, last_err)
            except (
                json.JSONDecodeError,
                urllib.error.URLError,
                OSError,
                ValueError,
                TypeError,
                http.client.HTTPException,
            ) as exc:
                last_err = str(exc)
                log.warning("Hermes unexpected error (model=%s): %s", model, exc)

        elapsed = time.monotonic() - t0
        return HermesResult(
            success=False,
            model_used=last_model,
            error=last_err,
            duration_s=elapsed,
            topic_id=topic.id,
        )

    def _try_fetch_raw(
        self,
        messages: list[dict[str, str]],
        model: str,
        topic_id: str,
    ) -> tuple[dict[str, Any] | None, bool, str]:
        """Call chat completions with 429 and transient-transport backoff.

        Returns ``(body, fatal_stop, err_msg)``.
        """
        r429_max = _hermes_429_max_retries()
        net_max = _hermes_network_max_retries()
        max_attempts = max(r429_max, net_max) + 1
        last_err = ""
        for attempt in range(max_attempts):
            try:
                return (self._call_api(messages, model), False, "")
            except HermesAPIError as exc:
                last_err = str(exc)
                is_429 = exc.status_code == 429
                is_transient = getattr(exc, "transient", False)
                can_retry = (is_429 and attempt < r429_max) or (
                    is_transient and attempt < net_max
                )
                if can_retry:
                    delay = min(60.0, 2.0 ** (attempt + 1))
                    reason = "429 rate limit" if is_429 else "transient network"
                    log.warning(
                        "Hermes %s model=%s topic=%s — retry %d/%d after %.1fs",
                        reason,
                        model,
                        topic_id,
                        attempt + 1,
                        max_attempts,
                        delay,
                    )
                    time.sleep(delay)
                    continue
                log.warning("Hermes API error (model=%s, topic=%s): %s", model, topic_id, exc)
                if exc.status_code and 400 <= exc.status_code < 500 and exc.status_code != 429:
                    with self._cfg._enabled_lock:
                        self._cfg.enabled = False
                    log.error(
                        "Disabling Hermes for remainder of run (HTTP %d at topic=%s, "
                        "model=%s). Manage the OpenRouter key at "
                        "https://openrouter.ai/settings/keys, or set "
                        "HERMES_API_BASE=https://api.anthropic.com/v1 with "
                        "ANTHROPIC_API_KEY to fall back to Anthropic. See "
                        "projects/fep_lean/docs/troubleshooting.md#hermes-http-403.",
                        exc.status_code, topic_id, model,
                    )
                    return (None, True, last_err)
                return (None, False, last_err)
        return (None, False, last_err)

    # ── Internal ──────────────────────────────────────────────────────────────

    def build_messages(
        self, topic: "TopicEntry", *, preamble: str = ""
    ) -> list[dict[str, str]]:
        """Construct the conversation messages for the given topic.

        Parameters
        ----------
        preamble:
            Optional workflow directive prepended to the user message before
            the theorem statement (e.g. "TASK: Draft a new Lean 4 skeleton…").
        """
        lean_sketch = getattr(topic, "lean_sketch", "") or ""
        statement = getattr(topic, "nl", getattr(topic, "statement", topic.id))
        topic_name = getattr(topic, "title", getattr(topic, "name", topic.id))
        mathlib_imports = getattr(topic, "mathlib", getattr(topic, "mathlib_imports", "MeasureTheory"))
        area = getattr(topic, "area", "FEP")

        area_context = {
            "FEP": "Free Energy Principle and variational inference",
            "ActiveInference": "Active Inference and policy selection",
            "BayesianMechanics": "Bayesian Mechanics and Markov blankets",
            "InfoGeometry": "Information Geometry and statistical manifolds",
            "Thermodynamics": "non-equilibrium Thermodynamics and entropy",
        }.get(area, "mathematical physics")

        theorem_block = (
            f"**Theorem:** {topic_name}\n\n"
            f"**Area:** {area_context} ({area})\n\n"
            f"**Natural language statement:**\n{statement}\n\n"
            f"**Mathlib imports:** {mathlib_imports}\n\n"
            f"**Current Lean 4 sketch:**\n```lean\n{lean_sketch}\n```\n\n"
            "Please:\n"
            "1. In 2–3 sentences, explain the proof strategy and key mathematical insight.\n"
            "2. Provide a refined Lean 4 theorem sketch in a ```lean``` code block.\n"
            "   — Use real Mathlib4 declarations.\n"
            "   — Minimise uses of `sorry` to genuinely unproved sub-goals only.\n"
            "   — Include a one-line `-- [proof strategy: ...]` comment at the top."
        )
        user_prompt = f"{preamble}\n\n{theorem_block}" if preamble else theorem_block
        return [
            {"role": "system", "content": _FEP_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

    def _build_model_chain(self) -> list[str]:
        """Build the list of models to try, starting with the configured primary.

        OpenRouter-only: if ``HermesConfig.fallback_models`` is non-empty it
        takes precedence; otherwise the built-in ``_FREE_MODEL_CHAIN`` is used.
        Anthropic-direct endpoints ignore any chain (single model).
        """
        chain = [self._cfg.model]
        if "openrouter.ai" in self._cfg.base_url:
            fallbacks = self._cfg.fallback_models or _FREE_MODEL_CHAIN
            for m in fallbacks:
                if m not in chain:
                    chain.append(m)
        return chain

    def _call_api(
        self, messages: list[dict[str, str]], model: str
    ) -> dict[str, Any]:
        """Make the HTTP POST and return the parsed JSON response body."""
        url = self._cfg.base_url.rstrip("/") + "/chat/completions"
        is_reasoning = model in _REASONING_MODELS
        max_tokens = self._cfg.reasoning_max_tokens if is_reasoning else self._cfg.max_tokens
        timeout = self._cfg.reasoning_timeout_s if is_reasoning else self._cfg.timeout_s

        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.2,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._cfg.api_key}",
        }
        if "openrouter.ai" in self._cfg.base_url:
            headers["HTTP-Referer"] = self._cfg.http_referer
            headers["X-Title"] = self._cfg.x_title

        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        # ``urllib``'s ``timeout`` arg only bounds *individual* socket ops
        # (connect, each read), not total wall time. Slow streamed responses
        # can exceed it many-fold (observed: a 150 s timeout taking 10+ min on
        # GLM-5.1). Enforce a hard wall-clock deadline by running the blocking
        # urlopen+read in a worker thread and giving up at ``timeout`` seconds.
        result: dict[str, Any] = {}

        def _do_request() -> None:
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    result["raw"] = resp.read().decode("utf-8")
            except BaseException as inner_exc:  # re-raised on the calling thread
                result["exc"] = inner_exc

        worker = threading.Thread(target=_do_request, name="hermes-http", daemon=True)
        worker.start()
        worker.join(timeout=timeout)
        if worker.is_alive():
            raise HermesAPIError(
                f"Wall-clock timeout after {timeout}s "
                f"(model={model}); abandoning request and advancing chain.",
                status_code=None,
                transient=True,
            )
        if "exc" in result:
            try:
                raise result["exc"]
            except urllib.error.HTTPError as exc:
                body_str = exc.read().decode("utf-8", errors="replace")
                raise HermesAPIError(
                    f"HTTP {exc.code}: {exc.reason} — {body_str[:300]}",
                    status_code=exc.code,
                    transient=False,
                ) from exc
            except urllib.error.URLError as exc:
                raise HermesAPIError(
                    f"Network error: {exc.reason}",
                    status_code=None,
                    transient=True,
                ) from exc
            except http.client.HTTPException as exc:
                raise HermesAPIError(
                    f"HTTP transport error ({type(exc).__name__}): {exc}",
                    status_code=None,
                    transient=True,
                ) from exc
            except (TimeoutError, OSError) as exc:
                # Low-level socket/timeout failures not wrapped in URLError on some paths.
                raise HermesAPIError(
                    f"Connection error ({type(exc).__name__}): {exc}",
                    status_code=None,
                    transient=True,
                ) from exc
        return json.loads(result["raw"])

    def _parse_response(
        self,
        raw: dict[str, Any],
        model: str,
        elapsed: float,
        topic_id: str,
    ) -> HermesResult:
        """Extract explanation, refined sketch, and reasoning from API response."""
        choices = raw.get("choices", [])
        if not choices:
            return HermesResult(
                success=False, model_used=model, error="empty choices",
                duration_s=elapsed, topic_id=topic_id,
            )
        choice = choices[0]
        msg = choice.get("message", {})
        content = msg.get("content") or ""
        reasoning = msg.get("reasoning") or ""
        # Some models wrap reasoning in <think>...</think> inside content
        if "<think>" in content and "</think>" in content:
            tag_open_pos = content.index("<think>")
            think_start = tag_open_pos + len("<think>")
            think_end = content.index("</think>")
            reasoning = content[think_start:think_end].strip()
            content = (content[:tag_open_pos] + content[think_end + len("</think>"):]).strip()

        usage = raw.get("usage", {})
        tokens = usage.get("completion_tokens", 0) + usage.get("prompt_tokens", 0)

        # Extract the ```lean block
        refined_sketch = _extract_lean_block(content)
        # First non-code paragraph is the explanation
        explanation = _extract_explanation(content)

        return HermesResult(
            success=bool(content),
            model_used=model,
            explanation=explanation,
            refined_lean_sketch=refined_sketch,
            reasoning=reasoning,
            tokens_used=tokens,
            duration_s=elapsed,
            topic_id=topic_id,
        )


class HermesAPIError(Exception):
    """Raised for API/transport failures from :meth:`HermesExplainer._call_api`."""

    def __init__(
        self,
        msg: str,
        *,
        status_code: int | None = None,
        transient: bool = False,
    ) -> None:
        super().__init__(msg)
        self.status_code = status_code
        self.transient = transient


# ── Text extraction helpers ───────────────────────────────────────────────────

def _extract_lean_block(content: str) -> str:
    """Extract the first ```lean...``` fenced code block from the LLM response."""
    import re
    m = re.search(r"```lean\s*\n(.*?)```", content, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Fallback: plain ``` fence starting with a theorem keyword
    m2 = re.search(r"```\s*\n(theorem\s+.*?)```", content, re.DOTALL)
    if m2:
        return m2.group(1).strip()
    # Fallback: bare theorem text without any fence (LLM omitted markdown)
    m3 = re.search(r"((?:import\s+\S+\s*\n|open\s+\S+\s*\n)*theorem\s+\w[^\n]*(?:\n.*?)*?(?::=\s*\n?(?:\s+\S[^\n]*\n)+|:=\s*\S[^\n]*\n))", content, re.DOTALL)
    if m3:
        return m3.group(1).strip()
    return ""


def restore_lean_structure(refined: str, original: str) -> str:
    """Restore import lines and namespace wrapper stripped by the LLM.

    LLMs frequently drop ``import Mathlib.*`` lines and ``namespace FEPxxx``
    wrappers, and sometimes add extra theorems with non-existent API calls.
    When the sketch starts with ``import``, the verifier's ``_wrap_lean_code``
    skips its own preamble — so any stripped import means the needed Mathlib
    module is absent at compile time.

    Strategy:
    0. Garbage detection: if the refined output contains C++ ``//`` comments or
       has no ``theorem`` declarations, fall back to the original sketch.
    1. Collect import lines from original only (discard LLM-added imports —
       they are often invalid module paths like ``Mathlib.Data.Fin``).
    2. Strip all import lines from refined body.
    3. Restore import block with original imports only.
    4. Reconstruct: imports → blank → body.
    5. Restore namespace wrapper if stripped.
    6. Remove theorem blocks that Hermes added beyond the original set
       (prevents broken hallucinated theorems from poisoning compilation).
    """
    import re

    if not refined or not original:
        return refined

    orig_lines = original.splitlines()
    refined_lines = refined.splitlines()

    # ── 0. Garbage detection: fall back to original when output is invalid ───
    # C++ `//` comments are not valid Lean4 syntax — indicates LLM hallucination
    _cpp_comment_re = re.compile(r"^\s*//(?!/)")  # // but not ///
    cpp_lines = [l for l in refined_lines if _cpp_comment_re.match(l)]
    has_theorem = bool(re.search(r"\btheorem[^\S\n]+\w+", refined))
    if cpp_lines or not has_theorem:
        # Conservative by design: safety (no broken hallucinations) over recall (LLM improvements).
        log.warning(
            "restore_lean_structure: refined sketch appears invalid "
            "(cpp_comment_lines=%d, has_theorem=%s); falling back to original",
            len(cpp_lines),
            has_theorem,
        )
        return original

    # ── 1. Collect import lines from original ONLY ───────────────────────────
    orig_imports: list[str] = [l for l in orig_lines if l.strip().startswith("import ")]

    # ── 2. Strip all import lines from refined body ──────────────────────────
    non_import_body: list[str] = [l for l in refined_lines if not l.strip().startswith("import ")]

    # ── 3. Build import block: originals only (no LLM additions) ─────────────
    merged_imports = orig_imports  # exact original order, no dedup needed

    # ── 4. Reconstruct: imports → blank → body ───────────────────────────────
    body = "\n".join(non_import_body).strip()

    if merged_imports:
        result = "\n".join(merged_imports) + "\n\n" + body
    else:
        result = refined  # no imports in either; leave unchanged

    # ── 5. Restore namespace wrapper if stripped ─────────────────────────────
    ns_match = re.search(r"^namespace\s+(\w+)", original, re.MULTILINE)
    if ns_match:
        ns_name = ns_match.group(1)
        if f"namespace {ns_name}" not in result:
            if merged_imports:
                import_block = "\n".join(merged_imports)
                after_imports = result[len(import_block):].strip()
                result = import_block + f"\n\nnamespace {ns_name}\n\n" + after_imports + f"\n\nend {ns_name}"
            else:
                result = f"namespace {ns_name}\n\n" + result.strip() + f"\n\nend {ns_name}"

    # ── 5.5. Restore `open` statements from original that Hermes dropped ────────
    # Only restore opens that appear in the original; never add Hermes-invented ones.
    orig_open_stmts = [l.rstrip() for l in orig_lines if l.strip().startswith("open ")]
    if orig_open_stmts:
        result_lines = result.splitlines()
        existing_opens: set[str] = {l.strip() for l in result_lines if l.strip().startswith("open ")}
        missing_opens = [l for l in orig_open_stmts if l.strip() not in existing_opens]
        if missing_opens:
            # Insert them right after the namespace declaration line (or after imports)
            ns_idx = next(
                (i for i, l in enumerate(result_lines) if re.match(r"^\s*namespace\s+\w+", l)),
                None,
            )
            if ns_idx is not None:
                result_lines[ns_idx + 1 : ns_idx + 1] = [""] + missing_opens
            else:
                # No namespace line — prepend after imports
                last_import = max(
                    (i for i, l in enumerate(result_lines) if l.strip().startswith("import ")),
                    default=-1,
                )
                insert_at = last_import + 1
                result_lines[insert_at:insert_at] = [""] + missing_opens
            result = "\n".join(result_lines)

    # ── 6. Remove theorem blocks Hermes added beyond the original set ─────────
    orig_theorem_names: set[str] = set(re.findall(r"\btheorem[^\S\n]+(\w+)", original))
    if orig_theorem_names:
        result = _strip_extra_theorems(result, orig_theorem_names)

    # ── 7. Completeness check: fall back if original theorems are absent ─────
    # After stripping extra theorems, the result must still contain at least
    # one of the original theorem names.  If ALL were stripped (e.g. Hermes
    # replaced everything with `theorem a : True := trivial`), the sketch is
    # useless — return the original.
    if orig_theorem_names:
        result_theorem_names: set[str] = set(re.findall(r"\btheorem[^\S\n]+(\w+)", result))
        if not result_theorem_names.intersection(orig_theorem_names):
            log.warning(
                "restore_lean_structure: no original theorem names survive after strip "
                "(original=%s, found=%s); falling back to original",
                orig_theorem_names,
                result_theorem_names,
            )
            return original

    return result


def _strip_extra_theorems(sketch: str, allowed_names: set[str]) -> str:
    """Remove theorem declarations from *sketch* whose names are not in *allowed_names*.

    Uses a line-by-line state machine to identify theorem blocks (including
    preceding doc/inline comments) and drops blocks whose ``theorem <name>``
    does not appear in the original sketch.  Non-theorem content (``variable``,
    ``abbrev``, ``open``, ``section`` etc.) is always preserved.
    """
    import re

    lines = sketch.splitlines()
    output: list[str] = []

    # Buffer for a pending theorem block (doc comments + theorem lines)
    pending: list[str] = []
    in_theorem = False
    current_name: str = ""

    _theorem_re = re.compile(r"^\s*theorem\s+(\w+)")
    _doc_re = re.compile(r"^\s*/--")
    _inline_comment_re = re.compile(r"^\s*--")

    def flush_pending(keep: bool) -> None:
        if keep:
            output.extend(pending)
        pending.clear()

    for line in lines:
        tm = _theorem_re.match(line)
        if tm:
            # Flush previous theorem block (if any)
            if in_theorem:
                flush_pending(current_name in allowed_names)
            # Start new block: include any buffered doc/comment lines
            current_name = tm.group(1)
            in_theorem = True
            pending.append(line)
        elif in_theorem:
            # Determine if this line ends the theorem block:
            # A blank line followed by a new theorem or end-of-namespace signals end.
            # For simplicity, keep accumulating until we hit the next `theorem` or `end`.
            if line.strip().startswith("end ") and not line.strip().startswith("end --"):
                # End of namespace: flush current theorem, then add the end line
                flush_pending(current_name in allowed_names)
                in_theorem = False
                output.append(line)
            else:
                pending.append(line)
        else:
            # Outside a theorem block: check if this is a leading doc comment for
            # the NEXT theorem (buffer it) or just regular non-theorem content.
            # We only buffer doc-comment lines; everything else goes straight to output.
            if _doc_re.match(line) or _inline_comment_re.match(line):
                pending.append(line)
            else:
                # Flush any buffered comments as non-theorem content
                flush_pending(True)
                output.append(line)

    # Flush final pending block
    if in_theorem:
        flush_pending(current_name in allowed_names)
    else:
        flush_pending(True)

    return "\n".join(output)


def _extract_explanation(content: str) -> str:
    """Extract the plain-text explanation (before any code block)."""
    import re
    # Remove code fences
    no_code = re.sub(r"```.*?```", "", content, flags=re.DOTALL).strip()
    # Take the first 3 non-empty paragraphs
    paras = [p.strip() for p in no_code.split("\n\n") if p.strip()]
    # Skip lines that are just headers
    paras = [p for p in paras if not p.startswith("#")]
    return "\n\n".join(paras[:3]) if paras else no_code[:800]
