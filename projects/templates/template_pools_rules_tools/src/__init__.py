"""template_pools_rules_tools — public API."""

from .fonds_reader import (
    count_summary,
    get_fonds_root,
    read_all_fonds,
    read_bibliography_fond,
    read_contacts_fond,
    read_datasets_fond,
)
from .rules_applier import (
    get_rules_root,
    load_all_manuscript_rules,
    load_all_project_rules,
    load_soft_rules,
    load_strong_rules,
    validate_against_rules,
)
from .tools_invoker import (
    discover_tools,
    discover_tools_with_validation,
    get_tool_entrypoints,
    get_tools_root,
    validate_tool_scripts_exist,
)
from .integration import generate_figure_data, run_integration_demo
from .figures import (
    generate_architecture_overview,
    generate_resource_counts,
    generate_status_dashboard,
    all_figures,
)
from .types import (
    AllFondsResult,
    AllRulesResult,
    BibliographyFondResult,
    ContactsFondResult,
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
    # Fonds reader
    "read_bibliography_fond",
    "read_contacts_fond",
    "read_datasets_fond",
    "read_all_fonds",
    "count_summary",
    "get_fonds_root",
    # Rules applier
    "load_soft_rules",
    "load_strong_rules",
    "validate_against_rules",
    "load_all_project_rules",
    "load_all_manuscript_rules",
    "get_rules_root",
    # Tools invoker
    "discover_tools",
    "discover_tools_with_validation",
    "get_tool_entrypoints",
    "validate_tool_scripts_exist",
    "get_tools_root",
    # Integration
    "run_integration_demo",
    "generate_figure_data",
    # Types
    "AllFondsResult",
    "AllRulesResult",
    "BibliographyFondResult",
    "ContactsFondResult",
    "DatasetsFondResult",
    "FigureDataRow",
    "FondsSummary",
    "IntegrationResult",
    "IntegrationSummary",
    "RuleSetResult",
    "SoftRuleEntry",
    "StrongRuleEntry",
    "ToolEntry",
    "ToolEntryWithValidation",
    "ToolValidationResult",
]
