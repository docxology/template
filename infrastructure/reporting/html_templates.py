"""HTML templates for report generation.

Provides reusable HTML templates for various report types.
"""
from __future__ import annotations

from typing import Any, Dict


def get_base_html_template() -> str:
    """Get base HTML template with styles.
    
    Returns:
        Base HTML template string
    """
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 28px;
        }}
        .header p {{
            margin: 5px 0;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }}
        .summary-card h3 {{
            font-size: 12px;
            text-transform: uppercase;
            color: #666;
            margin: 0 0 10px 0;
            letter-spacing: 0.5px;
        }}
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        .section {{
            margin: 30px 0;
        }}
        .section h2 {{
            color: #333;
            margin: 0 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #e9ecef;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #e9ecef;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}
        .status-passed {{
            background: #d4edda;
            color: #155724;
        }}
        .status-failed {{
            background: #f8d7da;
            color: #721c24;
        }}
        .status-warning {{
            background: #fff3cd;
            color: #856404;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 14px;
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


def render_summary_cards(cards: list[Dict[str, Any]]) -> str:
    """Render summary cards HTML.
    
    Args:
        cards: List of card dictionaries with 'title' and 'value'
        
    Returns:
        HTML string for summary cards
    """
    html = '<div class="summary-grid">\n'
    for card in cards:
        html += f"""        <div class="summary-card">
            <h3>{card['title']}</h3>
            <div class="value">{card['value']}</div>
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
    html = '<table>\n    <thead>\n        <tr>\n'
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




