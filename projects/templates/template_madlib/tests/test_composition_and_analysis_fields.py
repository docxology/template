from __future__ import annotations

from pathlib import Path


from src.analysis_fields import configured_field_counts, configured_field_inventory
from src.config import load_madlib_config
from src.tokens import generate_token_plan
from .helpers import base_payload, write_config

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# analysis_fields: _slot_summary with unknown slot name
# ---------------------------------------------------------------------------


def test_slot_summary_unknown_slot_returns_slot_string(tmp_path: Path) -> None:
    """_slot_summary for an unknown slot path should return 'slot'."""
    from src.analysis_fields import _slot_summary

    write_config(tmp_path, base_payload())

    config = load_madlib_config(tmp_path)

    # Pass a path for a slot name that doesn't exist in config
    result = _slot_summary(config, "madlib.slots.nonexistent_slot")

    assert result == "slot"


# ---------------------------------------------------------------------------
# analysis_fields: _field_scope covers all scope categories
# ---------------------------------------------------------------------------


def test_field_scope_section_paths(tmp_path: Path) -> None:
    """Paths containing .section_conditions., .section_titles., .narrative_moves. → 'section'."""
    from src.analysis_fields import _field_scope

    assert _field_scope("madlib.section_conditions.abstract") == "section"
    assert _field_scope("madlib.section_titles.methods") == "section"
    assert _field_scope("madlib.narrative_moves.results") == "section"


def test_field_scope_lexicon_path(tmp_path: Path) -> None:
    """Paths containing .lexicon. → 'lexicon'."""
    from src.analysis_fields import _field_scope

    assert _field_scope("madlib.lexicon.adjectives") == "lexicon"


def test_field_scope_slot_path(tmp_path: Path) -> None:
    """Paths containing .slots. → 'slot'."""
    from src.analysis_fields import _field_scope

    assert _field_scope("madlib.slots.first_adjective") == "slot"
    assert _field_scope("madlib.slots.first_adjective.count") == "slot"


def test_field_scope_visualization_path(tmp_path: Path) -> None:
    """Paths containing .visualizations → 'visualization'."""
    from src.analysis_fields import _field_scope

    assert _field_scope("madlib.visualizations.enabled") == "visualization"
    assert _field_scope("madlib.visualizations") == "visualization"


def test_field_scope_schema_path(tmp_path: Path) -> None:
    """Paths not matching any special prefix → 'schema'."""
    from src.analysis_fields import _field_scope

    assert _field_scope("madlib.seed") == "schema"
    assert _field_scope("madlib.composition_depth") == "schema"
    assert _field_scope("madlib.hypothesis") == "schema"
    assert _field_scope("madlib") == "schema"


# ---------------------------------------------------------------------------
# analysis_fields: _field_summary for all branches
# ---------------------------------------------------------------------------


def test_field_summary_for_various_paths(tmp_path: Path) -> None:
    """_field_summary must return meaningful strings for all known path patterns."""
    from src.analysis_fields import _field_summary

    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    # Core schema fields
    assert _field_summary(config, plan, "madlib.seed") == str(config.seed)
    assert _field_summary(config, plan, "madlib.composition_depth") == config.composition_depth
    assert _field_summary(config, plan, "madlib.hypothesis") == config.hypothesis

    # Aggregate fields
    assert "categories" in _field_summary(config, plan, "madlib.lexicon")
    assert "slot rules" in _field_summary(config, plan, "madlib.slots")
    assert _field_summary(config, plan, "madlib.visualizations") in ("enabled", "disabled")

    # Section-level fields
    assert _field_summary(config, plan, "madlib.section_conditions.abstract") in ("enabled", "disabled")
    assert len(_field_summary(config, plan, "madlib.section_titles.methods")) > 0
    assert "moves" in _field_summary(config, plan, "madlib.narrative_moves.methods")

    # Lexicon level
    assert "tokens" in _field_summary(config, plan, "madlib.lexicon.adjectives")

    # Visualization flags
    result = _field_summary(config, plan, "madlib.visualizations.enabled")
    assert result in ("true", "false")

    # Slot sub-fields
    assert _field_summary(config, plan, "madlib.slots.first_adjective.count") == "1"
    assert _field_summary(config, plan, "madlib.slots.noun_pair.section") == "introduction"

    # Block count fields
    for block in (
        "madlib.method_protocol",
        "madlib.evaluation_criteria",
        "madlib.failure_modes",
        "madlib.design_principles",
        "madlib.pipeline_phases",
        "madlib.quality_probes",
        "madlib.authoring_obligations",
        "madlib.audit_rules",
        "madlib.contribution_claims",
    ):
        summary = _field_summary(config, plan, block)
        assert "entries" in summary, f"Expected 'entries' in summary for {block!r}, got {summary!r}"

    # Unknown path
    assert _field_summary(config, plan, "madlib.unknown_field") == "configured field"


# ---------------------------------------------------------------------------
# analysis_fields: configured_field_inventory contains expected scopes
# ---------------------------------------------------------------------------


def test_configured_field_inventory_scopes(tmp_path: Path) -> None:
    """The inventory must contain rows for schema, section, lexicon, slot, and visualization scopes."""
    from src.config import load_madlib_config

    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    inventory = configured_field_inventory(config, plan)

    scopes_present = {row["scope"] for row in inventory}

    assert "schema" in scopes_present
    assert "section" in scopes_present
    assert "lexicon" in scopes_present
    assert "slot" in scopes_present
    assert "visualization" in scopes_present


def test_configured_field_inventory_origins(tmp_path: Path) -> None:
    """The inventory must contain both explicit and defaulted origins."""
    from src.config import load_madlib_config

    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    inventory = configured_field_inventory(config, plan)

    origins_present = {row["origin"] for row in inventory}

    assert "explicit" in origins_present
    assert "defaulted" in origins_present


def test_configured_field_inventory_no_duplicates(tmp_path: Path) -> None:
    """Each path should appear at most once in the inventory."""
    from src.config import load_madlib_config

    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    inventory = configured_field_inventory(config, plan)

    paths = [row["path"] for row in inventory]
    assert len(paths) == len(set(paths))


# ---------------------------------------------------------------------------
# analysis_fields: configured_field_counts aggregation
# ---------------------------------------------------------------------------


def test_configured_field_counts_total_matches_inventory_length(tmp_path: Path) -> None:
    """The 'total' count must equal the length of the inventory."""
    from src.config import load_madlib_config

    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)
    inventory = configured_field_inventory(config, plan)
    counts = configured_field_counts(config, inventory)

    assert counts["total"] == len(inventory)
    assert counts["explicit"] + counts["defaulted"] == counts["total"]
