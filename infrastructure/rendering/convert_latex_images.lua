-- Pandoc Lua filter to convert LaTeX \includegraphics commands to HTML img tags
-- This filter handles the conversion of LaTeX image commands that pandoc doesn't automatically convert

-- Helper function to extract caption text from Para content
local function extract_text_from_inlines(inlines)
  local text_parts = {}
  for _, inline in ipairs(inlines) do
    if inline.t == "Str" then
      table.insert(text_parts, inline.text)
    elseif inline.t == "Space" then
      table.insert(text_parts, " ")
    elseif inline.t == "Math" then
      -- Preserve math as LaTeX for MathJax
      table.insert(text_parts, "\\(" .. inline.text .. "\\)")
    elseif inline.t == "RawInline" and inline.format == "html" then
      table.insert(text_parts, inline.text)
    end
  end
  return table.concat(text_parts)
end

local function clean_caption_text(text)
  text = text:gsub("\\eqref{[^}]+}", "(Equation)")
  text = text:gsub("\\ref{[^}]+}", "(Ref)")
  return text
end

local function extract_braced_command_content(content, command_name)
  local prefix = "\\" .. command_name .. "{"
  local start_pos = content:find(prefix, 1, true)
  if not start_pos then
    return nil
  end

  local content_start = start_pos + #prefix
  local depth = 1

  for idx = content_start, #content do
    local ch = content:sub(idx, idx)
    if ch == "{" then
      depth = depth + 1
    elseif ch == "}" then
      depth = depth - 1
      if depth == 0 then
        return content:sub(content_start, idx - 1)
      end
    end
  end

  return nil
end

local function extract_caption_from_raw(content)
  local caption_text = extract_braced_command_content(content, "caption")
  if caption_text then
    return clean_caption_text(caption_text)
  end
  return ""
end

local function textwidth_to_percent(width_match)
  if width_match:match("\\textwidth") then
    local frac = width_match:match("^([%d.]+)\\textwidth$")
    if frac then
      local n = tonumber(frac)
      if n then
        local pct = n * 100
        local nearest_int = math.floor(pct + 0.5)
        if math.abs(pct - nearest_int) < 1e-9 then
          return string.format("%d%%", nearest_int)
        end
        return string.format("%s%%", tostring(pct))
      end
    end
    return "100%"
  end

  return width_match
end

-- Para filter to handle figure environments that span a paragraph
function Para(el)
  local para_content = extract_text_from_inlines(el.content)

  -- Check if this paragraph contains a figure environment
  if para_content:match("\\begin{figure}") then
    -- Extract the image source from any img tag or includegraphics
    local img_src = nil
    local img_html = nil

    -- Look for already-converted img tags in the content
    for _, inline in ipairs(el.content) do
      if inline.t == "RawInline" and inline.format == "html" then
        local src = inline.text:match('src="([^"]+)"')
        if src then
          img_src = src
          img_html = inline.text
          break
        end
      end
    end

    -- If no image found, try to extract from includegraphics
    if not img_src then
      local filename = para_content:match("\\includegraphics%[?[^%]]*%]?{([^}]+)}")
      if filename then
        -- Clean up filename path and ensure correct relative path from HTML location
        local clean_filename = filename:gsub("^%.%./output/figures/", "../figures/")
        clean_filename = clean_filename:gsub("^output/figures/", "../figures/")
        clean_filename = clean_filename:gsub("^figures/", "../figures/")
        img_src = clean_filename
        img_html = string.format('<img src="%s" alt="%s" style="max-width: 80%%; height: auto;" class="figure">',
                                  clean_filename, clean_filename:gsub("%.%w+$", ""))
      end
    end

    -- Extract caption text (between \caption{ and the closing })
    local caption_text = extract_caption_from_raw(para_content)

    -- If we found an image, create proper HTML figure
    if img_html then
      local figure_html
      if caption_text ~= "" then
        figure_html = string.format(
          '<figure class="figure">\n%s\n<figcaption>%s</figcaption>\n</figure>',
          img_html, caption_text
        )
      else
        figure_html = string.format('<figure class="figure">\n%s\n</figure>', img_html)
      end

      return pandoc.RawBlock("html", figure_html)
    end

    -- If no image found but it's still a figure block, try to remove the LaTeX wrappers
    -- This handles cases where the figure block has issues
    local cleaned_content = para_content
    cleaned_content = cleaned_content:gsub("\\begin{figure}%[[^%]]*%]", "")
    cleaned_content = cleaned_content:gsub("\\begin{figure}", "")
    cleaned_content = cleaned_content:gsub("\\end{figure}", "")
    cleaned_content = cleaned_content:gsub("\\centering", "")
    cleaned_content = cleaned_content:gsub("\\label{[^}]+}", "")
    cleaned_content = cleaned_content:gsub("\\caption{[^}]+}", "")

    -- If there's meaningful content left, return it
    cleaned_content = cleaned_content:match("^%s*(.-)%s*$") -- trim
    if cleaned_content and cleaned_content ~= "" then
      return pandoc.Para({pandoc.Str(cleaned_content)})
    end

    -- Otherwise return empty
    return {}
  end

  -- Check for standalone LaTeX commands that should be stripped
  local has_figure_commands = para_content:match("\\centering") or
                              para_content:match("\\caption{") or
                              para_content:match("\\label{fig:") or
                              para_content:match("\\end{figure}")

  if has_figure_commands then
    -- This is likely orphaned figure content, strip the LaTeX commands
    local new_content = {}
    local skip_next_space = false

    for _, inline in ipairs(el.content) do
      if inline.t == "RawInline" and inline.format == "html" then
        -- Keep HTML (like converted img tags)
        table.insert(new_content, inline)
        skip_next_space = false
      elseif inline.t == "Str" then
        local text = inline.text
        -- Strip out LaTeX figure commands
        text = text:gsub("\\begin{figure}%[[^%]]*%]", "")
        text = text:gsub("\\begin{figure}", "")
        text = text:gsub("\\end{figure}", "")
        text = text:gsub("\\centering", "")
        text = text:gsub("\\label{[^}]+}", "")

        -- Handle partial caption (might split across Str elements)
        if text:match("\\caption{") then
          skip_next_space = true
          -- Don't include caption start
        elseif text:match("^}") and skip_next_space then
          -- End of caption
          skip_next_space = false
        elseif not skip_next_space and text:match("%S") then
          table.insert(new_content, pandoc.Str(text))
        end
      elseif inline.t == "Space" and not skip_next_space then
        table.insert(new_content, inline)
      end
    end

    if #new_content > 0 then
      return pandoc.Para(new_content)
    end
    return {}
  end

  return el
