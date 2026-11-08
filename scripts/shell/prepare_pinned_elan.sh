#!/usr/bin/env bash
# Sourced inside hosted preparation so the caller's original clock stays intact.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    printf 'Source this helper from its existing hosted preparation step.\n' >&2
    exit 2
fi

_template_prepare_pinned_elan() {
    local asset size digest destination archive version had_xtrace=false
    case "$-" in *x*) had_xtrace=true; set +x ;; esac
    case "$RUNNER_OS/$RUNNER_ARCH" in
        Linux/X64)
            asset=529114798
            size=4996571
            digest=42b94d4244e8353142c456ec0e4ca6528fd898a6c604d4059f494e706e431f63
            ;;
        Linux/ARM64)
            asset=529114794
            size=5131114
            digest=05febd124d84ebf994b2e7479922a5650b1e950c17ae3bd1ddd776b65bb72bf9
            ;;
        macOS/X64)
            asset=529120381
            size=2330818
            digest=8a340b309d8ed2e96f930761fa223b3af57a38f5d253b53ac90293c9516f8cd4
            ;;
        macOS/ARM64)
            asset=529120756
            size=2190845
            digest=7ad829861392c718dfebde3a83b5c8508df47be02af68894b094b0b3952616e5
            ;;
        *) printf 'Unsupported Elan host: %s/%s\n' "$RUNNER_OS" "$RUNNER_ARCH" >&2; return 1 ;;
    esac
    destination=$(mktemp -d "$RUNNER_TEMP/template-elan-4.2.4.XXXXXX")
    archive="$destination/runtime.tar.gz"
    curl --fail --location --header 'Accept: application/octet-stream' \
        --header "Authorization: Bearer $GH_TOKEN" --proto '=https' --proto-redir '=https' \
        --retry "${TEMPLATE_ELAN_DOWNLOAD_RETRIES:-2}" \
        --max-time "${TEMPLATE_ELAN_DOWNLOAD_TIMEOUT_SECONDS:-60}" --output "$archive" \
        "https://api.github.com/repos/leanprover/elan/releases/assets/$asset"
    unset GH_TOKEN GITHUB_TOKEN
    if [ "$had_xtrace" = true ]; then set -x; fi
    test "$(wc -c < "$archive" | tr -d '[:space:]')" = "$size"
    echo "$digest  $archive" | shasum -a 256 --check --status
    tar -xzf "$archive" -C "$destination" elan-init
    test -f "$destination/elan-init" && test ! -L "$destination/elan-init"
    test -x "$destination/elan-init"
    "$destination/elan-init" -y --no-modify-path --default-toolchain none
    version=$("$HOME/.elan/bin/elan" --version)
    test "${version%% (*}" = 'elan 4.2.4'
    printf '%s\n' "$version"
    export PATH="$HOME/.elan/bin:$PATH"
    echo "$HOME/.elan/bin" >> "$GITHUB_PATH"
}

_template_prepare_pinned_elan
unset -f _template_prepare_pinned_elan
