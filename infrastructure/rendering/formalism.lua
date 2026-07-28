--[[
Auto-number formalism blocks and resolve references to them.

pandoc-crossref (0.3.24) numbers figures, equations, tables, listings and
sections, but has no custom-environment support, so numbered Definitions and
Propositions in a manuscript have to be written by hand. Hand numbering
drifts: a block inserted in the middle silently renumbers everything after it,
and a reference to it in prose keeps pointing at the old number.

This filter takes the numbering over.

    ::: {.definition #def:aspiration title="Aspiration"}
    An aspiration is a six-tuple.
    :::

    By [@def:aspiration] the registry is well formed.

renders as

    **Definition 1 (Aspiration).** An aspiration is a six-tuple.

    By Definition 1 the registry is well formed.

Counters are per kind and run in document order. A reference is resolved from
the label, never from a number written in the source, so there is no number in
the manuscript that can go stale.

Metadata:

  formalism_reset_level   Reset every counter when a header at or above this
                          level is seen. 0 (the default) never resets. A
                          collected volume sets this to 1 so numbering restarts
                          for each work it reproduces; a standalone paper leaves
                          it unset, because there a level-1 header is a section.

  formalism_kinds         Optional map of class name to displayed title, merged
                          over the defaults below. Use it to add a kind without
                          editing this file.

CITATION SYNTAX IS LOAD-BEARING. `[@def:x]` parses as a pandoc Citation, and
the writers this filter runs in front of resolve citations for real: the PDF
path uses --natbib, DOCX/EPUB/HTML use --citeproc. If a formalism reference
survived this filter as a Cite node, natbib would emit \citep{def:x} and ship
"[?]" in the PDF, and citeproc would log an unresolved citation. So every
citation this filter recognises as a formalism reference is consumed here and
never reaches the citation machinery:

  * a declared label becomes a hyperlink carrying the resolved text;
  * an undeclared label that still looks like a formalism reference is left
    exactly as the author wrote it, as literal text, and reported on stderr.
    Emitting a Cite would produce the undefined-citation failure above;
    dropping it would turn a broken cross-reference into invisible prose.

A citation group may mix the two vocabularies -- `[@def:x; @smith2020]`. The
formalism entries are peeled off and the bibliography entries are handed back
to the citation machinery as a narrowed Cite. Returning the group untouched
because one member was a bibliography key is the bug this partition exists to
prevent.
--]]

local DEFAULT_KINDS = {
  definition  = "Definition",
  proposition = "Proposition",
  theorem     = "Theorem",
  lemma       = "Lemma",
  corollary   = "Corollary",
  remark      = "Remark",
  axiom       = "Axiom",
  claim       = "Claim",
  example     = "Example",
}

local kinds = {}
local counters = {}
local labels = {}             -- label -> {kind_title = ..., number = ...}
local declared_prefixes = {}  -- "def" -> true, for recognising a broken "def:typo"
local reset_level = 0

local function meta_to_string(value)
  if value == nil then return nil end
  if type(value) == "string" then return value end
  return pandoc.utils.stringify(value)
end

local function read_meta(meta)
  for class, title in pairs(DEFAULT_KINDS) do
    kinds[class] = title
  end
  if meta.formalism_kinds then
    for class, title in pairs(meta.formalism_kinds) do
      kinds[class] = meta_to_string(title)
    end
  end
  if meta.formalism_reset_level then
    reset_level = tonumber(meta_to_string(meta.formalism_reset_level)) or 0
  end
end

--- The formalism class on a Div, or nil when it carries none.
--
-- A ``theorem-box`` Div is skipped deliberately. ``WebRenderer._html_theorem_blocks``
-- rewrites raw-LaTeX ``\begin{definition}`` environments into
-- ``::: {.theorem-box .definition}`` Divs and numbers them itself, on a shared
-- counter, before pandoc ever runs. That is the same Div shape this filter
-- consumes, so without this guard the combined HTML edition numbers such a
-- block twice — the tracked ``template_formal`` exemplar rendered
-- ``**Definition 1.** **Definition 1**`` and ``**Proposition 1.** **Proposition 2**``.
-- The raw-LaTeX authoring path keeps its own numbering; this filter owns only
-- blocks an author wrote in the fenced-Div syntax.
local function kind_of(div)
  for _, class in ipairs(div.classes) do
    if class == "theorem-box" then return nil end
  end
  for _, class in ipairs(div.classes) do
    if kinds[class] then return class end
  end
  return nil
end

local function is_unnumbered(div)
  for _, class in ipairs(div.classes) do
    if class == "unnumbered" then return true end
  end
  return false
end

--- Pass 1: number every formalism block and rewrite its opening.
local function number_blocks(blocks)
  return pandoc.walk_block(pandoc.Div(blocks), {
    traverse = "topdown",

    Header = function(header)
      if reset_level > 0 and header.level <= reset_level then
        counters = {}
      end
      return nil
    end,

    Div = function(div)
      local class = kind_of(div)
      if not class then return nil end

      local title_text = kinds[class]
      local label = div.identifier
      local prefix

      if is_unnumbered(div) then
        prefix = title_text
      else
        counters[class] = (counters[class] or 0) + 1
        local number = counters[class]
        prefix = title_text .. " " .. tostring(number)
        if label ~= "" then
          if labels[label] then
            io.stderr:write(
              "formalism.lua: duplicate label '" .. label .. "'\n")
          end
          labels[label] = { kind_title = title_text, number = number }
          local label_prefix = label:match("^([%a]+):")
          if label_prefix then declared_prefixes[label_prefix] = true end
        end
      end

      local named = div.attributes["title"]
      if named and named ~= "" then
        prefix = prefix .. " (" .. named .. ")"
      end

      -- The marker joins the first paragraph so the block reads as prose
      -- rather than as a heading with a dangling body.
      local marker = pandoc.Strong({ pandoc.Str(prefix .. ".") })
      local first = div.content[1]
      if first and (first.t == "Para" or first.t == "Plain") then
        local opening = { marker, pandoc.Space() }
        for _, inline in ipairs(first.content) do
          table.insert(opening, inline)
        end
        div.content[1] = pandoc.Para(opening)
      else
        table.insert(div.content, 1, pandoc.Para({ marker }))
      end
      return div
    end,
  }).content
end

--- Does this citation id name a formalism block, declared or not?
--
-- A declared label is definitive. An undeclared id counts when its prefix is
-- one the document already uses for formalism labels, or is a prefix of a
-- known kind name ("def" of "definition"). The document-driven half is what
-- catches conventional abbreviations the kind names do not spell out: once a
-- manuscript declares #thm:pythagoras, a stale [@thm:pythagorean] is caught
-- rather than passed to the bibliography as a missing key.
-- A reference is ours when the label was declared, or when its prefix is one
-- this document actually uses for a declared formalism. Nothing else.
--
-- An earlier version also claimed any prefix that merely spelled the start of a
-- kind name. That matched 64 prefixes, including the single letters a, c, d, e,
-- l, p, r and t, so an ordinary bibliography key of the routine
-- ``author:year`` shape was stolen: ``[@ex:pandoc2020]`` and ``[@co:jones1999]``
-- stopped being citations and shipped as literal ``[@...]`` markup in every
-- edition, with pandoc still exiting 0. Whether a key survived depended on
-- whether it happened to spell the start of one of nine English words. Only
-- declarations present in the document may claim a prefix.
local function looks_like_formalism(id)
  if labels[id] then return true end
  local prefix = id:match("^([%a]+):")
  if not prefix then return false end
  return declared_prefixes[prefix] == true
end

--- Pass 2: consume every formalism reference written as a citation.
local function resolve_references(blocks)
  return pandoc.walk_block(pandoc.Div(blocks), {
    Cite = function(cite)
      local resolved = {}
      local remaining = {}
      local formalism_seen = 0
      local resolved_count = 0

      for _, citation in ipairs(cite.citations) do
        if looks_like_formalism(citation.id) then
          formalism_seen = formalism_seen + 1
          if #resolved > 0 then
            table.insert(resolved, pandoc.Str(","))
            table.insert(resolved, pandoc.Space())
          end
          local entry = labels[citation.id]
          if entry then
            resolved_count = resolved_count + 1
            -- Carry the author's own prefix and suffix across. Dropping them
            -- deletes prose: "[see @def:aspiration, p. 3]" must not silently
            -- become "Definition 1".
            for _, inline in ipairs(citation.prefix or {}) do
              table.insert(resolved, inline)
            end
            if citation.prefix and #citation.prefix > 0 then
              table.insert(resolved, pandoc.Space())
            end
            local text = entry.kind_title .. " " .. tostring(entry.number)
            table.insert(resolved,
              pandoc.Link({ pandoc.Str(text) }, "#" .. citation.id))
            for _, inline in ipairs(citation.suffix or {}) do
              table.insert(resolved, inline)
            end
          else
            io.stderr:write(
              "formalism.lua: reference to undeclared formalism '"
              .. citation.id .. "'\n")
            table.insert(resolved, pandoc.Str("[@" .. citation.id .. "]"))
          end
        else
          table.insert(remaining, citation)
        end
      end

      -- Nothing of ours: hand the group back to natbib/citeproc untouched.
      if formalism_seen == 0 then return nil end

      -- Every member was ours and every one was broken: reproduce the author's
      -- own text exactly. cite.content is the verbatim source of the group.
      if resolved_count == 0 and #remaining == 0 then
        return cite.content
      end

      if #remaining == 0 then return resolved end

      -- Mixed group: keep the bibliography half as a citation the writer can
      -- still resolve, and rebuild its bracketed source text to match.
      local kept = {}
      for index, citation in ipairs(remaining) do
        if index > 1 then
          table.insert(kept, pandoc.Str(";"))
          table.insert(kept, pandoc.Space())
        end
        table.insert(kept, pandoc.Str("@" .. citation.id))
      end
      table.insert(kept, 1, pandoc.Str("["))
      table.insert(kept, pandoc.Str("]"))

      table.insert(resolved, pandoc.Space())
      table.insert(resolved, pandoc.Cite(kept, remaining))
      return resolved
    end,
  }).content
end

function Pandoc(doc)
  kinds = {}
  counters = {}
  labels = {}
  declared_prefixes = {}
  reset_level = 0

  read_meta(doc.meta)
  doc.blocks = number_blocks(doc.blocks)
  doc.blocks = resolve_references(doc.blocks)
  return doc
end

-- Metadata must be read before the block walk, and the block walk must finish
-- before any reference is resolved, so the traversal is driven explicitly from
-- Pandoc rather than left to pandoc's own element dispatch order.
return { { Pandoc = Pandoc } }