end

function RawInline(elem)
  -- Look for \includegraphics commands in raw LaTeX
  if elem.format == "tex" then
    local content = elem.text

    -- Pattern to match \includegraphics[options]{filename}
    local pattern = "\\includegraphics%[([^%]]*)%]%{([^}]+)%}"
    local options, filename = content:match(pattern)

    if filename then
      -- Extract width from options if present
      local width = "100%"
      if options then
        local width_match = options:match("width=([^,]+)")
        if width_match then
          width = textwidth_to_percent(width_match)
        end
      end

      -- Clean up filename path and ensure correct relative path from HTML location
      local clean_filename = filename:gsub("^%.%./output/figures/", "../figures/")
      clean_filename = clean_filename:gsub("^output/figures/", "../figures/")
      clean_filename = clean_filename:gsub("^figures/", "../figures/")

      -- Create HTML img tag
      local img_html = string.format('<img src="%s" alt="%s" style="max-width: %s; height: auto;" class="figure">',
                                   clean_filename, clean_filename:gsub("%.%w+$", ""), width)

      -- Limitation: this per-node filter can only attach a caption when
      -- \caption{...} is present in the same raw TeX node as \includegraphics.
      local caption_text = extract_caption_from_raw(content)
      if caption_text ~= "" then
        local figure_html = string.format(
          '<figure class="figure">%s<figcaption>%s</figcaption></figure>',
          img_html,
          caption_text
        )
        return pandoc.RawInline("html", figure_html)
      end

      -- Return the HTML as raw HTML
      return pandoc.RawInline("html", img_html)
    end
  end

  return elem
end

function RawBlock(elem)
  -- Handle block-level LaTeX commands
  if elem.format == "tex" then
    local content = elem.text

    -- Pattern to match \includegraphics[options]{filename}
    local pattern = "\\includegraphics%[([^%]]*)%]%{([^}]+)%}"
    local options, filename = content:match(pattern)

    if filename then
      -- Extract width from options if present
      local width = "100%"
      if options then
        local width_match = options:match("width=([^,]+)")
        if width_match then
          width = textwidth_to_percent(width_match)
        end
      end

      -- Clean up filename path and ensure correct relative path from HTML location
      local clean_filename = filename:gsub("^%.%./output/figures/", "../figures/")
      clean_filename = clean_filename:gsub("^output/figures/", "../figures/")
      clean_filename = clean_filename:gsub("^figures/", "../figures/")

      local alt_text = clean_filename:gsub("%.%w+$", "")
      local img_html = string.format(
        '<img src="%s" alt="%s" style="max-width: %s; height: auto;">',
        clean_filename,
        alt_text,
        width
      )

      -- Limitation: this per-node filter can only attach a caption when
      -- \caption{...} is present in the same raw TeX node as \includegraphics.
      local caption_text = extract_caption_from_raw(content)
      if caption_text ~= "" then
        local figure_html = string.format(
          '<figure class="figure">%s<figcaption>%s</figcaption></figure>',
          img_html,
          caption_text
        )
        return pandoc.RawBlock("html", figure_html)
      end

      -- Create HTML img tag wrapped in a div
      local div_html = string.format('<div class="figure">%s</div>', img_html)

      -- Return the HTML as raw HTML
      return pandoc.RawBlock("html", div_html)
    end
  end

  return elem
end
