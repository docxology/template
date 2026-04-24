-- _beamer_allowframebreaks.lua
--
-- Pandoc Lua filter applied during Beamer rendering. It tags every
-- top-level (h1) and second-level (h2) heading with the
-- ``allowframebreaks`` class, which Pandoc's Beamer writer turns into
-- ``\begin{frame}[allowframebreaks]``. Without this, a long section
-- whose markdown source has no h2 sub-breaks gets wrapped in a single
-- frame, produces an overfull vbox in xelatex, and the driver returns
-- code 256 — leaving a 15-byte PDF stub on disk.
--
-- The filter is intentionally tiny and stateless so it can be applied
-- to any Beamer build without coordination with the source markdown.

function Header(elem)
  if elem.level <= 2 then
    table.insert(elem.classes, 'allowframebreaks')
  end
  return elem
end
