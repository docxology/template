# Conclusion

This exemplar shows how pipeline tracks, sheaf fragment registries, and IMRAD manuscript sections fit together: analytical oracles and pymdp rollouts produce measured artifacts; composition binds 12 flat sections from 10 fragment tracks; coverage JSON and the first-page heatmap report 42 present / 42 bound / 0 missing cells.

Strict validation (`compose_manuscript.py --validate-only --strict`) fails on gray matrix cells, keeping the appendix full-track proof and Results sections trustworthy for downstream PDF rendering. The T-maze harness runs in `state_inference` mode with config hash `ea4b126a9c22f22f`; sweep RMSE 0 nats bounds analytical–empirical agreement on the toy.
