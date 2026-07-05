# Pools, Rules, and Tools: A Template-Integrated Resource Architecture

**A Meta-Project Demonstrating Fonds, Rules, and Tools Integration in Research Software**

---

| Field | Value |
|---|---|
| **Authors** | Research Template Author¹, Template Collaborator¹ |
| **Affiliation** | ¹ Active Inference Institute |
| **Correspondence** | author@research-template.org |
| **Version** | 1.0.0 |
| **Date** | 2026-07-05 |
| **License** | CC-BY-4.0 |
| **Repository** | [docxology/template](https://github.com/docxology/template) |
| **DOI** | 10.5281/zenodo.template_pools_rules_tools |
| **Keywords** | research software engineering, monorepo architecture, reproducibility, fonds, governance rules, tool discovery, graceful degradation |

---

## Author Contributions

**Research Template Author**: Conceptualisation, architecture design, module implementation (`fonds_reader`, `rules_applier`, `tools_invoker`, `integration`), manuscript writing (all sections), validation.

**Template Collaborator**: Manuscript review, test suite design, exemplar resource authoring (fonds, rules, tools).

## Acknowledgements

The authors thank the Active Inference Institute for hosting the public template repository and providing the infrastructure within which this exemplar was developed. The design of the three-layer resource architecture draws inspiration from the Unix philosophy [@Raymond2003art] and the enterprise application patterns documented by [@Fowler2002patterns].

## Data Availability

All source code, configuration files, and exemplar resources described in this paper are available in the public template repository at <https://github.com/docxology/template> under the `projects/templates/template_pools_rules_tools/` path. The integration pipeline is fully reproducible from source using `uv run python projects/templates/template_pools_rules_tools/scripts/02_run_integration.py` from the repository root. Generated manuscript variables are stored in `output/data/manuscript_variables.json` and injected at render time.

## Competing Interests

The authors declare no competing interests.
