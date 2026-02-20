# LLM-Based Assertion Extraction: Prompt Design, Error Taxonomy, and Validation \label{sec:extraction_pipeline}

_This supplementary section documents the implementation specifics of the LLM-based assertion extraction pipeline._

## Relationship to Prior Approaches

The closest prior effort is the systematic literature analysis of Knight, Cordes, and Friedman \citep{knight2022fep}, which used human annotators to manually code structural, visual, and mathematical features of FEP and Active Inference publications. Their work operated at the scale of hundreds of annotated papers and employed terms from the Active Inference Institute's Active Inference Ontology for automated text analysis. Our pipeline replaces the manual coding step with LLM-based assertion extraction, enabling scalable processing of the full corpus ($N = 1208$ papers) at the cost of exchanging human-verified precision for machine-generated assessments that require post-hoc validation.

| Dimension | Knight et al. (2022) | This work |
|-----------|---------------------|-----------|
| **Scale** | Hundreds of papers | 1208 papers |
| **Annotation** | Manual (structural/visual/math features) | Automated (LLM hypothesis assessment) |
| **Ontology** | Active Inference Ontology terms | 8 standard hypotheses |
| **Output** | Annotated features + term frequencies | Nanopublications + knowledge graph |
| **Reproducibility** | Annotator-dependent | Deterministic (given model + seed) |
| **Precision** | High (human-verified) | Medium (requires validation) |

## Prompt Engineering and Schema Design

The structured prompt is designed to minimize parsing failures and maximize assessment quality:

1. **Explicit JSON schema.** The prompt specifies the exact output schema—field names, allowed direction values, and the numeric confidence range—reducing the LLM's tendency to generate free-form text or ad hoc structures.

2. **Hypothesis definitions in-context.** All eight definitions are included verbatim, ensuring the LLM assesses relevance from the provided context rather than relying on parametric knowledge that may be stale.

3. **Reasoning field.** Each assessment includes a natural-language reasoning string, providing an audit trail for human reviewers and enabling systematic analysis of error patterns.

4. **Irrelevant filtering.** An explicit "irrelevant" direction allows the LLM to mark hypotheses that a paper does not address, avoiding forced spurious assessments.

### Prompt Template

The extraction prompt follows a two-part structure (system + user):

```text
SYSTEM: You are a scientific literature analyst specializing in the
Free Energy Principle and Active Inference. Assess the relevance of
the given paper to each hypothesis. Return a JSON array.

USER:
Paper: {title}
Abstract: {abstract}

Hypotheses:
H1: FEP Universality — {description}
H2: AIF Optimality — {description}
...
H8: Language AIF — {description}

For each hypothesis, return:
{
  "hypothesis_id": "H1",
  "direction": "supports|contradicts|neutral|irrelevant",
  "confidence": 0.0-1.0,
  "reasoning": "..."
}
```

The extraction module (`src/knowledge_graph/llm_extraction.py`) includes configurable retry logic with exponential backoff, JSON parsing with handling of markdown code fences and extraneous text, confidence clamping, and validation against the hypothesis ID set. The default model is `gemma3:4b` on a local Ollama instance, configurable via `--llm-model` and `--llm-url` flags.

## Failure Modes and Error Recovery

The primary failure modes are documented below.

### Over-Extraction Bias

Approximately 15--20\% of assessments in preliminary experiments exhibit over-extraction: the LLM attributes claims to a paper that merely mentions a hypothesis without taking a position. This is the most common error mode and produces false supporting evidence.

### Direction Misclassification

The LLM misclassifies a contradicting claim as supporting, or vice versa. Rarer but more consequential, as it directly inverts the evidence signal. Most common for papers that discuss limitations while ultimately endorsing a hypothesis.

### Confidence Calibration Constraints

The model occasionally assigns high confidence to assessments where the underlying semantic evidence is demonstrably weak or ambiguous. Reliable confidence calibration remains an open research problem across nearly all zero-shot LLM applications, necessitating the multi-tiered validation protocols described below.

### Progressive JSON Parsing Recovery

To mitigate formatting inconsistencies, the module implements a progressive parsing pipeline to recover malformed LLM outputs:

1. **Direct parse**: Attempt `json.loads()` on the raw response.
2. **Strip code fences**: Remove Markdown `` ```json ... ``` `` wrappers and retry.
3. **Extract JSON array**: Scan for the first `[...]` substring in the response text.
4. **Individual recovery**: If a valid array contains malformed elements, parse each element independently.

Papers that fail all parsing stages are logged and skipped; their count is reported at pipeline completion.

## Validation Methodology

Validation of LLM-extracted assertions follows a three-tier protocol:

1. **Spot-check validation.** A random sample of 50 papers is reviewed by a domain expert, comparing LLM assessments against human judgments for direction accuracy and confidence appropriateness.

2. **Boundary-case audit.** Papers known to make contested claims (e.g., critiques of FEP universality, Markov blanket realism debates) are specifically checked for correct direction assignment.

3. **Aggregate consistency.** Hypothesis scores are compared against qualitative expectations from the literature: hypotheses known to be well-supported (e.g., H4 Predictive Coding) should score positively; those known to be contested (e.g., H3 Markov Blanket Realism) should show lower or mixed scores.

Preliminary experiments on a sampled subset of Active Inference papers—evaluated across GPT-4 and Claude-family models—suggest that this automated approach reduces human annotation time by approximately 60--70\% compared to purely manual extraction. Both over-extraction biases and direction inversion errors are consistently intercepted by human review at acceptable rates. Structurally, the pipeline is designed for seamless proprietary or open-weight model upgrades: swapping the underlying reasoning engine requires only adjusting the `--llm-model` flag.
