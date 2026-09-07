# Manuscript — template_pools_rules_tools

Integration manuscript for fonds, rules, and tools. Counts inject from
`output/data/manuscript_variables.json` at render time. Never hand-author
total/content/cover figure counts: the generator derives them from the content
figure registry and separate cover-asset contract.

Keep level-two headings plain-text and concise. Pandoc may wrap headings with
inline code across lines; the Beamer frame splitter then cannot safely reuse the
multi-line title for continuation frames.

## See also

- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](README.md)
- [`figures/AGENTS.md`](figures/AGENTS.md)
