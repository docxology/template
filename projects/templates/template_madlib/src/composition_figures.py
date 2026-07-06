from __future__ import annotations

from .config import MadlibConfig
from .figure_specs import build_group_figure_markdown


def build_methods_figure_markdown(config: MadlibConfig) -> str:
    return build_group_figure_markdown(
        config,
        "methods",
        disabled_message="Method pipeline visualization is disabled by `madlib.visualizations`.",
    )


def build_results_figure_markdown(config: MadlibConfig) -> str:
    return build_group_figure_markdown(config, "results", disabled_message="")


def build_configuration_figure_markdown(config: MadlibConfig) -> str:
    return build_group_figure_markdown(
        config,
        "configuration",
        disabled_message="Configured-field visualizations are disabled by `madlib.visualizations.enabled`.",
    )


def build_evaluation_figure_markdown(config: MadlibConfig) -> str:
    return build_group_figure_markdown(
        config,
        "evaluation",
        disabled_message="Quality-gate visualization is disabled by `madlib.visualizations`.",
    )
