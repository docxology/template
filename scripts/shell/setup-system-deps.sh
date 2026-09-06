#!/usr/bin/env bash
################################################################################
# setup-system-deps.sh — one-shot installer for the pipeline's system tools
#
# Installs and verifies the external executables the rendering pipeline needs
# but uv cannot provision: pandoc, a XeLaTeX TeX distribution, and the LaTeX
# packages that minimal distributions (BasicTeX, texlive-xetex) lack.
#
# Idempotent: every step checks current state first and skips work already
# done, so re-running after a partial install resumes cleanly.
#
# Fail-closed: when an install needs interactive elevation (sudo password,
# Homebrew cask prompt) and stdin is not a TTY, it prints the exact commands
# and exits 1 instead of hanging or half-installing. Run it from an
# interactive terminal when elevation is expected.
#
# Usage:
#   bash scripts/shell/setup-system-deps.sh            # install missing + verify
#   bash scripts/shell/setup-system-deps.sh --check    # verify only, install nothing
#
# uv bootstrap reuses shell_bootstrap.sh (pinned installer + SHA-256 check).
# Platform support: macOS (Homebrew), Debian/Ubuntu (apt-get), matching the
# documented prerequisites in START_HERE.md and the CI provisioning in
# .github/workflows/ci.yml.
################################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CHECK_ONLY=0
for arg in "$@"; do
    case "$arg" in
        --check) CHECK_ONLY=1 ;;
        -h|--help)
            sed -n '2,30p' "${BASH_SOURCE[0]}" | grep -E '^#( |$)' | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *)
            echo "ERROR: unknown argument '$arg' (supported: --check)" >&2
            exit 1
            ;;
    esac
done

info() { echo "✅ $*"; }
warn() { echo "⚠️  $*"; }
fail() { echo "❌ $*" >&2; }
die()  { fail "$1"; exit "${2:-1}"; }

# True when elevation may be requested without hanging: either we are root,
# sudo is passwordless, or stdin is an interactive TTY (sudo can prompt).
may_elevate() {
    [[ ${EUID} -eq 0 ]] && return 0
    sudo -n true 2>/dev/null && return 0
    [[ -t 0 ]] && return 0
    return 1
}

# LaTeX .sty files the pipeline's preamble needs (mirrors
# infrastructure/rendering/latex_validation.py). CORE stys ship with every
# TeX distribution; if one is missing the distribution itself is broken and
# the fix is a fuller distribution, not tlmgr.
CORE_STYS="amsmath amssymb amsfonts amsthm graphicx geometry float booktabs longtable array hyperref natbib"
EXTRA_STYS="multirow caption subcaption bm cleveref doi newunicodechar fancyvrb xcolor listings lmodern"

# tlmgr package name for a sty (three stys live inside differently named
# TeX Live packages; the rest match 1:1).
sty_to_tlmgr_pkg() {
    case "$1" in
        subcaption) echo "caption" ;;
        caption)    echo "caption" ;;
        bm)         echo "tools" ;;
        *)          echo "$1" ;;
    esac
}

# Collect missing stys: sets MISSING_EXTRA_TLMGR (space-separated tlmgr
# package names, deduplicated) and CORE_MISSING=1 when a core sty is absent.
audit_tex_packages() {
    MISSING_EXTRA_TLMGR=""
    CORE_MISSING=0
    local sty pkg
    for sty in ${CORE_STYS}; do
        if ! "$KPSEWHICH" "${sty}.sty" >/dev/null 2>&1; then
            warn "core LaTeX package missing: ${sty}.sty (distribution incomplete)"
            CORE_MISSING=1
        fi
    done
    for sty in ${EXTRA_STYS}; do
        if ! "$KPSEWHICH" "${sty}.sty" >/dev/null 2>&1; then
            pkg="$(sty_to_tlmgr_pkg "$sty")"
            case " ${MISSING_EXTRA_TLMGR} " in
                *" ${pkg} "*) ;;
                *) MISSING_EXTRA_TLMGR="${MISSING_EXTRA_TLMGR:+${MISSING_EXTRA_TLMGR} }${pkg}" ;;
            esac
        fi
    done
}

