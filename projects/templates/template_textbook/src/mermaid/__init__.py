"""Mermaid diagram sources and rendering for the template textbook.

``diagrams`` holds the diagram source strings (data-driven from
``diagram_specs.yaml``); ``renderer`` converts them to PNG via the Mermaid CLI
(``mmdc``) when available and falls back to writing the ``.mmd`` source so the
build never hard-fails on a missing optional tool.
"""
