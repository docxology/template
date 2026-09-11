"""Resource-facing modules for the pools/rules/tools exemplar: fonds
reading, rules/tools manifests, schema receipts, typed definitions, and
the end-to-end integration orchestrator.

These modules are re-exported from ``template_pools_rules_tools`` for
backwards compatibility; import them from the package root.
"""

from .fonds_reader import (
    count_summary,
    get_fonds_root,
    read_all_fonds,
    read_bibliography_fond,
    read_contacts_fond,
    read_datasets_fond,
)
from .integration import (
    check_bibliography_overlap,
    derive_dashboard_data,
    generate_figure_data,
    run_integration_demo,
)
from .resource_schema import (
    REQUIRED_MANIFEST_KEYS,
    build_resource_schema_receipt,
    validate_resource_directory,
    validate_resource_manifest,
)
from .tools_invoker import (
    discover_tools,
    discover_tools_with_validation,
    get_tool_entrypoints,
    get_tools_root,
    validate_tool_scripts_exist,
)
from .type_defs import (
    AllFondsResult,
    AllRulesResult,
    BibliographyFondResult,
    ContactsFondResult,
    CrossFondOverlapResult,
    DatasetsFondResult,
    FigureDataRow,
    FondsSummary,
    IntegrationResult,
    IntegrationSummary,
    RuleSetResult,
    SoftRuleEntry,
    StrongRuleEntry,
    ToolEntry,
    ToolEntryWithValidation,
    ToolValidationResult,
)

__all__ = [
    "AllFondsResult",
    "AllRulesResult",
    "BibliographyFondResult",
    "ContactsFondResult",
    "CrossFondOverlapResult",
    "DatasetsFondResult",
    "FigureDataRow",
    "FondsSummary",
    "IntegrationResult",
    "IntegrationSummary",
    "REQUIRED_MANIFEST_KEYS",
    "RuleSetResult",
    "SoftRuleEntry",
    "StrongRuleEntry",
    "ToolEntry",
    "ToolEntryWithValidation",
    "ToolValidationResult",
    "build_resource_schema_receipt",
    "check_bibliography_overlap",
    "count_summary",
    "derive_dashboard_data",
    "discover_tools",
    "discover_tools_with_validation",
    "generate_figure_data",
    "get_fonds_root",
    "get_tool_entrypoints",
    "get_tools_root",
    "read_all_fonds",
    "read_bibliography_fond",
    "read_contacts_fond",
    "read_datasets_fond",
    "run_integration_demo",
    "validate_resource_directory",
    "validate_resource_manifest",
    "validate_tool_scripts_exist",
]
