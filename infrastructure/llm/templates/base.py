"""Base template class for LLM operations."""
from __future__ import annotations

from typing import Any
from string import Template

from infrastructure.core.exceptions import LLMTemplateError


class ResearchTemplate:
    """Base class for research templates."""
    
    template_str: str = ""
    
    def render(self, **kwargs: Any) -> str:
        """Render template with variables."""
        try:
            return Template(self.template_str).substitute(**kwargs)
        except KeyError as e:
            raise LLMTemplateError(
                f"Missing template variable: {e}",
                context={"required": str(e)}
            )










