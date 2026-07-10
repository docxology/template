# Security Guide

This template went through a dedicated security-hardening round (round 2's
`/security-review` pass) plus two further adversarial rounds that found
numeric-boundary gaps of the identical shape. This guide is the real story
of each fix, with file:line citations, and a checklist for a forker adding
a new validated field.

## Checksum-pinned `tla2tools.jar` download (ISC-69)

**The finding.** An earlier revision fetched `tla2tools.jar` from a moving
`latest` release tag with zero integrity verification before invoking
`java -jar` against it — a real supply-chain risk (a compromised or
silently-republished release asset would run unverified).

**The fix**, in
[`scripts/check_formal_specs.sh`](../scripts/check_formal_specs.sh):

- The URL is pinned to a specific, dated tag —
  `https://github.com/tlaplus/tlaplus/releases/download/v1.8.0/tla2tools.jar`
  — never `latest`.
- A hardcoded SHA-256
  (`TLA_JAR_SHA256="9e27b5e19a69ae1f56aabf8403a6ed5598dbfa6e638908e5278ac39736c1543d"`)
  is verified via `shasum -a 256 -c -` **every run**, whether the jar was
  just fetched or already cached — so a stale/corrupted/tampered cache is
  caught too, not just a fresh download.
- On mismatch: `rm -f "${TLA_JAR}"` then `status=1` — the untrusted file is
  never left sitting around for a later invocation to reuse, and the
  script fails loudly rather than silently proceeding.
