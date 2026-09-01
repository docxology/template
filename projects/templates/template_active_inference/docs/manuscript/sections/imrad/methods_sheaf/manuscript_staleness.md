The `manuscript_staleness` fragment closes the hydration loop. `output/reports/manuscript_staleness_report.json` checks {{manuscript_staleness_row_count}} manuscript token bindings against the current generated variables after resolved markdown is written; the pass flag is `{{manuscript_staleness_all_fresh}}`.

This is a publication-systems claim, not a domain result. A stale hydrated value, unresolved token, or missing resolved section becomes a validation failure before PDF or web outputs are accepted.
