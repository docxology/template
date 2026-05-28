"""Machine-verified sheaf laws over the IMRAD base poset.

The composer in :mod:`manuscript.sheaf.compose` *performs* gluing — it
concatenates per-section track fragments into one flat global manuscript. This
module *verifies the axioms that gluing implicitly assumes*, turning the word
"sheaf" from notation into a runnable, falsifiable claim.

We model the manuscript as a coverage sheaf over a finite base poset:

* **Base poset** ``P`` — the IMRAD blocks ``introduction < methods < results <
  discussion < appendix`` ordered as a chain, with the per-block *group* row
  containing its *section* rows (``group ⊒ section``). ``P`` is a finite poset
  (equivalently, a finite Alexandrov space).
* **Presheaf** ``F : P^op → Set`` — each composing section ``s`` is assigned the
  set of bound, well-typed track fragments ``F(s) = {(t, path) : t ∈ tracks(s)}``.
  Restriction along ``group ⊒ section`` is the projection onto the section's
  bindings (groups carry the empty assignment and do not compose).
* **Separation (locality)** — distinct composing sections glue to distinct
  global positions: ``s ↦ output_name(s)`` is injective. No two locals collapse
  onto one global section.
* **Gluing** — the compose order is a *linear extension* of ``P`` (block rank
  monotone in row order; within a block, section order strictly increasing), so
  the local fragments glue to a unique global section, and every composing
  section appears exactly once.
* **Typing** — each binding ``(t, path)`` is well-typed: ``renderer(t)`` exists
  and ``path``'s suffix lies in the renderer's accepted suffix set. Generated
  renderers (``section_figures``, ``layers_report``) carry no file-type
  contract and are explicitly type-exempt.
* **Compositionality** — every fragment file is *private* to one section (no
  fragment path is bound by two sections), so global composition is the
  coproduct (disjoint union) of the per-section bodies and is independent of
  inclusion order.

What is **not** claimed: this module verifies the sheaf *axioms* on a finite
base; it does **not** compute sheaf *cohomology* (``H^0``/``H^1``, Čech
complexes, derived functors). See ``verify_sheaf_laws`` for the oracle and
``tests/test_sheaf_laws.py`` for the negative controls that prove each check
bites.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from manuscript.sheaf.manifest import load_manifest
from manuscript.sheaf.models import (
    DEFAULT_MANIFEST_REL,
    SheafManifest,
    SheafSection,
    TrackRegistry,
)
from manuscript.sheaf.registry import load_track_registry, track_order_for_section
from manuscript.sheaf.renderers import GENERATED_RENDERERS, RENDERERS

# Canonical chain order of the IMRAD base poset. Lower rank composes first.
IMRAD_ORDER: tuple[str, ...] = (
    "introduction",
    "methods",
    "results",
    "discussion",
    "appendix",
)


class SheafLaw(str, Enum):
    """The structural laws that make the coverage presheaf a sheaf."""

    POSET = "poset"
    PRESHEAF = "presheaf"
    SEPARATION = "separation"
    GLUING = "gluing"
    TYPING = "typing"
    COMPOSITIONALITY = "compositionality"


@dataclass(frozen=True)
class LawViolation:
    """A single counter-example to one sheaf law."""

    law: SheafLaw
    code: str
    message: str


@dataclass
class SheafLawReport:
    """Structured result of verifying the sheaf laws against a manifest."""

    violations: list[LawViolation] = field(default_factory=list)
    checked: tuple[SheafLaw, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.violations

    def for_law(self, law: SheafLaw) -> list[LawViolation]:
        return [v for v in self.violations if v.law == law]

    def law_ok(self, law: SheafLaw) -> bool:
        return not self.for_law(law)

    @property
    def passed_laws(self) -> tuple[SheafLaw, ...]:
        failed = {v.law for v in self.violations}
        return tuple(law for law in self.checked if law not in failed)

    def summary(self) -> str:
        if self.ok:
            return f"sheaf laws: {len(self.checked)}/{len(self.checked)} verified"
        return f"sheaf laws: {len(self.passed_laws)}/{len(self.checked)} verified, {len(self.violations)} violation(s)"


def _known_renderers() -> frozenset[str]:
    known: frozenset[str] = frozenset(RENDERERS.keys()) | GENERATED_RENDERERS
    return known


def _composing_sections(manifest: SheafManifest) -> list[SheafSection]:
    return [s for s in manifest.sections if s.should_compose()]


def _check_poset(manifest: SheafManifest) -> list[LawViolation]:
    """IMRAD blocks form a chain; compose order is monotone in block rank."""
    out: list[LawViolation] = []
    rank = {block: i for i, block in enumerate(IMRAD_ORDER)}
    ordered = sorted(manifest.sections, key=lambda s: s.order)
    last_rank = -1
    for section in ordered:
        if section.imrad not in rank:
            out.append(
                LawViolation(
                    SheafLaw.POSET,
                    "unknown_imrad_block",
                    f"{section.id}: imrad block `{section.imrad}` not in chain {IMRAD_ORDER}",
                )
            )
            continue
        r = rank[section.imrad]
        if r < last_rank:
            out.append(
                LawViolation(
                    SheafLaw.POSET,
                    "non_monotone_block_order",
                    f"{section.id}: block `{section.imrad}` (rank {r}) follows a higher-rank "
                    f"block (rank {last_rank}); compose order is not a linear extension of P",
                )
            )
        last_rank = max(last_rank, r)
    # group ⊒ section containment. The group presentation is optional, but if a
    # manifest uses it at all, it must use it uniformly: every block with
    # composing sections needs a group row. A group-free manifest is exempt.
    group_blocks = {s.imrad for s in manifest.sections if s.kind == "group"}
    if group_blocks:
        for section in _composing_sections(manifest):
            if section.imrad not in group_blocks:
                out.append(
                    LawViolation(
                        SheafLaw.POSET,
                        "section_without_group",
                        f"{section.id}: block `{section.imrad}` has no group row (group ⊒ section containment broken)",
                    )
                )
    return out


def _check_presheaf(manifest: SheafManifest, registry: TrackRegistry) -> list[LawViolation]:
    """Bound tracks are registered; track order restricts the global order."""
    out: list[LawViolation] = []
    specs = registry.tracks
    # The global track order must be a strict total order (distinct ranks),
    # else "the monotone restriction of the global order" is ill-defined.
    orders: dict[int, list[str]] = {}
    for tid, spec in specs.items():
        orders.setdefault(spec.order, []).append(tid)
    for order_val, ids in orders.items():
        if len(ids) > 1:
            out.append(
                LawViolation(
                    SheafLaw.PRESHEAF,
                    "duplicate_track_order",
                    f"tracks {sorted(ids)} share compose order {order_val}; global track order is not strict",
                )
            )
    for section in _composing_sections(manifest):
        for tid in section.tracks:
            if specs and tid not in specs:
                out.append(
                    LawViolation(
                        SheafLaw.PRESHEAF,
                        "unbound_track",
                        f"{section.id}: track `{tid}` is not in the registry",
                    )
                )
        # Resolved local order must be monotone in the global registry order
        # (an explicit track_order override is allowed, but must be a permutation
        # of the bound tracks — verified by track_order_for_section's contract).
        resolved = [t for t in track_order_for_section(section, registry) if t in specs]
        ranks = [specs[t].order for t in resolved]
        if section.track_order is None and ranks != sorted(ranks):
            out.append(
                LawViolation(
                    SheafLaw.PRESHEAF,
                    "non_monotone_restriction",
                    f"{section.id}: resolved track order {resolved} is not monotone in the global registry order",
                )
            )
        if section.track_order is not None:
            bound = set(section.tracks)
            override = set(section.track_order)
            missing = override - bound
            if missing:
                out.append(
                    LawViolation(
                        SheafLaw.PRESHEAF,
                        "track_order_not_permutation",
                        f"{section.id}: track_order references unbound tracks {sorted(missing)}",
                    )
                )
    return out


def _check_separation(manifest: SheafManifest) -> list[LawViolation]:
    """s ↦ output_name is injective over composing sections."""
    out: list[LawViolation] = []
    seen_outputs: dict[str, str] = {}
    seen_ids: set[str] = set()
    for section in _composing_sections(manifest):
        if section.id in seen_ids:
            out.append(
                LawViolation(
                    SheafLaw.SEPARATION,
                    "duplicate_section_id",
                    f"section id `{section.id}` is declared twice; global anchors collide",
                )
            )
        seen_ids.add(section.id)
        prior = seen_outputs.get(section.output_name)
        if prior is not None:
            out.append(
                LawViolation(
                    SheafLaw.SEPARATION,
                    "output_name_collision",
                    f"sections `{prior}` and `{section.id}` both glue to "
                    f"`{section.output_name}`; locality (separation) broken",
                )
            )
        seen_outputs[section.output_name] = section.id
    return out


def _check_gluing(manifest: SheafManifest) -> list[LawViolation]:
    """Compose order is a strict linear extension; each section glues once."""
    out: list[LawViolation] = []
    rank = {block: i for i, block in enumerate(IMRAD_ORDER)}
    # Within each IMRAD block, composing-section order must be strictly increasing.
    by_block: dict[str, list[SheafSection]] = {}
    for section in _composing_sections(manifest):
        by_block.setdefault(section.imrad, []).append(section)
    for block, sections in by_block.items():
        ordered = sorted(sections, key=lambda s: s.order)
        orders = [s.order for s in ordered]
        if len(set(orders)) != len(orders):
            out.append(
                LawViolation(
                    SheafLaw.GLUING,
                    "duplicate_compose_order",
                    f"block `{block}`: composing sections share an order value {orders}; gluing order is ambiguous",
                )
            )
    # The full row order must place every block's rows contiguously (linear
    # extension of the chain) — i.e. once we leave a block we never return.
    seen_blocks: list[str] = []
    for section in sorted(manifest.sections, key=lambda s: s.order):
        if section.imrad not in rank:
            continue
        if not seen_blocks or seen_blocks[-1] != section.imrad:
            if section.imrad in seen_blocks:
                out.append(
                    LawViolation(
                        SheafLaw.GLUING,
                        "block_not_contiguous",
                        f"block `{section.imrad}` reappears after another block; "
                        f"compose order is not a linear extension of P",
                    )
                )
            seen_blocks.append(section.imrad)
    return out


def _check_typing(manifest: SheafManifest, registry: TrackRegistry) -> list[LawViolation]:
    """Each binding is well-typed: renderer exists and suffix is accepted."""
    out: list[LawViolation] = []
    specs = registry.tracks
    known = _known_renderers()
    suffixes = registry.renderer_suffixes
    for section in _composing_sections(manifest):
        for tid, rel in section.tracks.items():
            spec = specs.get(tid)
            if spec is None:
                # Reported by the presheaf law; typing cannot judge an unbound track.
                continue
            if spec.renderer not in known:
                out.append(
                    LawViolation(
                        SheafLaw.TYPING,
                        "unknown_renderer",
                        f"{section.id}/{tid}: renderer `{spec.renderer}` is not registered",
                    )
                )
                continue
            if spec.renderer in GENERATED_RENDERERS:
                # Generated renderers synthesize their body; no file-type contract.
                continue
            accepted = suffixes.get(spec.renderer)
            if accepted:
                suffix = Path(rel).suffix
                if suffix not in accepted:
                    out.append(
                        LawViolation(
                            SheafLaw.TYPING,
                            "suffix_type_error",
                            f"{section.id}/{tid}: fragment `{rel}` has suffix `{suffix}` "
                            f"but renderer `{spec.renderer}` accepts {accepted}",
                        )
                    )
    return out


def _check_compositionality(manifest: SheafManifest) -> list[LawViolation]:
    """Every fragment file is private to one section (composition is a coproduct)."""
    out: list[LawViolation] = []
    owner: dict[str, str] = {}
    for section in _composing_sections(manifest):
        for tid, rel in section.tracks.items():
            prior = owner.get(rel)
            if prior is not None and prior != section.id:
                out.append(
                    LawViolation(
                        SheafLaw.COMPOSITIONALITY,
                        "shared_fragment",
                        f"fragment `{rel}` is bound by both `{prior}` and "
                        f"`{section.id}` (via `{tid}`); composition is no longer a "
                        f"coproduct of private locals",
                    )
                )
            owner[rel] = section.id
    return out


_CHECKERS = (
    SheafLaw.POSET,
    SheafLaw.PRESHEAF,
    SheafLaw.SEPARATION,
    SheafLaw.GLUING,
    SheafLaw.TYPING,
    SheafLaw.COMPOSITIONALITY,
)


def verify_sheaf_laws(
    project_root: Path,
    *,
    manifest: SheafManifest | None = None,
    registry: TrackRegistry | None = None,
) -> SheafLawReport:
    """Verify all sheaf laws against the live (or supplied) manifest + registry.

    Returns a :class:`SheafLawReport` whose ``violations`` are concrete
    counter-examples. ``report.ok`` is ``True`` iff the coverage presheaf
    satisfies every sheaf axiom this module checks.
    """
    root = project_root.resolve()
    man = manifest or load_manifest(root / DEFAULT_MANIFEST_REL, project_root=root)
    reg = registry or load_track_registry(root / man.registry_path)

    violations: list[LawViolation] = []
    violations.extend(_check_poset(man))
    violations.extend(_check_presheaf(man, reg))
    violations.extend(_check_separation(man))
    violations.extend(_check_gluing(man))
    violations.extend(_check_typing(man, reg))
    violations.extend(_check_compositionality(man))
    return SheafLawReport(violations=violations, checked=_CHECKERS)


def sheaf_law_violations(
    manifest: SheafManifest,
    registry: TrackRegistry,
) -> list[LawViolation]:
    """Pure law check against in-memory manifest + registry (no filesystem load)."""
    violations: list[LawViolation] = []
    violations.extend(_check_poset(manifest))
    violations.extend(_check_presheaf(manifest, registry))
    violations.extend(_check_separation(manifest))
    violations.extend(_check_gluing(manifest))
    violations.extend(_check_typing(manifest, registry))
    violations.extend(_check_compositionality(manifest))
    return violations


SHEAF_LAW_COUNT = len(_CHECKERS)
