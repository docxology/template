"""Subfield registry: config loading and pattern cache."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

GENERIC_DEFAULT_SUBFIELDS: dict[str, dict] = {
    "A1_formal": {
        "keywords": [
            # Mathematical structures and methods
            "category theory",
            "information geometry",
            "bayesian mechanics",
            "boundary conditions",
            "stochastic",
            "langevin",
            "gauge theory",
            "path integral",
            "differential equation",
            "dynamical system",
            "fixed point",
            "convergence",
            "ergodic",
            "measure theory",
            "manifold",
            "lie group",
            # Formal reasoning indicators
            "theorem",
            "proof",
            "lemma",
            "corollary",
            "proposition",
            "derivation",
            "formalism",
            "formulation",
            "analytical",
            # Variational and optimization formalism
            "variational inference",
            "variational bound",
            "kl divergence",
            "kullback-leibler",
            "elbo",
            "evidence lower bound",
            "laplace approximation",
            "mean field",
            "message passing",
            "belief propagation",
            "expectation propagation",
            # Statistical mechanics and physics formalism
            "partition function",
            "hamiltonian",
            "lagrangian",
            "entropy production",
            "fluctuation theorem",
            "ito",
            "fokker-planck",
            "helmholtz",
            # Probability and inference formalism
            "posterior",
            "prior",
            "likelihood",
            "marginal",
            "conjugate",
            "sufficient statistic",
            "exponential family",
            "dirichlet",
            "state space model",
            # Mathematical notation indicators
            "equation",
            "matrix",
            "eigenvalue",
            "jacobian",
            "hessian",
            "gradient descent",
            "optimization",
            "objective function",
            "loss function",
        ],
        "description": "A1: Quantitative and formal mathematical theory",
        "priority": 3,  # Lower priority than C/B (checked after specific domains)
    },
    "A2_philosophy": {
        "keywords": [
            # Genuinely philosophical and qualitative terms
            "phenomenology",
            "epistemology",
            "ontology",
            "enactivism",
            "4e cognition",
            "embodied cognition",
            "extended mind",
            "predictive processing",
            "bayesian brain",
            "ecological psychology",
            "affordance",
            "niche construction",
            "autopoiesis",
            "sense-making",
            "consciousness",
            "qualia",
            "intentionality",
            "teleology",
            "reductionism",
            "emergence",
            "self-organization",
            "autonomy",
            "agency",
            "normativity",
            "naturalism",
            # General conceptual terms (catch-all when no specific domain matches)
            "conceptual framework",
            "theoretical perspective",
            "generative model",
        ],
        "description": "A2: Qualitative, conceptual, and review-style discussion",
        "priority": 4,  # Lowest priority — catch-all
    },
    "B_tools": {
        "keywords": [
            "planning",
            "reinforcement learning",
            "deep learning",
            "neural network",
            "amortized",
            "scalable",
            "monte carlo",
            "tree search",
            "benchmark",
            "implementation",
            "library",
            "software",
            "framework",
            "toolkit",
            "open source",
            "api",
            "algorithm",
            "gymnasium",
            "environment",
        ],
        "description": "B: Tools and translation methods development",
        "priority": 2,
    },
    "C1_neuroscience": {
        "keywords": [
            "neural",
            "cortical",
            "hippocampal",
            "eeg",
            "fmri",
            "neuroimaging",
            "synaptic",
            "dopamine",
            "spiking",
            "prefrontal",
            "basal ganglia",
            "cerebellum",
            "thalamus",
            "electrophysiology",
            "meg",
            "bold",
            "brain imaging",
            "neuron",
            "dendrit",
        ],
        "description": "C1: Computational and systems neuroscience",
        "priority": 1,
    },
    "C2_robotics": {
        "keywords": [
            "robot",
            "sensorimotor",
            "motor control",
            "embodied",
            "navigation",
            "manipulation",
            "actuator",
            "simulator",
            "gazebo",
            "ros ",
            "control loop",
            "pid",
            "end effector",
            "gripper",
        ],
        "description": "C2: Robotics and embodied agents",
        "priority": 1,
    },
    "C3_language": {
        "keywords": [
            "language",
            "linguistic",
            "speech",
            "semantic",
            "reading",
            "communication",
            "natural language",
            "syntax",
            "morphology",
            "phonology",
            "discourse",
            "pragmatics",
            "transformer",
            "large language model",
            "llm",
            "tokeniz",
        ],
        "description": "C3: Language processing and communication",
        "priority": 1,
    },
    "C4_psychiatry": {
        "keywords": [
            "psychiatric",
            "schizophrenia",
            "depression",
            "autism",
            "anxiety",
            "psychosis",
            "computational psychiatry",
            "clinical",
            "disorder",
            "diagnosis",
            "symptom",
            "patient",
            "therapy",
            "treatment",
            "mental health",
            "ptsd",
            "ocd",
            "bipolar",
            "addiction",
        ],
        "description": "C4: Computational psychiatry and clinical applications",
        "priority": 1,
    },
    "C5_biology": {
        "keywords": [
            "morphogenesis",
            "cell",
            "organism",
            "evolution",
            "life",
            "autopoiesis",
            "biological",
            "developmental",
            "gene",
            "protein",
            "metabolism",
            "homeostasis",
            "ecological",
            "phenotype",
            "genotype",
            "fitness",
            "adaptation",
            "species",
        ],
        "description": "C5: Biology and morphogenesis",
        "priority": 1,
    },
}


logger = logging.getLogger(__name__)

SUBFIELDS: dict[str, dict] = dict(GENERIC_DEFAULT_SUBFIELDS)
_PATTERN_CACHE: dict[str, list] = {}


def _build_pattern_cache() -> None:
    """Pre-compile word-boundary regex for every keyword in SUBFIELDS."""
    global _PATTERN_CACHE
    _PATTERN_CACHE = {
        field: [re.compile(r"\b" + re.escape(kw.lower()) + r"\b") for kw in info.get("keywords", [])]
        for field, info in SUBFIELDS.items()
    }


def load_subfields_from_config(config_path: Path) -> dict[str, dict]:
    """Load subfield keyword definitions from a YAML config file."""
    try:
        import yaml
    except ImportError:
        logger.warning("PyYAML not available; using default subfields")
        return dict(GENERIC_DEFAULT_SUBFIELDS)

    try:
        with open(config_path, encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except (OSError, yaml.YAMLError) as exc:
        logger.warning("Cannot read config %s: %s; using defaults", config_path, exc)
        return dict(GENERIC_DEFAULT_SUBFIELDS)

    subfield_kw = data.get("subfield_keywords") or data.get("project_config", {}).get("subfield_keywords")
    if not subfield_kw or not isinstance(subfield_kw, dict):
        logger.info("No subfield_keywords in config; using defaults")
        return dict(GENERIC_DEFAULT_SUBFIELDS)

    result: dict[str, dict] = {}
    priority_map = {"C": 1, "B": 2, "A1": 3, "A2": 4}
    for name, keywords in subfield_kw.items():
        if isinstance(keywords, list):
            priority = 4
            for prefix, prio in priority_map.items():
                if name.startswith(prefix):
                    priority = prio
                    break
            result[name] = {
                "keywords": keywords,
                "description": name.replace("_", " ").title(),
                "priority": priority,
            }
        else:
            logger.warning("Skipping non-list subfield entry: %s", name)

    if not result:
        logger.warning("Config subfield_keywords was empty; using defaults")
        return dict(GENERIC_DEFAULT_SUBFIELDS)

    logger.info(
        "Loaded %d subfield definitions from config: %s",
        len(result),
        list(result.keys()),
    )
    return result


def configure_subfields(config_path: Optional[Path] = None) -> dict[str, dict]:
    """Set module-level SUBFIELDS from config or defaults.

    Mutates the existing SUBFIELDS dict IN PLACE (clear + update) rather than
    rebinding it. Modules that did ``from ...subfield_registry import SUBFIELDS``
    (e.g. subfield_classifier) hold a reference to this exact object; rebinding
    the global here would leave their binding pointing at the stale default set,
    so the configured taxonomy would silently never apply at runtime.
    """
    new = load_subfields_from_config(config_path) if config_path is not None else dict(GENERIC_DEFAULT_SUBFIELDS)
    SUBFIELDS.clear()
    SUBFIELDS.update(new)
    _build_pattern_cache()
    return SUBFIELDS


def get_pattern_cache() -> dict[str, list]:
    """Return the compiled keyword pattern cache (for classification)."""
    return _PATTERN_CACHE


_build_pattern_cache()
