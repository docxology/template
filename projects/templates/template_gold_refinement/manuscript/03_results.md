# {{TITLE_RESULTS}} {#sec:results}

The refinery pipeline produces a monotonically increasing purity sequence across {{REFINERY_NUM_STAGES}} stages, reaching final purity of {{REFINERY_FINAL_PURITY}} ({{REFINERY_FINAL_KARAT}}).

## Purity progression

{{FIGURE_PURITY_PROGRESSION}}

| Stage | Name | Output purity | Karat | Gain |
|-------|------|--------------|-------|------|
{{STAGE_TABLE_ROWS}}

## Karat grading scale

{{FIGURE_KARAT_GRADING}}

## Final certification

- **Final purity:** {{REFINERY_FINAL_PURITY}}
- **Final karat:** {{REFINERY_FINAL_KARAT}}
- **Total purity gain:** {{REFINERY_TOTAL_GAIN}}
- **Nine-nines certified:** {{REFINERY_IS_CERTIFIED}}
- **Nines count:** {{REFINERY_FINAL_NINES}}

## Token plan summary

The mega-madlib engine generated {{TOKEN_COUNT}} tokens from seed {{TOKEN_SEED}} across {{CONFIG_NUM_LEXICON_CATEGORIES}} lexicon categories.

{{FIGURE_TOKEN_DENSITY}}

### Category distribution

| Category | Count |
|----------|-------|
{{TOKEN_CATEGORY_TABLE}}

### Section distribution

| Section | Token count |
|---------|-----------|
{{TOKEN_SECTION_TABLE}}

### Provenance trace

| Variable | Category | Value | Section | Source |
|----------|----------|-------|---------|--------|
{{TOKEN_PROVENANCE_TABLE}}

Selected purity adjectives for this section: {{RESULTS_PURITY_ADJ_1}}, {{RESULTS_PURITY_ADJ_2}}.

## Provenance flow

{{FIGURE_PROVENANCE_SANKEY}}

## Purity vs claim support

{{FIGURE_PURITY_CLAIM_SCATTER}}

## Token selection sensitivity

{{FIGURE_TOKEN_HEATMAP}}

## Contribution claims

| Claim | Statement | Evidence | Boundary |
|-------|-----------|----------|----------|
{{CONTRIBUTION_CLAIMS_TABLE}}