install_tex_packages_tlmgr() {
    # $1 = tlmgr binary path
    if ! may_elevate; then
        fail "LaTeX packages need elevation to install, but stdin is not interactive."
        echo "   Run these commands from a terminal with sudo available:" >&2
        echo "     sudo tlmgr update --self" >&2
        echo "     sudo tlmgr install ${MISSING_EXTRA_TLMGR}" >&2
        exit 1
    fi
    echo "Installing missing LaTeX packages: ${MISSING_EXTRA_TLMGR}"
    sudo "$1" update --self
    # Intentional word splitting: MISSING_EXTRA_TLMGR is a space-separated
    # package-name list (SC2086).
    # shellcheck disable=SC2086
    sudo "$1" install ${MISSING_EXTRA_TLMGR}
}

# Shared tail: uv presence + repo validator run.
verify_with_uv() {
    echo ""
    echo "=== Verification ==="
    info "pandoc $(pandoc --version | head -1)"
    info "xelatex $(xelatex --version | head -1)"
    (cd "$REPO_ROOT" && uv run python -m infrastructure.rendering.latex_package_validator) \
        || die "LaTeX package validator failed — see its report above"
    info "system dependencies verified end-to-end"
}

# ── uv ───────────────────────────────────────────────────────────────────────
# shellcheck source=scripts/shell/shell_bootstrap.sh
source "${REPO_ROOT}/scripts/shell/shell_bootstrap.sh"

if [[ ${CHECK_ONLY} -eq 1 ]]; then
    command -v uv >/dev/null 2>&1 || die "uv not found (required). Install: brew install uv, or the pinned installer in docs/operational/build/dependency-management.md"
else
    ensure_uv || die "could not provision uv — install it manually and re-run (see docs/operational/build/dependency-management.md)"
fi

# ── Platform detection ──────────────────────────────────────────────────────
OS="$(uname -s)"
case "$OS" in
    Darwin)  PLATFORM="macos" ;;
    Linux)   PLATFORM="linux" ;;
    *)       die "unsupported platform '$OS' — this script covers macOS and Debian/Ubuntu; see START_HERE.md for manual steps" ;;
esac

if [[ $CHECK_ONLY -eq 1 ]]; then
    echo "=== --check mode: verifying only, installing nothing ==="
    echo ""
    if command -v pandoc >/dev/null 2>&1; then
        info "pandoc $(pandoc --version | head -1)"
    else
        fail "pandoc not found"
        MISSING_PANDOC=1
    fi
    if command -v xelatex >/dev/null 2>&1; then
        info "xelatex $(xelatex --version | head -1)"
    else
        fail "xelatex not found"
        MISSING_XELATEX=1
    fi
    if [[ "$PLATFORM" == "macos" ]]; then
        KPSEWHICH="$(command -v kpsewhich || echo /Library/TeX/texbin/kpsewhich)"
    else
        KPSEWHICH="$(command -v kpsewhich || true)"
    fi
    if [[ -n "${KPSEWHICH:-}" && -x "${KPSEWHICH:-/nonexistent}" ]]; then
        audit_tex_packages
        if [[ ${CORE_MISSING} -eq 1 ]]; then
            fail "core LaTeX packages missing — reinstall a full TeX distribution (MacTeX, or texlive-xetex + texlive-latex-extra)"
            MISSING_TEX_PKG=1
        fi
        if [[ -n "$MISSING_EXTRA_TLMGR" ]]; then
            warn "missing optional-but-documented LaTeX packages (tlmgr names): ${MISSING_EXTRA_TLMGR}"
            MISSING_TEX_PKG=1
        fi
    else
        warn "kpsewhich not found — cannot audit LaTeX packages"
        MISSING_TEX_PKG=1
    fi
    echo ""
    if [[ "${MISSING_PANDOC:-0}" -eq 1 || "${MISSING_XELATEX:-0}" -eq 1 || "${MISSING_TEX_PKG:-0}" -eq 1 ]]; then
        die "verification failed — re-run without --check to install what is missing"
    fi
    verify_with_uv
    exit 0
