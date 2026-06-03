# Edition Content Syntax

An edition is defined entirely by YAML under `content/`. This is the complete
schema. The loaders (`src/newspaper/content.py`, `src/newspaper/config.py`) are
**strict**: unknown keys and invalid enum values raise errors that name the
offending value and the allowed set.

## `content/edition.yaml`

```yaml
masthead:
  nameplate: "The Triplicate"     # required — the big title
  city: "Crescent City"           # required
  state: "California"             # required
  date: "Wednesday, May 27, 2026" # required — printed verbatim
  motto: "Serving ... since 1879" # optional — italic line under the nameplate
  established: "1879"             # optional — left ear
  volume: "147"                   # optional — folio line
  number: "21"                    # optional — folio line
  price: "$1.50"                  # optional — folio line, right
  edition_label: "North Coast Edition"  # optional — folio line
  weather_strip: |                # optional — right ear; newlines → line breaks
    TODAY: Morning fog, 59°
    Full almanac — Page A12

render:                           # all keys optional; validated strictly
  output_basename: "the-triplicate"   # → output/pdf/<basename>.pdf
  page: "tabloid"               # tabloid | broadsheet | berliner | letter
  columns_default: 5            # main columns when a page omits `columns`
  gutter_inches: 0.16
  rail_inches: 1.55             # width of the optional left rail
  figures_dir: "output/figures"
  draft_grid: false             # true → draw frame outlines (debug)
  spot_color: false             # true → colored masthead + section labels
  spot_hex: "#9E1B32"           # the spot color used when spot_color is on

pages:                            # ordered list of page files (print order)
  - 00_front_page.yaml
  - 01_local_region.yaml
  # ...
```

## `content/pages/<name>.yaml`

```yaml
number: 1                  # page number (prints in the folio)
section: "A"               # section letter (folio: A1, A2, ...)
department: "Front Page"   # printed in the section banner (inside pages)
template: "front"          # front | standard | opinion | feature | classified
columns: 4                 # number of MAIN columns (rail is extra)
rail_enabled: true         # optional; usually implied by presence of `rail:`

rail:                      # optional — items for the narrow left rail
  - { box: index, ... }
  - { box: weather, ... }

lead:                      # optional — the page's lead story; its headline is
  headline: "..."          #   drawn SPANNING the main columns as furniture
  ...                      #   (see Story fields below)

main:                      # ordered list of items flowed through the columns
  - { headline: "...", ... }   # a Story
  - { box: briefs, ... }       # a Box
  - { figure: { ... } }        # a standalone Figure
```

### Story

```yaml
headline: "Council adopts budget"   # required
kicker: "City Council"              # optional — small caps label above
deck: "A $48.6M plan ..."           # optional — italic subhead
byline: "By Maren Holloway"         # optional
dateline: "CRESCENT CITY"           # optional
level: secondary                    # lead | primary | secondary | minor
drop_cap: true                      # optional — raised initial on 1st paragraph
figure:                             # optional — see Figure
  path: "output/figures/harbor.png"
  caption: "..."
  credit: "Triplicate / J. Okafor"
  height: 168
body:                               # list of blocks (see below)
  - "A plain string is a paragraph."
  - { subhead: "A bold subhead" }
  - { pull: { quote: "Pulled text.", by: "Speaker" } }
jump: "Continued on Page A4"        # optional — italic jump line
```

Inline markup inside any text: ReportLab mini-HTML — `<b>`, `<i>`, `<br/>`.

`level` controls the headline size: `lead` (44pt, used as a spanning headline
when set as a page's `lead:`), `primary` (23pt), `secondary` (17pt),
`minor` (12.5pt). On single-column flow, prefer `secondary`/`minor`.

### Box (modular units)

```yaml
- box: index | weather | tides | staff | briefs | table | calendar |
       almanac | generic | display
  title: "Inside Today"
  items: ["string", "..."]          # used by index / staff / generic / classified
  rows:  [["c1","c2"], ["..."]]     # used by table / weather / tides / almanac
  columns: ["Head1", "Head2"]       # optional table header row
  body:  ["paragraphs", {subhead: "..."}]   # used by weather/briefs/generic
  footnote: "small print"
```

On a `classified` page, every box **except** `display` is rendered as dense,
unboxed, splittable copy (so a long classifieds section packs and flows across
columns); a `display` box keeps its border (house/display ads).

### Figure

```yaml
figure:
  path: "output/figures/harbor.png"  # required; relative to project root
  caption: "Cutline text."
  credit: "Triplicate / J. Okafor"
  height: 168                        # > 0; placeholder height hint
```

The image is fit to the width of the column it flows into. A missing `path`
**file** degrades to a labelled gray placeholder — never an error — but an
*omitted* `path` field or a non-positive `height` is a load-time `ValueError`.
Figures may not appear in the `rail`. Multi-column spanning is not supported by
the flow model. Figure images may be **color** — any RGB PNG renders in full
color.

### Ad (display advertisement)

Newspapers are monochrome news wrapped around **color advertising**. A display
ad flows like a boxed module on any page (and in the rail) and is fully
color-capable:

```yaml
- ad:
    sponsor: "Foglight Bakery"           # required — advertiser name (big)
    tagline: "Fresh from the fog."        # optional — italic line
    graphic: "output/figures/ad_bakery.png"  # optional color logo/illustration
    background: "#F8EFD9"                 # optional hex tint (empty = white)
    accent: "#6E3C18"                    # optional hex for border + sponsor name
    border: "double"                     # box | double | thick | none
    graphic_height: 78                   # logo height hint (points)
    height: 0                            # optional fixed ad height (0 = natural)
    body:                                # optional centered copy lines
      - "Sourdough · pastries · wood-fired loaves"
    contact: "(707) 555-0210"            # optional bold accent-colored line
```

Ads carry an automatic "ADVERTISEMENT" label and centered copy. Like boxes, an
ad is a non-splitting flowable — an over-tall ad is reported as over-set, not
silently shrunk. A missing `sponsor` or an unknown `border` is a `ValueError`.

### Color & spot color

- **Color images / ads:** point any `graphic`/`figure` `path` at an RGB PNG. The
  shipped `ad_bakery` / `ad_realty` / `ad_grocery` / `ad_festival` graphics are
  procedural color examples; the festival banner doubles as a creative-color
  showcase.
- **Spot color:** set `render.spot_color: true` (with optional `spot_hex`) to
  print the nameplate, section labels and heavy band rules in a spot color — the
  classic colored-flag look. Off by default (the elegant black flag).

## Validation cheatsheet

| Mistake | Error you'll see |
|--------|------------------|
| unknown `render` key | `Unknown render key(s) in config: [...]. Allowed: [...]` |
| `template: gazette` | `unknown template 'gazette'; allowed: [...]` |
| `level: huge` | `unknown story level 'huge'; allowed: [...]` |
| `box: widget` | `unknown box kind 'widget'; allowed: [...]` |
| figure in `rail` | `figures are not allowed in the rail` |
| `ad:` without `sponsor` | `ad requires a 'sponsor' field; got keys [...]` |
| `border: glow` | `unknown ad border 'glow'; allowed: [...]` |
| missing page file | `page file referenced by manifest not found: ...` |
