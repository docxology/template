-- Add optional character breaks only to simple table-header tokens. Body cells,
-- ordinary code and non-TeX writers retain their exact input AST. Primitive
-- penalties need no package or macro preamble, including header-only documents.
local function eligible(text)
  return #text >= 3 and text:match('^[A-Za-z0-9_./:%+%-]+$') ~= nil
end

local function broken(text)
  local letters = {}
  for index = 1, #text do
    local letter = text:sub(index, index)
    if letter == '_' then letter = '\\_' end
    letters[#letters + 1] = letter
  end
  return table.concat(letters, '\\allowbreak{}')
end

local function rewrite(inlines)
  for _, inline in ipairs(inlines) do
    if inline.t ~= 'Str' and inline.t ~= 'Code' and inline.t ~= 'Space'
        and inline.t ~= 'SoftBreak' and inline.t ~= 'LineBreak' then return end
    if inline.t == 'Code' and (inline.identifier ~= '' or #inline.classes ~= 0
        or #inline.attributes ~= 0) then return end
  end
  for index, inline in ipairs(inlines) do
    if inline.t == 'Str' and eligible(inline.text) then
      inlines[index] = pandoc.RawInline('latex', broken(inline.text))
    elseif inline.t == 'Code' and inline.identifier == ''
        and #inline.classes == 0 and #inline.attributes == 0
        and eligible(inline.text) then
      inlines[index] = pandoc.RawInline('latex', '\\texttt{' .. broken(inline.text) .. '}')
    end
  end
end

local function break_headers(elem)
  for _, row in ipairs(elem.head.rows) do
    for _, cell in ipairs(row.cells) do
      -- Unknown spans/blocks/nesting abstain, rather than flattening scientific
      -- markup, raw TeX or an identifier-bearing wrapper into guessed text.
      if cell.row_span == 1 and cell.col_span == 1 and cell.identifier == '' then
        for _, block in ipairs(cell.contents) do
          if block.t == 'Plain' or block.t == 'Para' then rewrite(block.content) end
        end
      end
    end
  end
  return elem
end


function Pandoc(doc)
  if FORMAT ~= 'latex' and FORMAT ~= 'beamer'
      and not (FORMAT == 'json' and doc.meta['template-latex-table-headers']) then return nil end
  -- Nested tables and embedded/raw examples are not a header-rewrite surface.
  for index, block in ipairs(doc.blocks) do
    if block.t == 'Table' then doc.blocks[index] = break_headers(block) or block end
  end
  return doc
end
