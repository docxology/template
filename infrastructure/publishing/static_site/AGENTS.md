# `infrastructure/publishing/static_site/`

Deploy generated static sites to GitHub Pages, Cloudflare Pages, or Netlify.

## Public API

```python
from infrastructure.publishing.static_site import (
    SiteHosting,
    SiteDeployConfig,
    SiteDeployResult,
    GitHubPagesAdapter,
    CloudflarePagesAdapter,
    NetlifyAdapter,
    STATIC_SITE_ADAPTERS,
    get_adapter,
)
```

### `SiteHosting` enum

```python
class SiteHosting(str, Enum):
    GITHUB_PAGES = "github_pages"
    CLOUDFLARE_PAGES = "cloudflare_pages"
    NETLIFY = "netlify"
```

### `SiteDeployConfig`

| Field | Default | Notes |
| --- | --- | --- |
| `hosting` | required | `SiteHosting` value |
| `site_dir` | required | Local directory of built static files |
| `project_name` | required | Used as site / repo / project identifier |
| `dry_run` | `True` | No network calls when `True` |
| `branch` | `"gh-pages"` | GitHub Pages only |
| `production` | `False` | Netlify: promote to production deploy |

`dry_run=True` is the default at every layer — accidental imports cannot trigger
real deployments.

### `SiteDeployResult`

Returned by every adapter: `success`, `hosting`, `url`, `deploy_id`, `error`.

### Adapters

| Class | Provider | Credential env |
| --- | --- | --- |
| `GitHubPagesAdapter` | GitHub Pages | `GITHUB_TOKEN` |
| `CloudflarePagesAdapter` | Cloudflare Pages | `CLOUDFLARE_API_TOKEN` |
| `NetlifyAdapter` | Netlify | `NETLIFY_AUTH_TOKEN` |

All adapters share the same interface: `deploy(config: SiteDeployConfig) -> SiteDeployResult`.

### Registry

```python
STATIC_SITE_ADAPTERS: dict[SiteHosting, type[...]]

adapter = get_adapter(SiteHosting.GITHUB_PAGES)
result = adapter.deploy(config)
```

## Files

| File | Purpose |
| --- | --- |
| `__init__.py` | Re-exports public symbols |
| `models.py` | `SiteHosting`, `SiteDeployConfig`, `SiteDeployResult` |
| `github_pages.py` | `GitHubPagesAdapter` |
| `cloudflare_pages.py` | `CloudflarePagesAdapter` |
| `netlify.py` | `NetlifyAdapter` |
| `registry.py` | `STATIC_SITE_ADAPTERS` dict + `get_adapter()` |

## Tests

```bash
uv run pytest tests/infra_tests/publishing/test_static_site.py -v
```

## See also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md) — publishing module overview
