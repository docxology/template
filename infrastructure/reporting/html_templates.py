"""HTML templates for report generation.

Provides reusable HTML templates for various report types.
"""

from typing import Any

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def shared_css() -> str:
    """Return the shared design-token + dark-mode CSS block.

    This is the single source of truth for the modernized HTML design system:
    a ``:root`` custom-property block (``--brand-1`` … ``--mono``) plus the
    ``@media (prefers-color-scheme: dark)`` overrides. Every generated HTML
    surface (report templates, pipeline reports, interactive dashboards, and
    the web renderer) embeds this string so they share one token source.

    Output uses single braces (plain CSS) so callers can either embed it
    verbatim or escape braces for ``str.format``-based templates. The string is
    fully static — no timestamps or randomness — to keep generated output
    deterministic.

    Returns:
        CSS string containing the ``:root`` token block and the
        ``prefers-color-scheme: dark`` override block.
    """
    return """:root {
            --brand-1: #5b6ee0;
            --brand-2: #7048c4;
            --bg: #eef1f6;
            --surface: #ffffff;
            --surface-alt: #f6f8fb;
            --text: #1f2733;
            --text-muted: #5a6573;
            --border: #e3e8ef;
            --border-strong: #cdd5e0;
            --radius: 10px;
            --radius-pill: 999px;
            --shadow: 0 1px 3px rgba(16,24,40,0.08), 0 8px 24px rgba(16,24,40,0.06);
            --space: 1.5rem;
            --ok-bg: #d6f3e0; --ok-fg: #0f5132;
            --fail-bg: #fbdcdc; --fail-fg: #842029;
            --warn-bg: #fdeecb; --warn-fg: #664d03;
            --mono: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
        }
        @media (prefers-color-scheme: dark) {
            :root {
                --bg: #0f1420;
                --surface: #161c2b;
                --surface-alt: #1d2638;
                --text: #e6eaf2;
                --text-muted: #9aa6b8;
                --border: #2a3447;
                --border-strong: #3a465c;
                --shadow: 0 1px 3px rgba(0,0,0,0.4), 0 8px 24px rgba(0,0,0,0.35);
                --ok-bg: #123524; --ok-fg: #7ee2a8;
                --fail-bg: #3a1518; --fail-fg: #f3a3a3;
                --warn-bg: #3a2e08; --warn-fg: #f0d488;
            }
        }"""


def get_base_html_template() -> str:
    """Get base HTML template with styles.

    Consumes :func:`shared_css` for the design-token + dark-mode block so the
    template stays in lock-step with every other HTML surface.

    Returns:
        Base HTML template string
    """
    # ``shared_css()`` returns plain CSS (single braces); escape them so the
    # surrounding ``str.format`` template (which uses ``{title}`` etc.) leaves
    # the CSS untouched. Behavior is identical to the previous inline block.
    tokens_css = shared_css().replace("{", "{{").replace("}", "}}")
    return (
        """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="light dark">
    <title>{title}</title>
    <style>
        /* Design tokens — single source of truth; dark-mode overrides below.
           Static template (deterministic output): no timestamps or randomness. */
        """
        + tokens_css
        + """
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: var(--text);
            background: var(--bg);
            padding: var(--space);
            -webkit-font-smoothing: antialiased;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: var(--surface);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, var(--brand-1) 0%, var(--brand-2) 100%);
            color: #fff;
            padding: calc(var(--space) * 1.3);
        }}
        .header h1 {{
            margin: 0 0 0.5rem 0;
            font-size: clamp(1.5rem, 1rem + 2vw, 1.9rem);
            letter-spacing: -0.01em;
        }}
        .header p {{
            margin: 0.25rem 0;
            opacity: 0.92;
        }}
        .content {{
            padding: calc(var(--space) * 1.3);
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: var(--space);
            margin: var(--space) 0;
        }}
        .summary-card {{
            background: var(--surface-alt);
            padding: var(--space);
            border-radius: var(--radius);
            border-left: 4px solid var(--brand-1);
            transition: transform 0.12s ease, box-shadow 0.12s ease;
        }}
        .summary-card:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow);
        }}
        .summary-card h3 {{
            font-size: 0.72rem;
            text-transform: uppercase;
            color: var(--text-muted);
            margin: 0 0 0.6rem 0;
            letter-spacing: 0.06em;
        }}
        .summary-card .value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--text);
            font-variant-numeric: tabular-nums;
        }}
        .section {{
            margin: calc(var(--space) * 1.5) 0;
        }}
        .section h2 {{
            color: var(--text);
            margin: 0 0 var(--space) 0;
            padding-bottom: 0.6rem;
            border-bottom: 2px solid var(--border);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: var(--space) 0;
        }}
        th {{
            background: var(--surface-alt);
            padding: 0.75rem;
            text-align: left;
            font-weight: 600;
            color: var(--text-muted);
            border-bottom: 2px solid var(--border-strong);
            position: sticky;
            top: 0;
        }}
        td {{
            padding: 0.75rem;
            border-bottom: 1px solid var(--border);
            font-variant-numeric: tabular-nums;
        }}
        tr:hover {{
            background: var(--surface-alt);
        }}
        code, pre {{ font-family: var(--mono); }}
        .status-badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: var(--radius-pill);
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.02em;
        }}
        .status-passed {{
            background: var(--ok-bg);
            color: var(--ok-fg);
        }}
        .status-failed {{
            background: var(--fail-bg);
            color: var(--fail-fg);
        }}
        .status-warning {{
            background: var(--warn-bg);
            color: var(--warn-fg);
        }}
        .footer {{
            background: var(--surface-alt);
            padding: var(--space);
            text-align: center;
            color: var(--text-muted);
            font-size: 0.875rem;
            border-top: 1px solid var(--border);
        }}
        @media (max-width: 640px) {{
            body {{ padding: 0.75rem; }}
            .header, .content {{ padding: var(--space); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {header}
        <div class="content">
            {content}
        </div>
        {footer}
    </div>
</body>
</html>"""
    )


def render_summary_cards(cards: list[dict[str, Any]]) -> str:
    """Render summary cards HTML.

    Args:
        cards: List of card dictionaries with 'title' and 'value'

    Returns:
        HTML string for summary cards
    """
    html = '<div class="summary-grid">\n'
    for card in cards:
        html += f"""        <div class="summary-card">
            <h3>{card["title"]}</h3>
            <div class="value">{card["value"]}</div>
        </div>
"""
    html += "    </div>"
    return html


def render_table(headers: list[str], rows: list[list[str]]) -> str:
    """Render HTML table.

    Args:
        headers: List of header names
        rows: List of row data (each row is a list of cell values)

    Returns:
        HTML string for table
    """
    html = "<table>\n    <thead>\n        <tr>\n"
    for header in headers:
        html += f"            <th>{header}</th>\n"
    html += "        </tr>\n    </thead>\n    <tbody>\n"

    for row in rows:
        html += "        <tr>\n"
        for cell in row:
            html += f"            <td>{cell}</td>\n"
        html += "        </tr>\n"

    html += "    </tbody>\n</table>"
    return html
