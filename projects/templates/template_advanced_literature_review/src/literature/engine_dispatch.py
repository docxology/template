"""Advanced public boundary backed by the declared canonical literature engine."""

from template_literature_meta_analysis.literature.engine_dispatch import (
    ENGINE_SPECS as ENGINE_SPECS,
)
from template_literature_meta_analysis.literature.engine_dispatch import (
    EngineSpec as EngineSpec,
)
from template_literature_meta_analysis.literature.engine_dispatch import (
    dispatch_ordered as dispatch_ordered,
)
from template_literature_meta_analysis.literature.engine_dispatch import (
    engine_enabled as engine_enabled,
)

__all__ = ["ENGINE_SPECS", "EngineSpec", "dispatch_ordered", "engine_enabled"]
