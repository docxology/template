"""Domain detection for research papers.

Automatically detects the scientific domain of a paper (physics, computer science,
biology, mathematics, etc.) to enable domain-specific prompt engineering and
context-aware summarization.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


class PaperDomain(Enum):
    """Scientific domain categories."""
    PHYSICS = "physics"
    COMPUTER_SCIENCE = "computer_science"
    BIOLOGY = "biology"
    MATHEMATICS = "mathematics"
    CHEMISTRY = "chemistry"
    ENGINEERING = "engineering"
    MEDICINE = "medicine"
    MULTIDISCIPLINARY = "multidisciplinary"
    UNKNOWN = "unknown"


class PaperType(Enum):
    """Paper type categories."""
    EXPERIMENTAL = "experimental"
    THEORETICAL = "theoretical"
    REVIEW = "review"
    METHODOLOGY = "methodology"
    CASE_STUDY = "case_study"
    UNKNOWN = "unknown"


@dataclass
class DomainDetectionResult:
    """Result of domain detection analysis."""
    domain: PaperDomain
    confidence: float
    paper_type: PaperType
    type_confidence: float
    indicators: List[str]
    keywords: List[str]


class DomainDetector:
    """Detects scientific domain and paper type from text content.
    
    Uses keyword matching, pattern recognition, and statistical analysis
    to classify papers into domains and types.
    """
    
    # Domain-specific keyword patterns
    DOMAIN_KEYWORDS: Dict[PaperDomain, List[str]] = {
        PaperDomain.PHYSICS: [
            "quantum", "particle", "collision", "energy", "momentum", "velocity",
            "temperature", "pressure", "quark", "gluon", "QCD", "electromagnetic",
            "field", "wave", "oscillation", "resonance", "spectrum", "photon",
            "electron", "proton", "neutron", "atom", "molecule", "nucleus",
            "relativity", "gravity", "dark matter", "dark energy", "cosmology",
            "thermodynamics", "statistical mechanics", "entropy", "phase transition"
        ],
        PaperDomain.COMPUTER_SCIENCE: [
            "algorithm", "complexity", "optimization", "machine learning", "neural network",
            "deep learning", "data structure", "graph", "tree", "hash", "sort",
            "search", "database", "query", "index", "compression", "encoding",
            "distributed", "parallel", "concurrent", "thread", "process", "scheduler",
            "network", "protocol", "routing", "bandwidth", "latency", "throughput",
            "software", "programming", "language", "compiler", "interpreter",
            "artificial intelligence", "AI", "computer vision", "NLP", "natural language"
        ],
        PaperDomain.BIOLOGY: [
            "cell", "protein", "DNA", "RNA", "gene", "genome", "chromosome",
            "enzyme", "metabolism", "organism", "species", "evolution", "phylogeny",
            "ecosystem", "population", "habitat", "biodiversity", "mutation",
            "selection", "adaptation", "morphology", "physiology", "anatomy",
            "tissue", "organ", "membrane", "mitochondria", "nucleus", "ribosome",
            "transcription", "translation", "replication", "expression"
        ],
        PaperDomain.MATHEMATICS: [
            "theorem", "proof", "lemma", "corollary", "proposition", "conjecture",
            "function", "derivative", "integral", "limit", "convergence", "series",
            "matrix", "vector", "tensor", "eigenvalue", "eigenvector", "orthogonal",
            "manifold", "topology", "geometry", "algebra", "group", "ring", "field",
            "polynomial", "equation", "inequality", "optimization", "convex",
            "linear", "nonlinear", "differential", "partial", "ordinary"
        ],
        PaperDomain.CHEMISTRY: [
            "molecule", "atom", "bond", "reaction", "catalyst", "synthesis",
            "compound", "element", "periodic", "valence", "orbital", "electron",
            "ion", "acid", "base", "pH", "equilibrium", "kinetics", "thermodynamics",
            "solvent", "solution", "concentration", "molar", "stoichiometry"
        ],
        PaperDomain.ENGINEERING: [
            "design", "system", "control", "feedback", "signal", "filter",
            "circuit", "transistor", "sensor", "actuator", "robot", "automation",
            "mechanical", "structural", "material", "stress", "strain", "load",
            "efficiency", "performance", "optimization", "simulation", "model"
        ],
        PaperDomain.MEDICINE: [
            "patient", "clinical", "diagnosis", "treatment", "therapy", "disease",
            "symptom", "syndrome", "pathology", "diagnostic", "prognosis",
            "epidemiology", "prevalence", "incidence", "mortality", "morbidity",
            "drug", "medication", "dose", "dosage", "adverse", "side effect"
        ]
    }
    
    # Paper type indicators
    TYPE_INDICATORS: Dict[PaperType, List[str]] = {
        PaperType.EXPERIMENTAL: [
            "experiment", "experimental", "measurement", "measured", "observed",
            "data", "results", "findings", "sample", "trial", "test", "testing",
            "empirical", "observation", "laboratory", "lab", "apparatus", "setup"
        ],
        PaperType.THEORETICAL: [
            "theory", "theoretical", "model", "modeling", "simulation", "derive",
            "derivation", "formulate", "formulation", "framework", "conceptual",
            "hypothesis", "postulate", "assumption", "mathematical", "analytical"
        ],
        PaperType.REVIEW: [
            "review", "survey", "overview", "literature", "state of the art",
            "comprehensive", "systematic", "meta-analysis", "comparison",
            "comparative", "existing", "previous", "prior work", "related work"
        ],
        PaperType.METHODOLOGY: [
            "method", "methodology", "approach", "technique", "algorithm",
            "procedure", "protocol", "framework", "pipeline", "workflow",
            "implementation", "design", "architecture", "strategy"
        ],
        PaperType.CASE_STUDY: [
            "case study", "case", "example", "application", "use case",
            "scenario", "instance", "illustration", "demonstration"
        ]
    }
    
    def detect_domain(
        self,
        text: str,
        title: Optional[str] = None,
        abstract: Optional[str] = None
    ) -> DomainDetectionResult:
        """Detect paper domain and type from text content.
        
        Args:
            text: Full text or significant portion of paper.
            title: Optional paper title (given higher weight).
            abstract: Optional abstract (given higher weight).
            
        Returns:
            DomainDetectionResult with detected domain, type, and confidence.
        """
        # Combine all text sources with weights
        combined_text = ""
        if title:
            combined_text += (title + " ") * 3  # Title weighted 3x
        if abstract:
            combined_text += (abstract + " ") * 2  # Abstract weighted 2x
        combined_text += text
        
        # Normalize text
        text_lower = combined_text.lower()
        
        # Detect domain
        domain_scores: Dict[PaperDomain, float] = {}
        domain_indicators: Dict[PaperDomain, List[str]] = {}
        
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = 0.0
            found_keywords = []
            
            for keyword in keywords:
                # Count occurrences (case-insensitive)
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                matches = len(re.findall(pattern, text_lower))
                
                if matches > 0:
                    score += matches
                    found_keywords.append(keyword)
            
            if score > 0:
                domain_scores[domain] = score
                domain_indicators[domain] = found_keywords
        
        # Determine primary domain
        if domain_scores:
            primary_domain = max(domain_scores.items(), key=lambda x: x[1])[0]
            max_score = domain_scores[primary_domain]
            total_score = sum(domain_scores.values())
            confidence = min(1.0, max_score / max(1, total_score * 0.5))
        else:
            primary_domain = PaperDomain.UNKNOWN
            confidence = 0.0
        
        # Check for multidisciplinary
        if len(domain_scores) > 1:
            top_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)[:2]
            if top_domains[0][1] > 0 and top_domains[1][1] / top_domains[0][1] > 0.5:
                primary_domain = PaperDomain.MULTIDISCIPLINARY
                confidence = 0.7
        
        # Detect paper type
        type_scores: Dict[PaperType, float] = {}
        type_indicators: Dict[PaperType, List[str]] = {}
        
        for paper_type, indicators in self.TYPE_INDICATORS.items():
            score = 0.0
            found_indicators = []
            
            for indicator in indicators:
                pattern = r'\b' + re.escape(indicator.lower()) + r'\b'
                matches = len(re.findall(pattern, text_lower))
                
                if matches > 0:
                    score += matches
                    found_indicators.append(indicator)
            
            if score > 0:
                type_scores[paper_type] = score
                type_indicators[paper_type] = found_indicators
        
        # Determine primary type
        if type_scores:
            primary_type = max(type_scores.items(), key=lambda x: x[1])[0]
            max_type_score = type_scores[primary_type]
            total_type_score = sum(type_scores.values())
            type_confidence = min(1.0, max_type_score / max(1, total_type_score * 0.6))
        else:
            primary_type = PaperType.UNKNOWN
            type_confidence = 0.0
        
        # Collect all indicators
        all_indicators = []
        if primary_domain in domain_indicators:
            all_indicators.extend(domain_indicators[primary_domain])
        if primary_type in type_indicators:
            all_indicators.extend(type_indicators[primary_type])
        
        return DomainDetectionResult(
            domain=primary_domain,
            confidence=confidence,
            paper_type=primary_type,
            type_confidence=type_confidence,
            indicators=all_indicators[:10],  # Limit to top 10
            keywords=list(set(all_indicators))
        )
    
    def get_domain_specific_instructions(self, domain: PaperDomain) -> str:
        """Get domain-specific summarization instructions.
        
        Args:
            domain: Detected domain.
            
        Returns:
            Domain-specific instruction string for prompts.
        """
        instructions = {
            PaperDomain.PHYSICS: (
                "For this PHYSICS paper, emphasize:\n"
                "- Specific equations, formulas, and mathematical relationships\n"
                "- Experimental parameters (energy scales, temperatures, pressures)\n"
                "- Detection methods and measurement techniques\n"
                "- Statistical significance and error analysis\n"
                "- Physical interpretations and theoretical frameworks\n"
                "- Comparison with established theories and experimental data"
            ),
            PaperDomain.COMPUTER_SCIENCE: (
                "For this COMPUTER SCIENCE paper, emphasize:\n"
                "- Algorithms and their complexity analysis (time/space)\n"
                "- Dataset characteristics and experimental setup\n"
                "- Performance metrics and comparisons with baselines\n"
                "- Implementation details and system architecture\n"
                "- Scalability and efficiency considerations\n"
                "- Novel contributions and technical innovations"
            ),
            PaperDomain.BIOLOGY: (
                "For this BIOLOGY paper, emphasize:\n"
                "- Species, organisms, and biological systems studied\n"
                "- Sample sizes and experimental conditions\n"
                "- Statistical methods and significance testing\n"
                "- Biological mechanisms and processes\n"
                "- Experimental protocols and methodologies\n"
                "- Ecological or evolutionary implications"
            ),
            PaperDomain.MATHEMATICS: (
                "For this MATHEMATICS paper, emphasize:\n"
                "- Theorems, proofs, and mathematical structures\n"
                "- Key definitions and notation\n"
                "- Computational complexity and algorithmic aspects\n"
                "- Theoretical implications and applications\n"
                "- Connections to other mathematical areas\n"
                "- Rigor and mathematical precision"
            ),
            PaperDomain.CHEMISTRY: (
                "For this CHEMISTRY paper, emphasize:\n"
                "- Chemical reactions and mechanisms\n"
                "- Molecular structures and bonding\n"
                "- Experimental conditions and synthesis methods\n"
                "- Analytical techniques and characterization\n"
                "- Reaction yields and selectivity\n"
                "- Theoretical models and computational methods"
            ),
            PaperDomain.ENGINEERING: (
                "For this ENGINEERING paper, emphasize:\n"
                "- System design and architecture\n"
                "- Performance metrics and efficiency\n"
                "- Materials and components used\n"
                "- Testing and validation methods\n"
                "- Practical applications and use cases\n"
                "- Optimization strategies and trade-offs"
            ),
            PaperDomain.MEDICINE: (
                "For this MEDICINE paper, emphasize:\n"
                "- Clinical study design and methodology\n"
                "- Patient demographics and sample sizes\n"
                "- Diagnostic or treatment protocols\n"
                "- Statistical analysis and significance\n"
                "- Safety and efficacy outcomes\n"
                "- Clinical implications and recommendations"
            )
        }
        
        return instructions.get(domain, "Standard scientific paper summarization guidelines apply.")

