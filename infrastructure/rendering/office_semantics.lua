-- Preserve the declared cross-format roles of raw TeX in native Office books.
-- Unknown raw forms remain untouched and therefore remain an acceptance obligation.
local target = nil

local function equation(raw)
  local body = raw:match('^%s*\\begin{equation}%s*(.-)%s*\\end{equation}%s*$')
  if not body then return nil end
  local label = body:match('^\\label{([%w:_%-]+)}%s*')
  if not label then return nil end
  body = body:gsub('^\\label{[%w:_%-]+}%s*', '', 1)
  if body:find('\\label', 1, true) or body:find('\\begin{equation}', 1, true) then return nil end
  -- Reading the standard equation syntax preserves the identifier contract of
  -- pandoc-crossref, rather than inventing an unrelated numbering scheme.
  return pandoc.read('$$\n' .. body .. '\n$$ {#' .. label .. '}\n', 'markdown').blocks
end

local function pagebreak()
  if target == 'docx' then
    return pandoc.RawBlock('openxml', '<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
  end
  return pandoc.RawBlock('html', '<div class="template-office-pagebreak" style="break-after: page; page-break-after: always;"></div>')
end

local begin_compact = '\\thispagestyle{empty}\n\\setlength{\\parskip}{0pt}\n\\setlength{\\itemsep}{0pt}\n\\begin{samepage}\n\\scriptsize'
local end_begin = '% transmission-end-bookend\n\\clearpage\n' .. begin_compact

local function header(raw)
  local command, title, suffix = raw:match('^%s*\\([%a]+)%*{([^{}]+)}(.-)%s*$')
  local levels = {section=1, subsection=2, subsubsection=3}
  if not command or not levels[command] then return nil end
  local label = suffix:match('^\\label{([%w:_%-]+)}$')
  if suffix ~= '' and not label then return nil end
  return pandoc.Header(levels[command], pandoc.Inlines{pandoc.Str(title)}, pandoc.Attr(label or '', {'unnumbered'}))
end

function Pandoc(doc)
  target = FORMAT
  if target == 'json' then target = pandoc.utils.stringify(doc.meta['office-native-target'] or '') end
  if target ~= 'docx' and target ~= 'epub' and target ~= 'epub3' then return doc end
  if target == 'epub3' then target = 'epub' end
  local result = pandoc.List()
  local compact = nil
  local alternative = nil
  local retained_alternatives = doc.meta['template-office-source-alternatives']
  local source_alternatives = pandoc.List()
  local image_index = 0
  doc.meta['template-office-source-alternatives'] = nil
  local function append(block)
    if compact then compact:insert(block) else result:insert(block) end
  end
  for _, block in ipairs(doc.blocks) do
    if block.t == 'RawBlock' and block.format == 'html' then
      local description = block.text:match('^<!%-%-%s*alt:%s*(.-)%s*%-%->$')
      if description then
        if alternative then error('native Office source alt has no following image') end
        alternative = description:gsub('%s+', ' ')
      end
    end
    block = block:walk({Image=function(image)
      image_index = image_index + 1
      if retained_alternatives then
        if not retained_alternatives[image_index] then error('native Office source image order changed during filters') end
        local description = pandoc.utils.stringify(retained_alternatives[image_index])
        if description ~= '' then
          image.attributes['alt'] = description
          -- Pandoc's DOCX writer derives docPr.descr from Image.caption, even
          -- when an alt attribute exists. Figure.caption retains the original
          -- visible caption independently, so this restores the actual image
          -- alternative without replacing the displayed figure caption.
          image.caption = pandoc.Inlines{pandoc.Str(description)}
        end
        alternative = nil
      elseif alternative then image.attributes['alt'] = alternative; alternative = nil end
      source_alternatives:insert(pandoc.MetaString(image.attributes['alt'] or ''))
      return image
    end})
    if block.t == 'RawBlock' and (block.format == 'latex' or block.format == 'tex') then
      local raw = block.text:gsub('%s+$', '')
      if raw == begin_compact or raw == end_begin then
        if compact then error('nested native Office samepage group is unsupported') end
        if raw == end_begin then result:insert(pagebreak()) end
        compact = pandoc.List()
      elseif raw == '\\end{samepage}' or raw == '\\end{samepage}\n\\newpage' then
        if not compact then error('native Office samepage end has no beginning') end
        local attr = pandoc.Attr('', {'template-transmission'}, {
          ['custom-style']='TemplateTransmission',
          ['style']='break-inside: avoid; page-break-inside: avoid; font-size: 70%; margin: 0;',
        })
        result:insert(pandoc.Div(compact, attr))
        compact = nil
        if raw:find('\\newpage', 1, true) then result:insert(pagebreak()) end
      elseif raw == '\\newpage' or raw == '\\clearpage' then append(pagebreak())
      else
        local h = header(raw)
        local e = equation(raw)
        if h then append(h) elseif e then for _, child in ipairs(e) do append(child) end else append(block) end
      end
    elseif block.t == 'Para' or block.t == 'Plain' then
      local pending = pandoc.Inlines{}
      local function flush()
        if #pending > 0 then
          append(block.t == 'Para' and pandoc.Para(pending) or pandoc.Plain(pending))
          pending = pandoc.Inlines{}
        end
      end
      for _, inline in ipairs(block.content) do
        local e = nil
        if inline.t == 'RawInline' and (inline.format == 'tex' or inline.format == 'latex') then
          e = equation(inline.text)
        end
        if e then
          flush()
          for _, child in ipairs(e) do append(child) end
        else pending:insert(inline) end
      end
      flush()
    else append(block) end
  end
  if compact then error('native Office samepage group has no ending') end
  if alternative then error('native Office source alt has no following image') end
  if retained_alternatives then
    if #retained_alternatives ~= image_index then error('native Office source image count changed during filters') end
  else
    -- Crossref can rebuild Figure nodes and discard Image alt attributes and
    -- raw HTML comments for DOCX. Carry the exact ordered descriptions through
    -- that filter, restore them in the final pass, then remove this metadata.
    doc.meta['template-office-source-alternatives'] = pandoc.MetaList(source_alternatives)
  end
  doc.blocks = result
  return doc
end

return {{Pandoc=Pandoc}}
