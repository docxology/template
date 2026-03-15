# Migration from Flat Structure

> **Step-by-step guide** for migrating a flat `src/` project to the two-layer architecture

**Quick Reference:** [Two-Layer Architecture](two-layer-architecture.md) | [Decision Tree](decision-tree.md)

---

## When to Migrate

If you have an old project with a flat `src/` directory, migrating to the two-layer structure provides:

- Clear separation between infrastructure and project code
- Better code reuse across projects
- Independent test coverage requirements per layer
- Multi-project support

## Migration Steps

### 1. Create Packages

```bash
mkdir -p infrastructure projects/{name}/src
```

### 2. Move Modules

- Infrastructure modules → `infrastructure/`
- Project modules → `projects/{name}/src/`

**Use the [Decision Tree](decision-tree.md) to determine which layer each module belongs in:**

| Module Type | Destination |
|-------------|------------|
| PDF generation, validation, figure management | `infrastructure/` |
| Simulation algorithms, statistical analysis | `projects/{name}/src/` |
| Custom visualization for your data | `projects/{name}/src/` |
| Build artifact verification, generic utilities | `infrastructure/` |

### 3. Update Imports

```diff
- from example import calculate_average
+ from projects.{name}.src.example import calculate_average

# Build verification is handled by the validation module
```

### 4. Update Tests

- Infrastructure tests → `tests/infra_tests/`
- Project tests → `projects/{name}/tests/`
- Update `conftest.py` if needed

### 5. Validate

```bash
pytest tests/ projects/{name}/tests/ --cov=infrastructure --cov=projects/{name}/src
uv run python scripts/execute_pipeline.py --project {name} --core-only
```

## Post-Migration Checklist

- [ ] All imports updated to new paths
- [ ] Infrastructure tests pass independently
- [ ] Project tests pass independently
- [ ] No infrastructure → project imports exist
- [ ] Coverage requirements met (60% infra, 90% project)
- [ ] Pipeline executes successfully
- [ ] Documentation updated (`AGENTS.md`, `README.md` in each directory)

---

**Related Documentation:**

- [Two-Layer Architecture](two-layer-architecture.md) — Architecture overview
- [Decision Tree](decision-tree.md) — Code placement decisions
- [New Project Setup](../guides/new-project-setup.md) — Setting up a new project
