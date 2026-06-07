`sheaf-track:scholarship` binds `output/data/scholarship_source_matrix.json` into
the appendix proof row. The appendix claim is exactly
{{scholarship_source_count}} connected source rows with connected status
`{{scholarship_sources_connected}}`; each row names a bibliography key, method
role, manuscript section, registered track set, evidence artifact, and
claim-boundary statement. The row set includes
{{scholarship_quantitative_method_role_count}} quantitative/statistical or
visualization-quality method roles, including {{visualization_statistics_backed_count}}
statistically backed figures with bridge status
`{{visualization_statistics_bridge_ok}}`. The explicit crosswalk has
{{statistical_visualization_bridge_row_count}} rows and
{{statistical_visualization_bridge_source_count}} statistical source links; every
row is referenced in the manuscript
(`{{statistical_visualization_bridge_all_referenced}}`), and every such
reference section is manifest-bound to sheaf tracks
(`{{statistical_visualization_bridge_references_sheaf_bound}}`) with a
visualization track present
(`{{statistical_visualization_bridge_references_visualization_bound}}`). This
binds statistics and figure-quality claims to generated artifacts rather than
bibliography authority.

The visualization registry is also now a paper-integration object: role metadata
complete `{{visualization_intent_metadata_complete}}`, paper claims complete
`{{visualization_paper_claims_complete}}`, and section bindings complete
`{{visualization_figures_section_bound}}`. Those flags are read from the saved
visualization-quality audit and then rechecked through the semantic sheaf
restrictions.
