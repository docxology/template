"""Advanced public boundary backed by the declared canonical literature engine."""

from template_literature_meta_analysis.literature.bibliography import (
    _LATEX_SPECIALS as _LATEX_SPECIALS,
)
from template_literature_meta_analysis.literature.bibliography import (
    _PREPRINT_ENTRY_TYPE as _PREPRINT_ENTRY_TYPE,
)
from template_literature_meta_analysis.literature.bibliography import (
    _TITLE_STOP_WORDS as _TITLE_STOP_WORDS,
)
from template_literature_meta_analysis.literature.bibliography import (
    _VERBATIM_FIELDS as _VERBATIM_FIELDS,
)
from template_literature_meta_analysis.literature.bibliography import (
    BibEntry as BibEntry,
)
from template_literature_meta_analysis.literature.bibliography import (
    _disambiguate_key as _disambiguate_key,
)
from template_literature_meta_analysis.literature.bibliography import (
    _escape_latex as _escape_latex,
)
from template_literature_meta_analysis.literature.bibliography import (
    _extract_surname as _extract_surname,
)
from template_literature_meta_analysis.literature.bibliography import (
    _normalize_field_value as _normalize_field_value,
)
from template_literature_meta_analysis.literature.bibliography import (
    _slugify_token as _slugify_token,
)
from template_literature_meta_analysis.literature.bibliography import (
    _title_key_word as _title_key_word,
)
from template_literature_meta_analysis.literature.bibliography import (
    corpus_to_bibtex as corpus_to_bibtex,
)
from template_literature_meta_analysis.literature.bibliography import (
    generate_citation_key as generate_citation_key,
)
from template_literature_meta_analysis.literature.bibliography import (
    paper_to_bibentry as paper_to_bibentry,
)
from template_literature_meta_analysis.literature.bibliography import (
    render_entries as render_entries,
)
from template_literature_meta_analysis.literature.bibliography import (
    render_entry as render_entry,
)

__all__ = [
    "_LATEX_SPECIALS",
    "_PREPRINT_ENTRY_TYPE",
    "_TITLE_STOP_WORDS",
    "_VERBATIM_FIELDS",
    "BibEntry",
    "_disambiguate_key",
    "_escape_latex",
    "_extract_surname",
    "_normalize_field_value",
    "_slugify_token",
    "_title_key_word",
    "corpus_to_bibtex",
    "generate_citation_key",
    "paper_to_bibentry",
    "render_entries",
    "render_entry",
]
