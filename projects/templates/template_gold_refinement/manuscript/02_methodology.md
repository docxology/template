# {{TITLE_METHODOLOGY}} {#sec:methodology}

The refinery pipeline consists of {{REFINERY_NUM_STAGES}} canonical stages, each mapping a metallurgical operation to a manuscript-composition operation. The pipeline is implemented in `src/refinery.py` and validated by `src/purity.py`.

## Stage definitions

| # | Stage | Output purity | Karat | Metallurgical operation |
|---|-------|-------------|-------|------------------------|
{{STAGE_TABLE_ROWS}}

## Purity progression

The purity sequence across all stages is: {{PURITY_SEQUENCE}}

Purity is strictly increasing — enforced by `assert_monotone_increase()` which raises `ValueError` if any stage's output purity does not exceed its input. Formally, for stages $s_1, \ldots, s_n$ with input purity $p_{\text{in}}^{(i)}$ and output purity $p_{\text{out}}^{(i)}$:

$$
p_{\text{out}}^{(i)} > p_{\text{in}}^{(i)} \quad \text{and} \quad p_{\text{in}}^{(i+1)} = p_{\text{out}}^{(i)} \quad \forall i \in \{1, \ldots, n-1\}
$$

The full purity progression is shown in [@fig:purity_progression] (see [@sec:results]).

## Token selection

The mega-madlib engine selects tokens from config-owned lexicon categories using a deterministic digest:

$$
\text{index} = \text{int}\left(\text{SHA-256}\left(\text{seed} \mid \text{slot} \mid \text{category} \mid \text{ordinal} \mid \text{inventory}\right)[:12], 16\right) \mod n
$$

where $n$ is the size of the lexicon category inventory. Selected metallurgical terms: {{METHOD_METAL_TERM_1}}, {{METHOD_METAL_TERM_2}}, {{METHOD_METAL_TERM_3}}. Selected manuscript terms: {{METHOD_MANUSCRIPT_TERM_1}}, {{METHOD_MANUSCRIPT_TERM_2}}.

## Config-owned lexicon

| Category | Count | Sample |
|----------|-------|--------|
{{LEXICON_TABLE}}

## Karat grading

Karat grades map purity fractions to standard gold fineness:

- 9K = 37.5% (ore stage)
- 18K = 75.0% (smelting stage)
- 22K = 91.67% (assaying stage)
- 24K = 99.9% (cupellation stage)
- Nine-nines = 99.9999999% (certification stage)

The mapping is implemented in `src/purity.py::karat_for_purity()`. The karat grading chart is shown in [@fig:karat_grading] (see [@sec:results]).

## Pipeline phases

| Phase | Input | Transformation | Output | Guard |
|-------|-------|----------------|--------|-------|
{{PIPELINE_PHASES_TABLE}}
