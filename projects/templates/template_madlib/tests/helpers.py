from __future__ import annotations

from pathlib import Path

import yaml


def write_config(root: Path, payload: dict) -> None:
    manuscript = root / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "config.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")


def base_payload() -> dict:
    return {
        "paper": {"title": "Test Madlib"},
        "madlib": {
            "seed": 7,
            "composition_depth": "deep",
            "hypothesis": "Tokens remain auditable.",
            "section_conditions": {"discussion": False},
            "section_titles": {"methods": "Methods: Test Protocol"},
            "narrative_moves": {"methods": ["load config", "expand slots"]},
            "method_protocol": [
                {
                    "name": "Ingest declared manuscript schema",
                    "action": "Parse config before composition.",
                    "evidence": "Config validation test.",
                    "output": "MadlibConfig",
                },
                {
                    "name": "Track configured field origins",
                    "action": "Separate explicit YAML paths from loader defaults.",
                    "evidence": "configured_field_inventory.json.",
                    "output": "field-origin inventory",
                },
                {
                    "name": "Review selection invariants",
                    "action": "Confirm only declared digest inputs can change token choices.",
                    "evidence": "Token determinism tests.",
                    "output": "selection invariant set",
                },
                {
                    "name": "Generate evidence tables and figures",
                    "action": "Build tables and registered figures from generated data.",
                    "evidence": "Artifact and figure tests.",
                    "output": "output/data, output/reports, and output/figures",
                },
                {
                    "name": "Align claims with evidence ledger",
                    "action": "Tie local method claims to config, source, or artifacts.",
                    "evidence": "data/claim_ledger.yaml.",
                    "output": "claim-aligned evidence surface",
                },
                {
                    "name": "Render and hand off review bundle",
                    "action": "Render, validate, copy, and leave review obligations explicit.",
                    "evidence": "Stage logs.",
                    "output": "output/templates/template_madlib",
                },
            ],
            "audit_rules": [
                "Every placeholder resolves.",
                "Every method protocol row identifies action, evidence, and output.",
                "Every fork that adds domain claims must add validators.",
                "Every review handoff includes data, reports, figures, validation, and copy statistics.",
            ],
            "contribution_claims": [
                "Config-owned tokens are auditable.",
                "Generated methods remain auditable when rows, figures, and gates share one source.",
                "Review packets make generated-method handoff auditable beyond PDF or HTML.",
            ],
            "evaluation_criteria": [
                {
                    "name": "Placeholder resolution",
                    "target": "No unresolved tokens.",
                    "evidence": "pytest",
                    "gate": "tests",
                }
            ],
            "failure_modes": [
                {
                    "name": "Unresolved placeholder",
                    "risk": "Missing variable.",
                    "detection": "scan output",
                    "mitigation": "add a variable",
                },
                {
                    "name": "Fork without validators",
                    "risk": "Domain claims rely only on generic gates.",
                    "detection": "claim ledger review",
                    "mitigation": "add domain validators",
                },
                {
                    "name": "Review packet incompleteness",
                    "risk": "Reviewer lacks generated evidence artifacts.",
                    "detection": "copy statistics review",
                    "mitigation": "regenerate full output packet",
                },
            ],
            "design_principles": [
                {
                    "name": "Configuration owns prose choices",
                    "rationale": "Reviewers can inspect declared language.",
                    "manuscript_effect": "Section variables are generated from source.",
                },
                {
                    "name": "Forks must add validators",
                    "rationale": "Domain claims need domain evidence.",
                    "manuscript_effect": "Authoring obligations require validators before domain claims.",
                },
                {
                    "name": "Review packet is a method artifact",
                    "rationale": "PDF alone is insufficient method evidence.",
                    "manuscript_effect": "Generated artifacts travel with the manuscript.",
                },
            ],
            "pipeline_phases": [
                {
                    "name": "Schema parse",
                    "input_artifact": "manuscript/config.yaml",
                    "transformation": "Load config.",
                    "output_artifact": "MadlibConfig",
                    "guard": "config tests",
                },
                {
                    "name": "Evidence and visualization emission",
                    "input_artifact": "MadlibConfig and TokenPlan",
                    "transformation": "Write audit tables, reports, figures, and registry.",
                    "output_artifact": "output/data, output/reports, and output/figures",
                    "guard": "artifact and figure tests",
                },
                {
                    "name": "Review packet assembly",
                    "input_artifact": "validated output and copy statistics",
                    "transformation": "Group manuscript, web, slides, figures, data, reports, and validation.",
                    "output_artifact": "review packet",
                    "guard": "copied-output validation",
                },
            ],
            "quality_probes": [
                {
                    "name": "Placeholder survival",
                    "question": "Did any token survive?",
                    "passing_signal": "No placeholders remain.",
                    "artifact": "output/manuscript",
                },
                {
                    "name": "Method completeness",
                    "question": "Do method rows cover generation, evidence, rendering, and review?",
                    "passing_signal": "Protocol and phase tables contain expected responsibilities.",
                    "artifact": "manuscript/config.yaml",
                },
                {
                    "name": "Digest invariant review",
                    "question": "Are token-selection inputs documented and tested?",
                    "passing_signal": "Methods prose names digest inputs.",
                    "artifact": "src/tokens.py and output/manuscript/02_methodology.md",
                },
            ],
            "authoring_obligations": [
                {
                    "name": "Review generated claims",
                    "obligation": "Inspect hydrated manuscript.",
                    "review_surface": "output/manuscript",
                },
                {
                    "name": "Assemble reviewer packet",
                    "obligation": "Provide generated evidence artifacts with rendered output.",
                    "review_surface": "output/templates/template_madlib",
                },
            ],
            "lexicon": {
                "adjectives": ["auditable", "conditional"],
                "nouns": ["manuscript", "token"],
                "verbs": ["compose", "trace"],
                "methods": ["hash indexing"],
                "constraints": ["config owned"],
                "artifacts": ["token inventory"],
                "qualities": ["traceability"],
                "audiences": ["reviewers"],
                "failures": ["unresolved placeholder"],
            },
            "slots": [
                {"name": "first_adjective", "category": "adjectives", "section": "abstract"},
                {"name": "noun_pair", "category": "nouns", "section": "introduction", "count": 2},
                {"name": "method", "category": "methods", "section": "methods"},
            ],
        },
    }
