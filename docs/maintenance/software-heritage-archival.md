# Software Heritage archival — docxology repositories

> Status snapshot: 2026-06-27. Records which docxology public repositories have been
> submitted to the Software Heritage (SWH) "Save code now" archive, which remain, and
> how to finish + verify. Scope agreed: **docxology's own public repos (software +
> papers)** — forks and private repos are excluded (see rationale below).

## How SWH archival works here

- **SWH continuously auto-harvests public GitHub.** Every public docxology repo will
  be archived over time with no action. "Save code now" only **expedites a fresh
  snapshot** of a specific repo.
- **Submission channel:** the public form at <https://archive.softwareheritage.org/save/>
  (origin type `git`, the repo's `.git` clone URL). No account needed; an automatic
  browser proof-of-work (Anubis) clears transparently.
- **Anonymous rate limit.** SWH throttles anonymous "Save code now" to a small burst —
  ~10–12 requests before returning *"The rate limit for 'save code now' requests has
  been reached."* The window resets after a cool-down (≈1 hour). **Logging in to SWH
  raises the limit substantially**, which is the fastest way to submit the full set.
- **Verify a repo** at: `https://archive.softwareheritage.org/browse/origin/?origin_url=<repo-url>`
  (a freshly *accepted/pending* request 404s here until the scheduled visit completes).

## Submitted this session — accepted/pending (11)

Confirmed in the live save-requests queue (status `accepted` → `pending` visit):

| Repo | Type |
| --- | --- |
| `template` | framework |
| `template_active_inference` | exemplar |
| `template_autoresearch_project` | exemplar |
| `template_autoscientists` | exemplar |
| `template_code_project` | exemplar |
| `template_gold_refinement` | exemplar |
| `template_literature_meta_analysis` | exemplar |
| `template_madlib` | exemplar |
| `template_newspaper` | exemplar |
| `template_prose_project` | exemplar |
| `democreate` | software |

Verify the queue at <https://archive.softwareheritage.org/save/list/> (sorted by date;
these appear at/near the top) or per-repo via the browse URL above once visits complete.

## Remaining own public repos to submit (rate-limited — queue when the window resets)

**Template exemplars:** `template_sia`, `template_template`, `template_textbook`,
`template_bioinformatics_project`

**Original software:** `codomyrmex`, `entofile`, `steganographer`, `dotscope`,
`ivm-xyz`, `QuadCraft`, `QuadMath`, `timeline_generator`, `opentir`, `coasys`, `p3if`,
`active-inference-pocket-lab`, `CogSecSkills`, `qr_live_protocol`, `hhs-opendata`,
`crescent-city`, `sunspot`, `godel_ivm`, `active_inference`, `active_torchference`,
`markdown_decision_process`, `course`, `links`, `multi-time`, `snake`, `transformer`

**Scholarly / paper / Zenodo-linked:** `itrace` (Zenodo DOI 10.5281/zenodo.20614908),
`grateful_data`, `cohereants`, `crescent_city`, `blake_jiang`, `ntqr_llm`,
`ento_linguistics`, `realizing_emptiness`, `biology_textbook`, `cognitive_case_diagrams`,
`docxology`, `MetaInformAnt`, `BeeStack`, `AGEINT`, `ant_stack`, `biol-1`, `biol-8`,
`literature`, `curriculum`, `institute_website`

Submission URL pattern for each: `https://github.com/docxology/<name>.git`

## Excluded — by design

- **Forks** (e.g. `pymdp`, `flybody`, `cogames`, `TradingAgents`, `RxInferExamples.jl`,
  `spm`, `Ludii`, `ngc-learn`, and ~40 more): these are other authors' projects; SWH
  archives the upstream originals already. Not "docxology software." Can be added on
  request.
- **Private repos** (`projects`, `alphacogant`, `instituteos`, `CA_public_records`, the
  many `*-private` mirrors, etc.): SWH can only archive **public** origins. Making a repo
  public is a deliberate access-control decision left to you — not something done here.

## How to finish the remaining ~50

Pick one:

1. **Log in to SWH** (top-right "login", e.g. via GitHub OIDC) — authenticated save
   requests have a much higher rate limit; the full list can then go in one pass.
2. **Throttle over time** — submit ~10 per hour anonymously across the day.
3. **Do nothing** — SWH's automatic GitHub harvesting will archive all public repos
   eventually; the manual saves above just expedite the most important ones first.

## Method notes (for reproducing)

- The save form's JS validation requires **real keystrokes** in the Origin URL field;
  setting the value programmatically (DOM `value`) submits an empty/invalid request that
  silently no-ops. Use focus + type + click Submit, and confirm the green
  *"request has been accepted"* banner before the next entry.
- A red banner = rate limit reached → stop and wait for the cool-down.
