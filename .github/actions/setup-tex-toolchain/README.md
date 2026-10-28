# setup-tex-toolchain

Composite action: the cached `xelatex` + `bibtex` provisioning shared by the two
lanes that compile documents with the extended LaTeX package set.

```yaml
- uses: ./.github/actions/setup-tex-toolchain
```

It is two steps, in the order both callers already used:

1. `actions/cache` (pinned `v6.1.0`) over `/var/cache/apt`,
   `/usr/share/texlive`, and `/usr/share/texmf` under the key
   `texlive-<os>-xetex-extra-bibtex-fonts-v1`.
2. On a cache miss, `apt-get install` of `texlive-xetex texlive-latex-extra
   texlive-bibtex-extra texlive-fonts-recommended lmodern`.

Callers:

| Caller | Why |
| --- | --- |
| [`hardening.yml`](../../workflows/hardening.yml) `test-infra-slow` | the slow-marked lane compiles bibliographies |
| [`release-rehearsal.yml`](../../workflows/release-rehearsal.yml) `rehearsal` | fresh-checkout rehearsal compiles the same documents |

Both callers previously carried byte-identical copies of these steps, so they are
now defined once. The `ci.yml` TeX steps stay inline — they are **not** identical:
the `test-infra` step installs `texlive-xetex lmodern texlive-fonts-recommended`
and probes `article.cls`/`pzdr.tfm`, while `test-contract` installs the wider
`texlive-latex-extra` + `poppler-utils` set and probes `plainnat.bst`,
`seqsplit.sty`, and `lmodern.sty`. Parameterising one action across those distinct
scopes would hide which lane prepares which package.

## Editing

- The cache key is shared: bumping it invalidates both lanes together, which is
  intended — they must compile against the same package set.
- Keep the install conditional on `cache-hit`; an unconditional `apt-get install`
  would undo the cache.
- Do not add the ci.yml package probes here; they belong to their own lanes.
- Run `actionlint` after edits and keep the sibling README/AGENTS pair current.
