"""Interactive dashboard modules for the code project: payload computation,
Plotly panel assembly, and the thin facade plus CLI entry point.

These modules are re-exported from ``template_code_project`` for
the supported public API; import them from the package root.
"""

from .dashboard import (
    CFG_DEFAULT,
    DATA_DIR,
    OUTPUT,
    PROJECT_ROOT,
    REP_DIR,
    REPO_ROOT,
    WEB_DIR,
    build_dashboard_html,
    cli_main,
    parse_dashboard_args,
)
from .dashboard_panels import build_dashboard, to_dashboard_invariant
from .dashboard_payload import (
    DASHBOARD_PAYLOAD_SCHEMA_VERSION,
    DashboardPayloadError,
    compute_payload,
    load_yaml_defaults,
    to_diagonal_A,
    validate_dashboard_payload,
)

__all__ = [
    "CFG_DEFAULT",
    "DASHBOARD_PAYLOAD_SCHEMA_VERSION",
    "DashboardPayloadError",
    "DATA_DIR",
    "OUTPUT",
    "PROJECT_ROOT",
    "REP_DIR",
    "REPO_ROOT",
    "WEB_DIR",
    "build_dashboard",
    "build_dashboard_html",
    "cli_main",
    "compute_payload",
    "load_yaml_defaults",
    "parse_dashboard_args",
    "to_dashboard_invariant",
    "to_diagonal_A",
    "validate_dashboard_payload",
]
