"""Generate source-bound publication record documentation for public exemplars."""

from __future__ import annotations

from infrastructure.documentation._publication_records_check import (
    _github_readme_source_rows,
    _local_source_path_rows,
    _markdown_table_rows,
    _publication_matrix_source_rows,
    _row_map_differences,
    check_publication_records_doc,
    write_publication_records_doc,
)
from infrastructure.documentation._publication_records_external import (
    _fetch_json,
    refresh_external_records,
)
from infrastructure.documentation._publication_records_load import (
    _authors_from_config,
    _load_json_mapping,
    _published_artifacts,
    _section_mapping,
    _sidecar_findings,
    load_publication_records,
)
from infrastructure.documentation._publication_records_render import (
    _markdown_link,
    _published_artifact_links,
    _relative_link,
    render_github_readme_publication_block,
    render_publication_records_doc,
    replace_github_readme_publication_block,
)
from infrastructure.documentation._publication_records_types import (
    README_BLOCK_BEGIN,
    README_BLOCK_END,
    PublicationRecord,
    _doi_url,
    _github_repo_url,
    _record_id_from_doi,
    _record_url_from_doi,
)

__all__ = [
    "PublicationRecord",
    "README_BLOCK_BEGIN",
    "README_BLOCK_END",
    "_authors_from_config",
    "_doi_url",
    "_fetch_json",
    "_github_readme_source_rows",
    "_github_repo_url",
    "_load_json_mapping",
    "_local_source_path_rows",
    "_markdown_link",
    "_markdown_table_rows",
    "_publication_matrix_source_rows",
    "_published_artifact_links",
    "_published_artifacts",
    "_record_id_from_doi",
    "_record_url_from_doi",
    "_relative_link",
    "_row_map_differences",
    "_section_mapping",
    "_sidecar_findings",
    "check_publication_records_doc",
    "load_publication_records",
    "refresh_external_records",
    "render_github_readme_publication_block",
    "render_publication_records_doc",
    "replace_github_readme_publication_block",
    "write_publication_records_doc",
]
