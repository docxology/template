"""Runner scripts — pipeline execution entry points.

Thin orchestrators that invoke the pipeline for one or many projects.

Modules:

    execute_pipeline       – single-project pipeline runner
    execute_multi_project  – multi-project pipeline runner (serial / parallel)
    run_matrix             – reproducible project × stage matrix runner
"""

__all__ = [
    "execute_pipeline",
    "execute_multi_project",
    "run_matrix",
]
