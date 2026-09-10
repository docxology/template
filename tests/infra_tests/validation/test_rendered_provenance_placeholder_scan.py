"""Rendered publication provenance: placeholder-token scan and source publication mode."""

from __future__ import annotations
import subprocess
from pathlib import Path
from infrastructure.validation.publication.audit import (
    AuditContext,
    build_publication_audit,
    check_placeholder_tokens,
)
from tests._support.projects import write_doc
from tests.infra_tests.validation._rendered_provenance_helpers import PROJECT, _green_project


def test_rendered_placeholder_scan_covers_grammar_without_duplicate_propagation(
    tmp_path: Path,
) -> None:
    project = _green_project(tmp_path)
    propagated = """# Abstract

Unresolved {{ RESULT_COUNT }}, {{analysis.mean:.4f}}, {{verify.*}}, {{#if result}}, ${DATASET:-missing}, and ${REQUIRED:?set it}.

Cross-reference {{#fig:overview}}, Mermaid KW{{For each keyword}}, and LaTeX ${(\beta)} remain legitimate.

Literal `{{INLINE_EXAMPLE}}`.
Literal double-backtick ``{{DOUBLE_INLINE_EXAMPLE}}``.

Paragraph continuation
    {{ PARAGRAPH_CONTINUATION_VISIBLE }}

- list item

    {{ LIST_PARAGRAPH_VISIBLE }}

After the list.

- list code item

        {{ NESTED_LIST_CODE_MASKED }}

```text
${FENCED_EXAMPLE:-default}
```

````markdown
```text
{{NESTED_BACKTICK_EXAMPLE}}
```
````

~~~~text
~~~text
{{NESTED_TILDE_EXAMPLE}}
~~~
~~~~

Mismatched inline bad`` {{ MISMATCHED_INLINE_VISIBLE }} ```

```lang`not-a-commonmark-fence
{{ INVALID_FENCE_VISIBLE }}
"""
    write_doc(project / "output" / "web" / "_combined_manuscript.md", propagated)
    write_doc(
        project / "output" / "manuscript" / "00_abstract.md",
        propagated + "\nHydrated-only unresolved {{ HYDRATED_ONLY }}.\n",
    )
    ctx = AuditContext(
        repo_root=tmp_path,
        project=PROJECT,
        project_root=project,
        rendered=True,
        include_drift=False,
    )

    findings = list(check_placeholder_tokens(ctx))

    tokens = [finding.message.rsplit(": ", 1)[1] for finding in findings]
    assert tokens == [
        "{{ RESULT_COUNT }}",
        "{{analysis.mean:.4f}}",
        "{{verify.*}}",
        "{{#if result}}",
        "${DATASET:-missing}",
        "${REQUIRED:?set it}",
        "{{ PARAGRAPH_CONTINUATION_VISIBLE }}",
        "{{ LIST_PARAGRAPH_VISIBLE }}",
        "{{ MISMATCHED_INLINE_VISIBLE }}",
        "{{ INVALID_FENCE_VISIBLE }}",
        "{{ HYDRATED_ONLY }}",
    ]
    assert len(tokens) == len(set(tokens))
    assert findings[0].path.endswith("output/web/_combined_manuscript.md")
    assert findings[-1].path.endswith("output/manuscript/00_abstract.md")

    parity_source = """Paragraph
    {{PARAGRAPH_VISIBLE}}

- item

    {{LIST_VISIBLE}}

- code item

        {{LIST_CODE_MASKED}}
"""
    pandoc = subprocess.run(
        ["pandoc", "--from=commonmark", "--to=html"],
        input=parity_source,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "{{PARAGRAPH_VISIBLE}}" in pandoc
    assert "{{LIST_VISIBLE}}" in pandoc
    assert "<code>  {{LIST_CODE_MASKED}}</code>" in pandoc


def test_source_publication_mode_permits_declared_hydratable_tokens(tmp_path: Path) -> None:
    _green_project(tmp_path)

    report = build_publication_audit(
        tmp_path,
        [PROJECT],
        rendered=False,
        include_drift=False,
    )

    assert all(finding.diagnostic_code != "PUBLICATION.PLACEHOLDER_TOKEN" for finding in report.findings)
