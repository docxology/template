# content/ — the edition

This is the newspaper, as data. The engine reads it; it contains no code.

```
content/
  edition.yaml        masthead + render settings + ordered page list
  pages/
    00_front_page.yaml … 11_weather_almanac.yaml   one file per page
```

Edit these files to change the paper — see [`../docs/syntax_guide.md`](../docs/syntax_guide.md)
for the complete schema and [`../docs/forking_guide.md`](../docs/forking_guide.md)
to turn it into a different title.

> Template edition: all stories, names and events here are illustrative and
> fictional; the masthead is homage to the real Crescent City *Triplicate*.

The manifest's `pages` entries are resolved strictly beneath `content/pages/`;
absolute paths, `..` escapes, duplicate file references, and missing files are
rejected before any page is rendered. Page YAML also requires list-shaped
`rail`/`main` sections and unique positive folio numbers. This keeps a typo or
untrusted manifest from producing a plausible PDF with missing or overwritten
pages.
