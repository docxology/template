-- _beamer_allowframebreaks.lua
--
-- Pandoc Lua filter applied during Beamer rendering. It tags every
-- heading through h4 with the
-- ``allowframebreaks`` class, which Pandoc's Beamer writer turns into
-- ``\begin{frame}[allowframebreaks]``. Without this, a long section
-- whose markdown source has no h2 sub-breaks gets wrapped in a single
-- frame, produces an overfull vbox in xelatex, and the driver returns
-- code 256 — leaving a 15-byte PDF stub on disk.
--
-- The filter is intentionally tiny and stateless so it can be applied
-- to any Beamer build without coordination with the source markdown. The
-- renderer chooses slide-level 2--4 from the source; tagging through h4
-- keeps whichever heading is producing frames breakable.

function Header(elem)
  if elem.level <= 4 then
    table.insert(elem.classes, 'allowframebreaks')
  end
  return elem
end

-- Long flat tables cannot break inside Beamer's alignment boxes. Paginate
-- whole rows before serialization, repeating the complete header. Unknown
-- spans, multiple bodies, intermediate heads, and footers retain their input.
local function plain_inlines(inlines)
  for _, inline in ipairs(inlines) do
    if inline.t == 'Emph' or inline.t == 'Strong' or inline.t == 'Link' then
      if inline.attr and inline.attr.identifier ~= '' then return false end
      if not plain_inlines(inline.content) then return false end
    elseif inline.t ~= 'Str' and inline.t ~= 'Space' and inline.t ~= 'SoftBreak'
        and inline.t ~= 'LineBreak' and inline.t ~= 'Code' then
      return false
    elseif inline.attr and inline.attr.identifier ~= '' then
      return false
    end
  end
  return true
end

local function flat_rows(rows, columns)
  for _, row in ipairs(rows) do
    if #row.cells ~= columns or row.attr.identifier ~= '' then return false end
    for _, cell in ipairs(row.cells) do
      if cell.row_span ~= 1 or cell.col_span ~= 1
          or cell.attr.identifier ~= '' then return false end
      for _, block in ipairs(cell.contents) do
        if (block.t ~= 'Plain' and block.t ~= 'Para')
            or not plain_inlines(block.content) then return false end
      end
    end
  end
  return true
end

local function paginate_table(elem)
  local limit = 8
  if #elem.colspecs == 0 or #elem.bodies ~= 1 or #elem.foot.rows ~= 0 then return nil end
  local body = elem.bodies[1]
  if #body.head ~= 0 or #body.body <= limit or body.row_head_columns ~= 0
      or body.attr.identifier ~= '' or elem.head.attr.identifier ~= ''
      or elem.foot.attr.identifier ~= '' then return nil end
  if not flat_rows(elem.head.rows, #elem.colspecs)
      or not flat_rows(body.body, #elem.colspecs) then return nil end
  local blocks = pandoc.List()
  for first = 1, #body.body, limit do
    if first > 1 then blocks:insert(pandoc.RawBlock('latex', '\\framebreak')) end
    local part = elem:clone()
    local rows = pandoc.List()
    for index = first, math.min(first + limit - 1, #body.body) do
      rows:insert(body.body[index]:clone())
    end
    part.bodies[1].body = rows
    if first > 1 then
      part.identifier = ''
      part.caption = pandoc.Caption()
    end
    blocks:insert(part)
  end
  return blocks
end

function Pandoc(doc)
  if FORMAT ~= 'beamer' then return nil end
  local blocks = pandoc.List()
  for _, block in ipairs(doc.blocks) do
    local parts = block.t == 'Table' and paginate_table(block) or nil
    if parts then blocks:extend(parts) else blocks:insert(block) end
  end
  doc.blocks = blocks
  return doc
end
