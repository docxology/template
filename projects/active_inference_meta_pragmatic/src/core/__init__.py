"""Core Active Inference modules.

Contains the fundamental building blocks: Active Inference framework,
Free Energy Principle, and Generative Models.
"""

from .active_inference import (
    ActiveInferenceFramework,
    demonstrate_active_inference_concepts,
)
from .free_energy_principle import (
    FreeEnergyPrinciple,
    define_what_is_a_thing,
    demonstrate_fep_concepts,
)
from .generative_models import (
    GenerativeModel,
    create_simple_generative_model,
    demonstrate_generative_model_concepts,
)

__all__ = [
    "ActiveInferenceFramework",
    "demonstrate_active_inference_concepts",
    "FreeEnergyPrinciple",
    "define_what_is_a_thing",
    "demonstrate_fep_concepts",
    "GenerativeModel",
    "create_simple_generative_model",
    "demonstrate_generative_model_concepts",
]
