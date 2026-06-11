"""Maintenance and operator-tooling scripts.

Thin orchestrators for repository maintenance tasks that are NOT part of the
numbered build pipeline (00–10) and NOT validation gates (see ``scripts/gates/``).
Each delegates its logic to an ``infrastructure/`` module and is run directly,
e.g. ``uv run python scripts/maintenance/manage_workspace.py status``.

Modules:
    batch_cogsec_improve: Batch source-improvement orchestrator.
    codegraph_local: Local CodeGraph index helper commands.
    manage_workspace: uv workspace status / add-package helper.
    merge_test_supplements: Merge pytest supplement files into a canonical module.
    organize_executive_outputs: Tidy multi-project executive report outputs.
    render_working_projects: Render private-sidecar working projects on demand.
    rerender_working_pdfs: Re-render working-project PDFs with a status rubric.
    setup_pre_commit: Install/refresh the pre-commit hook set.
    show_project_info: Print metadata for a discovered project.
"""
