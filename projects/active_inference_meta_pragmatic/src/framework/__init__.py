"""Framework modules for the Active Inference Meta-Pragmatic project.

Contains the 2x2 quadrant framework, meta-cognition system,
modeler perspective, and cognitive security analyzer.
"""

from .cognitive_security import CognitiveSecurityAnalyzer
from .meta_cognition import (
    MetaCognitiveSystem,
    demonstrate_meta_cognitive_processes,
    demonstrate_thinking_about_thinking,
)
from .modeler_perspective import (
    ModelerPerspective,
    demonstrate_modeler_perspective,
)
from .quadrant_framework import (
    QuadrantFramework,
    demonstrate_quadrant_framework,
)

__all__ = [
    "QuadrantFramework",
    "demonstrate_quadrant_framework",
    "MetaCognitiveSystem",
    "demonstrate_meta_cognitive_processes",
    "demonstrate_thinking_about_thinking",
    "ModelerPerspective",
    "demonstrate_modeler_perspective",
    "CognitiveSecurityAnalyzer",
]
