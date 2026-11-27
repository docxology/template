-- Normalize a narrow set of raw TeX labels for combined HTML and its JSON replay.
-- The caller supplies this filter only when it also supplies pandoc-crossref.
local function section_label(block)
  local inline = block.t == "Para" and #block.content == 1 and block.content[1]
  if inline and inline.t == "RawInline" and inline.format == "tex" then
    return inline.text:match("^\\label{(sec:[%w_.:-]+)}$")
  end
end

local function figure_parts(block)
  if block.format ~= "tex" then return end
  return block.text:match(
    "^\\begin{figure}%[[^%]]+%]%s+\\centering%s+"
    .. "\\includegraphics%[width=([%d.]+)\\textwidth%]{([^}]+)}%s+"
    .. "\\caption{(.*)}%s+\\label{(fig:[%w_.:-]+)}%s+\\end{figure}%s*$")
end

function Pandoc(doc)
  local owners, targets = {}, {}
  local opaque_html = false
  local function count(id)
    if id and id ~= "" then owners[id] = (owners[id] or 0) + 1 end
  end
  local function count_identifier(node)
    count(node.identifier)
    if (node.t == "RawBlock" or node.t == "RawInline") and node.format ~= "tex" then
      -- Only inert, complete comments have no possible fragment ownership.
      -- Other raw HTML can hide anchors through syntax the AST cannot classify.
      local comment = node.text:match("^%s*<!%-%-([^<>]*)%-%->%s*$")
      if not comment or comment:find("--", 1, true) then opaque_html = true end
    end
    if node.t == "RawBlock" then
      local _, _, _, label = figure_parts(node)
      count(label)
    end
  end
  local function count_sections(blocks)
    for i = 2, #blocks do
      if blocks[i-1].t == "Header" then count(section_label(blocks[i])) end
    end
  end
  doc:walk({Block = count_identifier, Inline = count_identifier, Blocks = count_sections})
  if opaque_html then return end

  local function typed_target(node)
    local prefix = node.t == "Header" and "sec:" or "fig:"
    local id = node.identifier
    if id:sub(1, 4) == prefix and owners[id] == 1 then targets[id] = true end
  end
  doc:walk({Header = typed_target, Figure = typed_target})

  local function sections(blocks)
    local output = pandoc.List()
    for _, block in ipairs(blocks) do
      local label = section_label(block)
      local header = output[#output]
      if label and owners[label] == 1 and header and header.t == "Header"
        and not header.identifier:match("^sec:") then
        local alias = header.identifier
        header.identifier = label
        targets[label] = true
        if alias ~= "" and owners[alias] == 1 then
          output:insert(#output, pandoc.Div({}, pandoc.Attr(alias)))
        end
      else
        output:insert(block)
      end
    end
    return output
  end

  local function figure(block)
    local width, path, caption, label = figure_parts(block)
    local fraction = tonumber(width)
    if not label or owners[label] ~= 1 or not fraction or fraction <= 0 then return end
    local parsed = pandoc.read(caption, "markdown+tex_math_dollars+raw_tex-raw_html").blocks
    if #parsed ~= 1 or parsed[1].t ~= "Para" then return end
    targets[label] = true
    local image = pandoc.Image(parsed[1].content, path, "", pandoc.Attr("", {}, {
      width = string.format("%g%%", fraction * 100),
    }))
    return pandoc.Figure({pandoc.Plain({image})}, pandoc.Caption(parsed), pandoc.Attr(label))
  end
  doc = doc:walk({Blocks = sections, RawBlock = figure})

  local function reference(inline)
    local label = inline.text:match("^\\ref{([%w_.:-]+)}$")
    if label and targets[label] then
      local citation = pandoc.Citation(label, "SuppressAuthor")
      return pandoc.Cite({pandoc.Str("[-@" .. label .. "]")}, {citation})
    end
  end
  return doc:walk({
    RawInline = function(inline)
      if inline.format == "tex" then return reference(inline) end
    end,
    Math = function(inline)
      if inline.mathtype == "InlineMath" then return reference(inline) end
    end,
  })
end
