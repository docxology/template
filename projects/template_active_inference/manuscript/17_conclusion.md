# Conclusion

This exemplar shows how pipeline tracks, sheaf fragment registries, and IMRAD manuscript sections fit together: analytical oracles and pymdp rollouts produce measured artifacts; composition binds {{composed_section_count}} flat sections from {{sheaf_track_count}} fragment tracks; coverage JSON and the first-page heatmap report {{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing cells.

Strict validation (`compose_manuscript.py --validate-only --strict`) fails on gray matrix cells, keeping the appendix full-track proof and Results sections trustworthy for downstream PDF rendering. The T-maze harness runs in `{{pymdp_mode}}` mode with config hash `{{pymdp_config_hash}}`; sweep RMSE {{sweep_rmse_mi}} nats bounds analytical–empirical agreement on the toy.
