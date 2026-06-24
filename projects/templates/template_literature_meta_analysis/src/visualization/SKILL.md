---
name: Data Visualization Library
description: Orchestrates matplotlib and seaborn pipelines for rendering figures.
---

# Instructions

You are interacting with the `src/visualization/` rendering layer.

## Agentic Interface (MCP Strategy)

1. **Accessibility Standards Base**: Implement a 16pt or larger font size floor for all axes, ticks, titles, and legends to cater to low-vision visibility in final PDFs. Avoid pure red/green contrast gradients.
2. **Deterministic Geometries**: Provide static seeding (`random_state=42`) for algorithmic layouts like `spring_layout` in NetworkX spatial mappings. Layouts should not drastically warp across identical runs.
3. **Headless Safety Execution**: Validate that figure generations don't invoke interactive display calls (`plt.show()`) mid-pipeline. The `Agg` backend must be functional.
