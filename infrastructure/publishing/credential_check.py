"""Non-destructive, read-only credential verification for publishing platforms.

This answers one question reproducibly: *can we actually publish?* For each
platform that exposes a read-only identity/verify endpoint, it sends a single
GET with the configured token and reports whether the credential authenticates.
It never writes, uploads, or mutates anything.

This is deliberately separate from :mod:`status_report`: credential presence is
machine-specific and volatile, so it belongs in an operational check, not in a
committed README. Run it before a release to confirm tokens are live.

Token values are never printed — only HTTP status and public identity fields
(login, account name) returned by the provider.

Usage::

    uv run python -m infrastructure.publishing.credential_check          # uses os.environ / .env
    uv run python -m infrastructure.publishing.credential_check --only github zenodo

Public API:
    * :data:`PROBES` — the probe catalogue.
    * :func:`run_probe` — probe a single platform (URL override supported for tests).
    * :func:`check_all` — probe every platform with credentials present.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlsplit, urlunsplit

REQUEST_TIMEOUT = 20


@dataclass(frozen=True)
class PlatformProbe:
    """A read-only auth probe for one platform."""

    name: str
    env_vars: tuple[str, ...]
    url: str  # may contain "{token}" for query-param auth
    auth_header: str | None  # e.g. "Bearer {token}"; None when token is in the URL
    identity_path: tuple[str, ...]  # JSON key path to a public identity value
    note: str = ""


@dataclass(frozen=True)
class ProbeResult:
    """Outcome of a single probe."""

    name: str
    status: str  # "pass" | "fail" | "skipped" | "no-endpoint"
    http_status: int | None
    identity: str | None
    env_var: str | None
    detail: str

    @property
    def ok(self) -> bool:
        return self.status == "pass"


# Probe catalogue. env_vars are tried in order; the first present wins.
PROBES: tuple[PlatformProbe, ...] = (
    PlatformProbe(
        "github",
        ("GITHUB_TOKEN",),
        "https://api.github.com/user",
        "Bearer {token}",
        ("login",),
    ),
    PlatformProbe(
        "huggingface_hub",
        ("HUGGINGFACE_TOKEN", "HF_TOKEN"),
        "https://huggingface.co/api/whoami-v2",
        "Bearer {token}",
        ("name",),
    ),
    PlatformProbe(
        "osf",
        ("OSF_TOKEN",),
        "https://api.osf.io/v2/users/me/",
        "Bearer {token}",
        ("data", "attributes", "full_name"),
    ),
    PlatformProbe(
        "ipfs_pinata",
        ("PINATA_JWT",),
        "https://api.pinata.cloud/data/testAuthentication",
        "Bearer {token}",
        ("message",),
    ),
    PlatformProbe(
        "zenodo",
        ("ZENODO_API_TOKEN", "ZENODO_PROD_TOKEN", "ZENODO_TOKEN"),
        "https://zenodo.org/api/deposit/depositions?size=1&access_token={token}",
        None,
        (),
    ),
    PlatformProbe(
        "netlify",
        ("NETLIFY_AUTH_TOKEN",),
        "https://api.netlify.com/api/v1/user",
        "Bearer {token}",
        ("email",),
    ),
    PlatformProbe(
        "cloudflare_pages",
        ("CLOUDFLARE_API_TOKEN",),
        "https://api.cloudflare.com/client/v4/user/tokens/verify",
        "Bearer {token}",
        ("result", "status"),
    ),
    PlatformProbe(
        "pypi",
        ("PYPI_TOKEN", "TESTPYPI_TOKEN"),
        "",
        None,
        (),
        note="No read-only identity endpoint; token validated at upload time.",
    ),
)


def _select_token(probe: PlatformProbe, env: Mapping[str, str]) -> tuple[str | None, str | None]:
    for var in probe.env_vars:
        val = env.get(var)
        if val:
            return val.strip(), var
    return None, None


def _dig(payload: Any, path: tuple[str, ...]) -> str | None:
    cur = payload
    for key in path:
        if isinstance(cur, Mapping) and key in cur:
            cur = cur[key]
        else:
            return None
    return None if cur is None else str(cur)


def _http_get_json(url: str, headers: dict[str, str]) -> tuple[int, Any]:
    parts = urlsplit(url)
    localhost = parts.hostname in {"127.0.0.1", "::1", "localhost"}
    if parts.scheme != "https" and not (parts.scheme == "http" and localhost):
        return 0, {"_error": f"blocked unsupported credential probe URL scheme: {parts.scheme or '<missing>'}"}

    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as resp:  # nosec B310 - scheme/host validated above.
            body = resp.read().decode("utf-8", "replace")
            return resp.status, _try_json(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        return exc.code, _try_json(body)
    except (urllib.error.URLError, OSError) as exc:
        return 0, {"_error": f"{type(exc).__name__}: {exc}"}


def _try_json(body: str) -> Any:
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"_raw": body[:200]}


def _apply_url_override(url: str, override_base: str | None) -> str:
    """Replace scheme+host of ``url`` with ``override_base`` (for tests)."""
    if not override_base:
        return url
    parts = urlsplit(url)
    base = urlsplit(override_base)
    return urlunsplit((base.scheme, base.netloc, parts.path, parts.query, parts.fragment))


def _identity_for(probe: PlatformProbe, payload: Any) -> str | None:
    if probe.identity_path:
        return _dig(payload, probe.identity_path)
    if isinstance(payload, list):
        return f"{len(payload)} item(s) visible"
    return "authenticated"


def run_probe(
    probe: PlatformProbe,
    env: Mapping[str, str],
    *,
    override_base: str | None = None,
) -> ProbeResult:
    """Probe a single platform. ``override_base`` redirects the host (tests)."""
    token, env_var = _select_token(probe, env)
    if not probe.url:
        return ProbeResult(probe.name, "no-endpoint", None, None, env_var, probe.note or "no read-only endpoint")
    if not token:
        return ProbeResult(probe.name, "skipped", None, None, None, f"no credential set ({' / '.join(probe.env_vars)})")

    url = _apply_url_override(probe.url.format(token=token), override_base)
    headers: dict[str, str] = {"User-Agent": "publishing-credential-check"}
    if probe.auth_header:
        headers["Authorization"] = probe.auth_header.format(token=token)

    http_status, payload = _http_get_json(url, headers)
    if 200 <= http_status < 300:
        return ProbeResult(probe.name, "pass", http_status, _identity_for(probe, payload), env_var, "ok")
    detail = ""
    if isinstance(payload, Mapping):
        detail = str(payload.get("message") or payload.get("_error") or payload)[:160]
    return ProbeResult(probe.name, "fail", http_status, None, env_var, detail)


def check_all(
    env: Mapping[str, str] | None = None,
    *,
    only: list[str] | None = None,
    override_base: str | None = None,
) -> list[ProbeResult]:
    """Probe every catalogued platform; filter with ``only``."""
    environ = env if env is not None else os.environ
    selected = [p for p in PROBES if (only is None or p.name in only)]
    return [run_probe(p, environ, override_base=override_base) for p in selected]


_BADGE = {"pass": "✅", "fail": "❌", "skipped": "⚪", "no-endpoint": "•"}


def format_results(results: list[ProbeResult]) -> str:
    lines = ["Publishing credential check (read-only, no writes):", ""]
    for r in results:
        badge = _BADGE.get(r.status, "?")
        http = f"HTTP {r.http_status}" if r.http_status else ""
        ident = r.identity or r.detail
        lines.append(f"  {badge} {r.name:18} {r.status:11} {http:9} {ident}")
    passed = sum(1 for r in results if r.status == "pass")
    failed = sum(1 for r in results if r.status == "fail")
    lines.append("")
    lines.append(f"  {passed} passed, {failed} failed, {len(results) - passed - failed} skipped/n-a")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI: probe credentials and exit non-zero if any present credential fails."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m infrastructure.publishing.credential_check",
        description="Read-only verification that publishing credentials authenticate.",
    )
    parser.add_argument("--only", nargs="*", default=None, help="Restrict to platform names")
    parser.add_argument("--env-file", default=None, help="Load KEY=VALUE lines from this file first")
    args = parser.parse_args(argv)

    env = dict(os.environ)
    if args.env_file:
        from pathlib import Path

        path = Path(args.env_file)
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    env.setdefault(key.strip(), val.strip())

    results = check_all(env, only=args.only)
    print(format_results(results))
    return 1 if any(r.status == "fail" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