fi

# ── Install mode ─────────────────────────────────────────────────────────────
if [[ "$PLATFORM" == "macos" ]]; then
    command -v brew >/dev/null 2>&1 \
        || die "Homebrew not found. Install it from https://brew.sh then re-run this script."

    # macOS TeX distros put everything under /Library/TeX/texbin, which a
    # fresh BasicTeX install does not add to the current shell's PATH.
    export PATH="/Library/TeX/texbin:${PATH}"

    if command -v pandoc >/dev/null 2>&1; then
        info "pandoc already present: $(pandoc --version | head -1)"
    else
        brew install pandoc
    fi

    if command -v xelatex >/dev/null 2>&1; then
        info "xelatex already present: $(xelatex --version | head -1)"
    else
        echo "Installing BasicTeX (~100 MB; MacTeX is the 4 GB full alternative: brew install --cask mactex)"
        if ! may_elevate; then
            fail "BasicTeX's installer needs an admin password, but stdin is not interactive."
            echo "   Run 'brew install --cask basictex' from a terminal, then re-run this script." >&2
            exit 1
        fi
        brew install --cask basictex
        hash -r
        command -v xelatex >/dev/null 2>&1 || warn "xelatex still not on PATH — open a new terminal so /Library/TeX/texbin is picked up, then re-run this script"
    fi

    KPSEWHICH="$(command -v kpsewhich || echo /Library/TeX/texbin/kpsewhich)"
    if [[ -x "$KPSEWHICH" ]]; then
        audit_tex_packages
        if [[ ${CORE_MISSING} -eq 1 ]]; then
            die "core LaTeX packages missing — the TeX distribution is incomplete; install full MacTeX (brew install --cask mactex)"
        fi
        if [[ -n "$MISSING_EXTRA_TLMGR" ]]; then
            TLMGR="$(command -v tlmgr || echo /Library/TeX/texbin/tlmgr)"
            install_tex_packages_tlmgr "$TLMGR"
            hash -r
        else
            info "all documented LaTeX packages already present"
        fi
    else
        warn "kpsewhich not found even after TeX install — open a new terminal and re-run this script"
    fi
else
    command -v apt-get >/dev/null 2>&1 \
        || die "apt-get not found — this script covers Debian/Ubuntu on Linux; see START_HERE.md for your distribution"

    if command -v pandoc >/dev/null 2>&1; then
        info "pandoc already present: $(pandoc --version | head -1)"
    else
        apt_install_pandoc=1
    fi

    if command -v xelatex >/dev/null 2>&1; then
        info "xelatex already present: $(xelatex --version | head -1)"
    else
        apt_install_tex=1
    fi

    if [[ "${apt_install_pandoc:-0}" -eq 1 || "${apt_install_tex:-0}" -eq 1 ]]; then
        if ! may_elevate; then
            fail "apt installs need elevation, but stdin is not interactive."
            echo "   Run from a terminal:" >&2
            echo "     sudo apt-get update" >&2
            echo "     sudo apt-get install -y pandoc texlive-xetex texlive-latex-extra texlive-bibtex-extra texlive-fonts-recommended texlive-latex-recommended lmodern fonts-dejavu" >&2
            exit 1
        fi
        sudo apt-get update
        sudo apt-get install -y ${apt_install_pandoc:+pandoc} \
            ${apt_install_tex:+texlive-xetex texlive-latex-extra texlive-bibtex-extra texlive-fonts-recommended texlive-latex-recommended lmodern fonts-dejavu}
    fi
fi

echo ""
if ! command -v uv >/dev/null 2>&1 && [[ "${PLATFORM}" == "linux" ]]; then
    warn "uv not found — 'uv sync' inside the pipeline bootstraps it via shell_bootstrap.sh on first run"
fi

# Sync the Python environment now that system tools exist.
(cd "$REPO_ROOT" && uv sync --quiet) || die "uv sync failed — resolve Python dependency issues and re-run"

verify_with_uv
