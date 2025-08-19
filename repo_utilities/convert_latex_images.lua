-- Pandoc Lua filter to convert LaTeX \includegraphics commands to HTML img tags
-- This filter handles the conversion of LaTeX image commands that pandoc doesn't automatically convert

function RawInline(elem)
  -- Look for \includegraphics commands in raw LaTeX
  if elem.format == "tex" then
    local content = elem.text
    
    -- Pattern to match \includegraphics[options]{filename}
    local pattern = "\\includegraphics%[([^%]]*)%]%{([^}]+)%}"
    local options, filename = content:match(pattern)
    
    if filename then
      -- Extract width from options if present
      local width = "100%%"
      if options then
        local width_match = options:match("width=([^,]+)")
        if width_match then
          -- Convert LaTeX width to CSS percentage
          if width_match:match("0%.8\\textwidth") then
            width = "80%%"
          elseif width_match:match("0%.9\\textwidth") then
            width = "90%%"
          else
            width = width_match:gsub("\\textwidth", "100%%")
          end
        end
      end
      
      -- Clean up filename path and ensure correct relative path from HTML location
      local clean_filename = filename:gsub("^%.%./output/figures/", "figures/")
      clean_filename = clean_filename:gsub("^output/figures/", "figures/")
      clean_filename = clean_filename:gsub("^figures/", "figures/")
      
      -- Create HTML img tag
      local img_html = string.format('<img src="%s" alt="%s" style="max-width: %s; height: auto;" class="figure">', 
                                   clean_filename, clean_filename:gsub("%.%w+$", ""), width)
      
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
      local width = "100%%"
      if options then
        local width_match = options:match("width=([^,]+)")
        if width_match then
          -- Convert LaTeX width to CSS percentage
          if width_match:match("0%.8\\textwidth") then
            width = "80%%"
          elseif width_match:match("0%.9\\textwidth") then
            width = "90%%"
          else
            width = width_match:gsub("\\textwidth", "100%%")
          end
        end
      end
      
      -- Clean up filename path and ensure correct relative path from HTML location
      local clean_filename = filename:gsub("^%.%./output/figures/", "figures/")
      clean_filename = clean_filename:gsub("^output/figures/", "figures/")
      clean_filename = clean_filename:gsub("^figures/", "figures/")
      
      -- Create HTML img tag wrapped in a div
      local img_html = string.format('<div class="figure"><img src="%s" alt="%s" style="max-width: %s; height: auto;"></div>', 
                                   clean_filename, clean_filename:gsub("%.%w+$", ""), width)
      
      -- Return the HTML as raw HTML
      return pandoc.RawBlock("html", img_html)
    end
  end
  
  return elem
end
