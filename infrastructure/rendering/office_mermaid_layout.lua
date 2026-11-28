-- DOCX preserves Image.title through Crossref into wp:docPr. The native
-- layout verifier checks each marked source PNG and restores its exact title.
local marker = os.getenv('TEMPLATE_DOCX_MERMAID_LAYOUT_MARKER')

if FORMAT ~= 'docx' or not marker then
  error('DOCX Mermaid occurrence marking requires the current writer')
end

local ordinal = 0

function Image(image)
  if image.attributes['data-template-max-height'] ~= '4.2in' then
    return
  end
  local digest = image.src:match('^%.%./figures/mermaid_inline/inline_mermaid_%d+_([0-9a-f]+)%.png$')
  if not digest or #digest ~= 12 then
    return
  end
  ordinal = ordinal + 1
  image.title = marker .. ordinal .. ':' .. image.title
  return image
end
