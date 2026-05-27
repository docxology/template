# Script Notes

Scripts contain no business logic — parse arguments, resolve paths, call `../src/`
functions, print output paths to stdout for manifest collection. Use
`MPLBACKEND=Agg` and fixed seeds. The `z_`-prefixed script runs last in
lexicographic analysis order (it depends on prior outputs).
