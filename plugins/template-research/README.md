# Template Research

Review a draft manuscript, check what its evidence actually supports, and describe what an independent reader could reproduce. Template Research brings three review workflows from the [Research Project Template](https://github.com/docxology/template) into Claude. Researchers, research software engineers, and reviewers can work from short excerpts pasted directly into a chat. The plugin works with manuscripts from any authoring system.

| Skill | Output |
| --- | --- |
| **Review manuscript excerpt** | Prioritized editorial findings and suggested wording for an abstract, results, or limitations section. |
| **Map claims to evidence** | A table linking each claim to supplied evidence, marking partial support, contradictions, and gaps. |
| **Write reproducibility disclosure** | A short statement of what can be reused or reproduced, with a checklist of missing evidence. |

## Try it

These prompts use fictional research examples. Paste one into a new chat with the plugin enabled.

1. **Editorial review**

   > Review these excerpts for consistency and suggest a revised abstract sentence. Abstract: “The shading treatment improved seedling survival across all sites.” Results: “In two nursery plots, survival rose from 70% to 80% in Plot A and stayed at 77% in Plot B.” Limitations: “Both plots used the same cultivar and were observed for four weeks.”

   Look for a finding that anchors the overstatement in the two excerpts and proposed wording that scopes the observed increase to Plot A.

2. **Claim–evidence map**

   > Map each claim to the supplied evidence. Claims: “The prototype’s median drying time was 20% lower than the control’s over the 30-day evaluation” and “The method lowered operating costs.” E1, Table 2: “Control median 50 min, prototype median 40 min, same 30-day evaluation period, 16 batches per group.” E2, Appendix A: “The study recorded energy use. Pricing and labor were outside the study scope.”

   Look for the supplied comparison and denominator on the first row and the missing cost evidence on the second.

3. **Reproducibility disclosure**

   > Draft a reproducibility statement from these records. Candidate R1 uses source revision alpha-7, fixture F1 and an environment lock labeled L1. Two clean runs report exit status 0 and the same SHA-256 for Figure 2. The replay instructions, archived fixture location, and result checks for Table 1 were omitted.

   Look for a disclosure that gives the authors' reported evidence its proper scope and identifies the missing replay and Table 1 evidence.

## Privacy policy

Each workflow uses excerpts you deliberately paste into the current request. These may include public author names or other public attribution relevant to reviewing a citation or manuscript. Paste only the relevant text and remove confidential material and unnecessary personal details.

Claude processes the excerpts and generates the answer in the conversation. The plugin has no separate storage, retention, or telemetry. It does not access files, uploads, other conversations, websites, or connected services, and it does not send content to docxology or any off-platform destination. The [Anthropic Privacy Policy](https://www.anthropic.com/legal/privacy), or the terms and settings for your organization’s Claude account, govern the conversation. The plugin is intended for adult researchers and reviewers.

## Troubleshooting

- If Claude does a general copy edit, ask for the named skill and paste the relevant sections with labels such as `Abstract` and `Results`.
- If a claim is marked `Not shown`, add a short source excerpt with its section, table, row, or figure label. A citation identifier alone leaves source support unchecked.
- If a disclosure lists a check as missing, paste the matching run-summary lines and identify the revision and the artifact those lines describe. A release label or a successful run alone leaves artifact identity unresolved.

For usage questions and bugs, use [GitHub Issues](https://github.com/docxology/template/issues) with a minimal synthetic example and plugin version. Report vulnerabilities through [GitHub private vulnerability reporting](https://github.com/docxology/template/security/advisories/new). The [repository security policy](https://github.com/docxology/template/security/policy) describes the fallback route.

## Provenance and license

The chat workflows adapt Template’s [manuscript claim verification](https://github.com/docxology/template/blob/main/docs/prompts/manuscript-claim-verification/SKILL.md), [reproducibility audit](https://github.com/docxology/template/blob/main/docs/prompts/reproducibility-audit/SKILL.md), and [release evidence guidance](https://github.com/docxology/template/blob/main/docs/maintenance/release-boundary.md). The upstream command-line workflows and build system are available from the repository. The plugin is licensed under the [Apache License 2.0](LICENSE).