- The jar itself is gitignored, not committed — a 2.2MB compiled binary
  has no place in a strongly-typed *source* template (a separate, earlier
  Forge finding; see `ISA.md`'s Changelog).

## Construction-time SQL-identifier validation (ISC-70)

**The finding.** Every query in
[`storage/db.py`](../src/template_formal/storage/db.py) interpolates
`self.table.name` directly into a raw SQL string — SQLite's `?`
parameter-binding covers *values*, never *identifiers*. Without a
construction-time guard, a `TableSchema`/`Column` built with a name like
`"x; DROP TABLE observations; --"` could reach that interpolation.

**The fix**, in
[`storage/schema.py`](../src/template_formal/storage/schema.py):

- `SQL_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")`
  (line 30) is the only shape a table/column name may take.
- `validate_sql_identifier(name, *, what)` (line 45) raises `ValueError`
  if `name` doesn't match — called from both `Column.__post_init__`
  (line 87-88) and `TableSchema.__post_init__` (line 113-114), so a
  malformed identifier can never become a `Column`/`TableSchema` instance
  in the first place.
- **Defense-in-depth, not redundant belt-and-suspenders**: every method in
  `storage/db.py` (`select_all`, `select_by`, `insert`) re-validates
  `self.table.name` against the same pattern immediately before building
  its SQL string (e.g. `db.py` line 169, 188, 227), *in addition to* the
  construction-time guard — because a frozen dataclass's fields can still
  be overwritten via `object.__setattr__` after construction, and the
  query builder should not assume a `TableSchema` reaching it was
  necessarily built through its own constructor.
- The `column`/`values` keys accepted by `select_by`/`insert` are checked
  for membership against `self.table.column_names()` first (already
  construction-time-validated names), before either method builds a SQL
  string from them.

A real test proves a SQL-injection-shaped identifier raises `ValueError`
before it can reach any raw-SQL f-string (`tests/storage/test_storage_schema.py`).
One documented, non-exploitable residual: `TableSchema.to_ddl`'s DDL
generation has no guard against a *hypothetical* `object.__setattr__`
tampering scenario after construction — left as an informational note
(`ISA.md`'s round-2 audit), since no real code path in this template
constructs a `TableSchema` from untrusted input.

## Numeric-boundary consistency: `BeliefState.variance` and `ColonyTrialConfig.preference_variance` (ISC-81/84)

**The finding, round 3.** A FirstPrinciples pass and an independent
security-deep pass **converged on the same defect without coordinating**:
[`agent/agent.py`](../src/template_formal/agent/agent.py)'s `BeliefState`
(the numeric field the manuscript's headline Active-Inference decision
loop is built on) had zero validation on `variance`.
`BeliefState(mean=0.0, variance=0.0)` constructed silently and only failed
three calls later, deep inside `gaussian_kl_divergence`/
`gaussian_differential_entropy`, with an undocumented
`ZeroDivisionError`/`ValueError: math domain error` — far from the actual
misconfiguration site.

**The fix**, `agent/agent.py` lines 150-152:

```python
def __post_init__(self) -> None:
    if not math.isfinite(self.variance) or self.variance <= 0.0:
        raise ValueError(f"BeliefState.variance must be finite and > 0.0, got {self.variance!r}")
```

This mirrors the same `__post_init__` pattern already established for
`storage/schema.py`'s `Column`/`TableSchema` (SQL identifiers) and
`storage/transaction.py`'s isolation-level `Literal` check — an
unvalidated numeric/string field silently accepting a nonsensical value is
the identical defect *class*, just recurring at a new call site each time.

**The second-order finding, round 3 continued (ISC-84).** Once
`BeliefState.variance` was fixed, a *third* Forge cross-vendor audit of
that very fix caught a residual: `colony/experiment.py`'s
`ColonyTrialConfig.preference_variance` (line 128-129 in its
`__post_init__`) still used its original `>= 0.0` guard, accepting `0.0` —
but its sole consumer, `BeliefState.__post_init__`, now rejected
`variance <= 0.0`. A config with `preference_variance=0.0` therefore still
constructed silently and only failed one call later inside
`run_colony_trial`'s `BeliefState` construction — **the identical "guard
accepts a value its downstream consumer rejects" pattern, recreated one
boundary removed.** Fixed by tightening the config-level guard to match
exactly:

```python
if self.preference_variance <= 0.0:
    raise ValueError(f"preference_variance must be > 0.0 (matches BeliefState), got {self.preference_variance}")
```

**The generalizable lesson** (`ISA.md`'s round-3 Decisions): a
config-level validation fix does not automatically propagate to every
other constructor of the same underlying value type. Closing a gap at one
call site is not the same as closing the gap for the type itself — when
two independent guards validate the same value at different points in a
call chain (a config field, and the type it ultimately constructs),
tightening one without checking the other reintroduces the same defect
class at the remaining, looser boundary. Checking that all guards on a
given value *agree* is a distinct verification step from checking that any
one guard is individually correct.

## Checklist before adding a new validated numeric/string field

Mirror the `__post_init__` pattern that now appears at every one of these
call sites (`Column`/`TableSchema` in `storage/schema.py`,
`IsolationLevel` in `storage/db.py`/`storage/transaction.py`,
`ColonyTrialConfig` in `colony/experiment.py`, `BeliefState` in
`agent/agent.py`):

1. **Validate in `__post_init__`, not at first use.** The failure must
   surface at construction, not three calls later inside unrelated
   arithmetic — that "far from the misconfiguration" failure mode is
   exactly what every fix above closes.
2. **State the exact domain in the docstring** (`[0.0, 1.0]` for a
   fraction, `> 0.0` for a variance, a specific `Literal` for an
   enumerated string) — the validation should be a direct transcription of
   that stated domain, not a looser approximation of it.
3. **Check every other constructor of the same underlying value.** If this
   field's value flows into another type's constructor downstream (as
   `ColonyTrialConfig.preference_variance` flows into `BeliefState`),
   confirm the two guards agree — the stricter bound wins, always.
4. **Write both directions as tests**: every invalid value at and past the
   boundary raises `ValueError`, and the full valid boundary/interior
   range still constructs without error.
5. **Grep for the pattern's absence, not just its presence.** A tree-wide
   grep for unvalidated `float`/`str` dataclass fields feeding arithmetic
   or SQL/DDL construction is what actually found these gaps — not code
   review of the fields that already had guards.
