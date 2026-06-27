# Static site deployment

Deploy generated docs or manuscript sites to GitHub Pages, Cloudflare Pages, or Netlify (opt-in).

## Entry points

| Symbol | Module | Role |
| --- | --- | --- |
| `get_adapter` | `registry.py` | Return adapter for a `SiteHosting` target |
| `GitHubPagesAdapter` | `github_pages.py` | Push to `gh-pages` branch |
| `CloudflarePagesAdapter` | `cloudflare_pages.py` | Direct upload via Cloudflare API |
| `NetlifyAdapter` | `netlify.py` | Deploy via Netlify deploy API |

## Usage

```python
from pathlib import Path
from infrastructure.publishing.static_site import (
    SiteHosting,
    SiteDeployConfig,
    get_adapter,
)

config = SiteDeployConfig(
    hosting=SiteHosting.GITHUB_PAGES,
    site_dir=Path("output/my_project/site"),
    project_name="my_project",
    dry_run=True,          # default — no network calls
)

adapter = get_adapter(SiteHosting.GITHUB_PAGES)
result = adapter.deploy(config)
print(result.success, result.url)
```

### Cloudflare Pages

```python
config = SiteDeployConfig(
    hosting=SiteHosting.CLOUDFLARE_PAGES,
    site_dir=Path("output/my_project/site"),
    project_name="my_project",
    dry_run=False,         # requires CLOUDFLARE_API_TOKEN
)
adapter = get_adapter(SiteHosting.CLOUDFLARE_PAGES)
result = adapter.deploy(config)
```

### Netlify

```python
config = SiteDeployConfig(
    hosting=SiteHosting.NETLIFY,
    site_dir=Path("output/my_project/site"),
    project_name="my_project",
    dry_run=False,
    production=True,       # promote to production URL
)
adapter = get_adapter(SiteHosting.NETLIFY)
result = adapter.deploy(config)
```

## Credentials

| Provider | Env var |
| --- | --- |
| GitHub Pages | `GITHUB_TOKEN` |
| Cloudflare Pages | `CLOUDFLARE_API_TOKEN` |
| Netlify | `NETLIFY_AUTH_TOKEN` |

## Related

- [`AGENTS.md`](AGENTS.md) — module internals and file list
- [`../archival/`](../archival/) — multi-target archival mirror
