# Reclaim native runner capacity

Run this composite on a hosted Linux runner before native allocation. It removes the fixed toolchain directories listed in [action.yml](action.yml), reports reclaimed and remaining space in KiB, and warns when remaining space is below 10 GiB. A retained directory is reported as `reclaim-retained`; the action does not produce acceptance evidence.

See [AGENTS.md](AGENTS.md) for maintenance guidance.
