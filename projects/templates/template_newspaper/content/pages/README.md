# `template_newspaper/content/pages/`

One YAML file per printed page, listed in print order by
[`../edition.yaml`](../edition.yaml). These files are pure data — the layout
engine in [`../../src/newspaper/`](../../src/newspaper/) reads them; they contain
no code. Edit them to change the paper.

## Files

| File | Role |
| --- | --- |
| `00_front_page.yaml` | Front page: nameplate, lead story, above-the-fold furniture. |
| `01_local_region.yaml` | Local and regional news. |
| `02_government.yaml` | Government and civic affairs. |
| `03_coast_environment.yaml` | Coast and environment. |
| `04_opinion.yaml` | Opinion and editorial. |
| `05_business_fishing.yaml` | Business and the fishing economy. |
| `06_community_arts.yaml` | Community and arts. |
| `07_sports.yaml` | Sports. |
| `08_education.yaml` | Education. |
| `09_record_obituaries.yaml` | The record and obituaries. |
| `10_classifieds.yaml` | Classifieds. |
| `11_weather_almanac.yaml` | Weather and almanac. |

Each file declares a page template plus the stories, boxes, figures and tables
that fill it. Unknown templates or box kinds are rejected at load time with an
error naming the offending value and the allowed set.

## See Also

- [`../README.md`](../README.md) — the edition as data
- [`../AGENTS.md`](../AGENTS.md) — content editing rules
- [`../../docs/syntax_guide.md`](../../docs/syntax_guide.md) — the complete page schema
