"""CSV data export functions for executive reporting dashboards.

This module is a **re-export hub**.  All implementation has been split into
focused submodules:

  - ``_csv_project_breakdown`` — detailed per-project metric breakdown
  - ``_csv_comparative``       — cross-project rankings and percentiles
  - ``_csv_tables``            — prioritized recommendations + bulk data tables

Every public name that was previously importable from this module is still
available via the re-exports below.
"""

from __future__ import annotations

from infrastructure.reporting._csv_comparative import (  # noqa: F401
    generate_comparative_analysis_csv,
)
from infrastructure.reporting._csv_project_breakdown import (  # noqa: F401
    generate_detailed_project_breakdown_csv,
)
from infrastructure.reporting._csv_tables import (  # noqa: F401
    generate_csv_data_tables,
    generate_prioritized_recommendations_csv,
)
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)
__all__ = [
    "generate_comparative_analysis_csv",
    "generate_csv_data_tables",
    "generate_detailed_project_breakdown_csv",
    "generate_prioritized_recommendations_csv",
]
