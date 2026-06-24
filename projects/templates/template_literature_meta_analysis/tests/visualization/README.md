# Visualization Tests (`tests/visualization/`)

Test suite validating correct `matplotlib` figure generation parameters. The suite focuses purely on structural execution stability using dummy matrices, actively avoiding aesthetic regressions by running strictly within local `Agg` parameters.

## Focus Areas

- Temporary generation of 16 PNG asset structures ensuring no OS-level segmentation faults or `X11` binding bugs interrupt runtime.
- Verification that custom Colorblind safe configurations do not drop keys mapped loosely against standard Pandas dataframes.

## Running the Tests

```bash
uv run pytest tests/visualization/ -v
```

See **[AGENTS.md](AGENTS.md)** for detailed module logic verification protocols spanning headless CI integration requirements.
