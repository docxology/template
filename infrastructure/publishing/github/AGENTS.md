# `infrastructure/publishing/github/`

GitHub Releases REST API helper.

## Public API

```python
from infrastructure.publishing.github import create_github_release
```

### `create_github_release`

```python
create_github_release(
    tag_name: str,
    release_name: str,
    description: str,
    assets: list[Path],
    token: str,
    repo: str,
    *,
    base_url: str = "https://api.github.com",
) -> str
```

Returns the release HTML URL. Non-existent assets are skipped with a warning.

## Environment variables

| Variable | Use |
| --- | --- |
| `GITHUB_TOKEN` | Personal access token with `repo` scope |

## Tests

```bash
uv run pytest tests/infra_tests/publishing/test_platforms.py::TestCreateGithubRelease -v
```

## See also

- [`README.md`](README.md)
- [`../platforms.py`](../platforms.py) — backwards-compatible re-export
