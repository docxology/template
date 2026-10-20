-- Final archive-only pass, deliberately after Crossref: one conceptual Figure
-- has one number/full caption even when its source-bound image body has panels.
-- Nested figures, raw examples and mixed prose/image bodies abstain unchanged.
local function images_only(elem)
  if #elem.content == 0 or #elem.classes ~= 0 or #elem.attributes ~= 0 then return false end
  for _, block in ipairs(elem.content) do
    if (block.t ~= 'Plain' and block.t ~= 'Para') or #block.content ~= 1
        or block.content[1].t ~= 'Image' then return false end
  end
  return elem.identifier == '' or elem.identifier:match('^[A-Za-z0-9:_.-]+$') ~= nil
end

function Pandoc(doc)
  if FORMAT ~= 'beamer' then return nil end
  local blocks = pandoc.List()
  for _, block in ipairs(doc.blocks) do
    if block.t ~= 'Figure' or not images_only(block) then
      blocks:insert(block)
    else
      blocks:insert(pandoc.RawBlock('latex', '\\framebreak'))
      local anchor = '\\refstepcounter{figure}'
      if block.identifier ~= '' then anchor = anchor .. '\\label{' .. block.identifier .. '}' end
      -- This zero-ink anchor belongs to the first image frame, never a separate
      -- title-only frame or a second conceptual counter for the next panel.
      blocks:insert(pandoc.RawBlock('latex', anchor))
      for _, image in ipairs(block.content) do
        blocks:insert(pandoc.RawBlock('latex', '\\begin{archiveimageframe}'))
        blocks:insert(image)
        blocks:insert(pandoc.RawBlock('latex', '\\end{archiveimageframe}'))
        blocks:insert(pandoc.RawBlock('latex', '\\framebreak'))
      end
      if #block.caption.long > 0 then
        local number = '\\thefigure'
        if block.identifier ~= '' then
          number = '\\archivefigurecaptionnumber{' .. block.identifier .. '}{\\thefigure}'
        end
        local prefix = pandoc.RawInline('latex', '\\figurename~' .. number .. ':\\ ')
        local first = true
        local function emit(inlines)
          if #inlines == 0 then return end
          if first then inlines:insert(1, prefix); first = false end
          blocks:insert(pandoc.RawBlock('latex', '\\begin{archivecaptionframe}'))
          blocks:insert(pandoc.Para(inlines))
          blocks:insert(pandoc.RawBlock('latex', '\\end{archivecaptionframe}'))
          blocks:insert(pandoc.RawBlock('latex', '\\framebreak'))
        end
        for _, caption in ipairs(block.caption.long) do
          if caption.t == 'Plain' or caption.t == 'Para' then
            local chunk = pandoc.List()
            local characters = 0
            for _, inline in ipairs(caption.content) do
              local whitespace = inline.t == 'Space' or inline.t == 'SoftBreak' or inline.t == 'LineBreak'
              -- Split only between complete authored inline nodes at an actual
              -- word boundary. No shortening, reordering or duplicate caption.
              if whitespace and characters >= 400 then
                emit(chunk); chunk = pandoc.List(); characters = 0
              else
                chunk:insert(inline)
                characters = characters + #pandoc.utils.stringify(inline)
              end
            end
            emit(chunk)
          else
            -- Other complete semantic caption blocks keep their content; a
            -- complex unbreakable block is never flattened into guessed prose.
            blocks:insert(pandoc.RawBlock('latex', '\\begin{archivecaptionframe}'))
            if first then blocks:insert(pandoc.Para({prefix})); first = false end
            blocks:insert(caption)
            blocks:insert(pandoc.RawBlock('latex', '\\end{archivecaptionframe}'))
            blocks:insert(pandoc.RawBlock('latex', '\\framebreak'))
          end
        end
      end
    end
  end
  doc.blocks = blocks
  return doc
end
