"""Core modules for the autopoiesis exemplar: CLI entry point, shared
dataclasses and utilities, deterministic grammar expansion, grammar
definition and parsing, the honesty manifest, and output-path helpers.

These modules are re-exported from ``template_autopoiesis`` for backwards
compatibility; import them from the package root.
"""

from .cli import (
    build_parser,
    cmd_enumerate,
    cmd_expand,
    cmd_honesty,
    cmd_materialize,
    cmd_sample,
    cmd_verify,
    main,
)
from .common import (
    CheckReport,
    CheckResult,
    DERIVED_SEED_BITS,
    HASH_PREFIX_HEX_LENGTH,
    trunc,
)
from .expand import (
    SCHEMA_VERSION,
    Spec,
    derive_seed,
    enumerate_all,
    expand,
    filter_archetypes,
    sample,
    write_spec,
)
from .grammar import (
    DEP_MODES,
    Grammar,
    GrammarError,
    GrammarSlot,
    KNOWN_DOMAINS,
    RESERVED_SLOTS,
    VENDORABLE_DEPS,
    force_domain,
    load_grammar,
    parse_grammar,
)
from .honesty import (
    HonestyManifest,
    STRUCTURAL_EVIDENCE,
    build_manifest,
    verify_honesty,
)
from .project_paths import project_output_dirs

__all__ = [
    "CheckReport",
    "CheckResult",
    "DEP_MODES",
    "DERIVED_SEED_BITS",
    "Grammar",
    "GrammarError",
    "GrammarSlot",
    "HASH_PREFIX_HEX_LENGTH",
    "HonestyManifest",
    "KNOWN_DOMAINS",
    "RESERVED_SLOTS",
    "SCHEMA_VERSION",
    "Spec",
    "STRUCTURAL_EVIDENCE",
    "VENDORABLE_DEPS",
    "build_manifest",
    "build_parser",
    "cmd_enumerate",
    "cmd_expand",
    "cmd_honesty",
    "cmd_materialize",
    "cmd_sample",
    "cmd_verify",
    "derive_seed",
    "enumerate_all",
    "expand",
    "filter_archetypes",
    "force_domain",
    "load_grammar",
    "main",
    "parse_grammar",
    "project_output_dirs",
    "sample",
    "trunc",
    "verify_honesty",
    "write_spec",
]
