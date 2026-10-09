"""Independent declared frontmatter text obligations from original YAML bytes."""

from __future__ import annotations

import hashlib
import datetime as dt
from typing import Any

import yaml

from infrastructure.reporting.native_format_content_contracts import ContentBlock, NativeContentContract, text_tokens


def compile_pdf_frontmatter_contract(path: str, config_bytes: bytes, artifact_id: str) -> NativeContentContract:
    """Interpret declared title/subtitle/authors without reading producer TeX.

    Runtime dates, configured covers and transmission pages have separate
    source-owned native obligations; they cannot be supplied as guessed text.
    """
    if not config_bytes or len(config_bytes) > 4 * 1024 * 1024:
        raise ValueError("original PDF frontmatter config exceeds its finite byte budget")

    class UniqueLoader(yaml.SafeLoader):
        pass

    def mapping(loader: UniqueLoader, node: yaml.MappingNode) -> dict[Any, Any]:
        result = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node)
            if key in result:
                raise ValueError("original PDF frontmatter config repeats a key")
            result[key] = loader.construct_object(value_node)
        return result

    UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
    loader = UniqueLoader(config_bytes)
    try:
        config = loader.get_single_data()
    finally:
        loader.dispose()
    if not isinstance(config, dict):
        raise ValueError("original PDF frontmatter config must be a mapping")
    blocks = []
    blockers = []
    book = config.get("book") or {}
    paper = config.get("paper") or {}
    if not isinstance(book, dict) or not isinstance(paper, dict):
        raise ValueError("original PDF paper/book metadata is malformed")
    for name in ("title", "subtitle"):
        value = book.get(name) or paper.get(name)
        if value:
            if not isinstance(value, str):
                raise ValueError("original PDF frontmatter title is not literal text")
            blocks.append(ContentBlock(f"config/{name}", f"frontmatter:{name}", 0, text_tokens(value)))
    book_opening = bool(book.get("title"))
    if book_opening:
        edition = book.get("edition") or "1.0"
        year = book.get("year") or paper.get("year") or ""
        if not isinstance(edition, str) or (year and type(year) not in {str, int}):
            raise ValueError("original PDF book edition/year is not supported literal metadata")
        if book.get("edition") or year:
            label = "Edition " + edition + (" – " + str(year) if year else "")
            blocks.append(ContentBlock("config/book/edition", "frontmatter:edition", 0, text_tokens(label)))
    authors = config.get("authors") or []
    if not isinstance(authors, list):
        raise ValueError("original PDF author metadata is malformed")
    for index, author in enumerate(authors):
        if not isinstance(author, dict):
            raise ValueError("original PDF author entry is not a mapping")
        affiliations = author.get("affiliations")
        if affiliations is not None and not isinstance(affiliations, (str, list)):
            raise ValueError("original PDF author affiliations are not literal text/list")
        affil_values = [affiliations] if isinstance(affiliations, str) else (affiliations or [])
        if any(not isinstance(value, str) for value in affil_values):
            raise ValueError("original PDF author affiliation list contains nonliteral text")
        if len(affil_values) > 1000:
            raise ValueError("original PDF author affiliation list exceeds its finite count")
        for name in ("name", "affiliation", "email", "orcid"):
            value = author.get(name)
            if value:
                if not isinstance(value, str):
                    raise ValueError("original PDF author field is not literal text")
                if name == "orcid":
                    value = "ORCID: " + value
                blocks.append(
                    ContentBlock(f"config/authors/{index}/{name}", "frontmatter:author", 0, text_tokens(value))
                )
        if affiliations is not None:
            blockers.append(
                f"config/authors/{index}: affiliation list/singular precedence and native ordered placement required"
            )
            for affil_index, value in enumerate(affil_values):
                blocks.append(
                    ContentBlock(
                        f"config/authors/{index}/affiliations/{affil_index}",
                        "frontmatter:affiliation",
                        0,
                        text_tokens(value),
                    )
                )
    front = config.get("front_matter") or {}
    if not isinstance(front, dict):
        raise ValueError("original PDF frontmatter settings are malformed")
    if any(front.get(name) for name in ("cover_image", "cover", "cover_file")):
        blockers.append("configured PDF cover requires independent native source asset/layout witness")
    publication = config.get("publication") or {}
    if not isinstance(publication, dict):
        raise ValueError("original PDF publication metadata is malformed")
    doi = publication.get("doi") or publication.get("doi_status")
    if doi:
        if not isinstance(doi, str):
            raise ValueError("original PDF publication DOI/status is not literal text")
        paper_cover = paper.get("cover")
        if authors or book_opening or (isinstance(paper_cover, dict) and paper_cover.get("image")):
            blocks.append(
                ContentBlock("config/publication/doi", "frontmatter:doi", 0, text_tokens("DOI: " + doi.strip()))
            )
    for section_name, section in (("paper", paper), ("book", book)):
        cover = section.get("cover") or {}
        if not isinstance(cover, dict):
            raise ValueError("original PDF cover configuration is not a mapping")
        if cover.get("image"):
            if not isinstance(cover["image"], str):
                raise ValueError("original PDF cover image is not a literal source path")
            blockers.append(
                f"configured {section_name}/cover requires independent source asset/alt/native layout witness"
            )
    if book_opening:
        for name in ("license", "code_license"):
            value = book.get(name)
            if value:
                if not isinstance(value, str):
                    raise ValueError("original PDF book publishing field is not literal text")
                blocks.append(ContentBlock(f"config/book/{name}", "frontmatter:publishing", 0, text_tokens(value)))
        for field in ("page_two_quote", "page_two_acknowledgements"):
            section = front.get(field) or {}
            if not isinstance(section, dict):
                raise ValueError("original PDF book publishing prose is not a mapping")
            value = section.get("text")
            if value:
                if not isinstance(value, str):
                    raise ValueError("original PDF book publishing prose is not literal text")
                if field == "page_two_acknowledgements":
                    heading = section.get("title", "Acknowledgements")
                    if not isinstance(heading, str):
                        raise ValueError("original PDF acknowledgement heading is not literal text")
                    blocks.append(
                        ContentBlock(
                            f"config/front_matter/{field}/title", "frontmatter:publishing", 0, text_tokens(heading)
                        )
                    )
                blocks.append(
                    ContentBlock(f"config/front_matter/{field}/text", "frontmatter:publishing", 0, text_tokens(value))
                )
                if field == "page_two_quote" and section.get("attribution"):
                    for name in ("attribution", "citation"):
                        quote_label = section.get(name)
                        if quote_label:
                            if not isinstance(quote_label, str):
                                raise ValueError("original PDF quotation attribution/citation is not literal text")
                            blocks.append(
                                ContentBlock(
                                    f"config/front_matter/{field}/{name}",
                                    "frontmatter:publishing",
                                    0,
                                    text_tokens(quote_label),
                                )
                            )
        blockers.append(
            "book publishing/quote/acknowledgement/citation/contents require original ordered page/native witness"
        )
    else:
        rendering = config.get("rendering") or {}
        if not isinstance(rendering, dict):
            raise ValueError("original PDF rendering metadata is malformed")
        include_date = rendering.get("include_date", True)
        if type(include_date) is not bool:
            blockers.append("original PDF nonboolean date setting requires independently interpreted source policy")
        elif include_date:
            date = paper.get("date") or book.get("year") or paper.get("year")
            if date:
                if type(date) not in {str, int, dt.date}:
                    raise ValueError("original PDF title date is not supported literal metadata")
                literal_date = str(date)
                if any(char in literal_date for char in "\\{}$%&#_^~"):
                    blockers.append("original PDF title date raw TeX requires source semantic/native admission")
                else:
                    blocks.append(ContentBlock("config/date", "frontmatter:date", 0, text_tokens(literal_date)))
            else:
                blockers.append(
                    "original PDF title date uses TeX runtime clock; source-owned clock/date witness required"
                )
    bookends = publication.get("transmission_bookends") or {}
    if isinstance(bookends, dict) and bookends.get("enabled"):
        blockers.append("configured transmission frontmatter requires independent hydrated page/native witness")
    if not blocks:
        blockers.append("original PDF frontmatter declares no independently interpreted text")
    return NativeContentContract(
        artifact_id, ((path, hashlib.sha256(config_bytes).hexdigest()),), tuple(blocks), tuple(blockers)
    )
