#!/usr/bin/env bash
# Install the pinned Elan launcher before the caller selects its Lean compiler.
set -euo pipefail

if [[ $(uname -s) != Linux || $(uname -m) != x86_64 ]]; then
    printf '%s\n' 'The pinned CI Elan asset requires Linux x86_64.' >&2
    exit 1
fi

work=$(mktemp -d "${RUNNER_TEMP:?RUNNER_TEMP is required}/ci-elan.XXXXXX")
trap 'rm -rf -- "$work"' EXIT
archive="$work/elan.tar.gz"
size=4996571
digest=42b94d4244e8353142c456ec0e4ca6528fd898a6c604d4059f494e706e431f63
asset_api=https://api.github.com/repos/leanprover/elan/releases/assets/529114798
asset_tag=https://github.com/leanprover/elan/releases/download/v4.2.4/elan-x86_64-unknown-linux-gnu.tar.gz

download() {
    curl --disable --fail --silent --show-error --location --max-redirs 5 \
        --proto '=https' --proto-redir '=https' --retry 2 --retry-max-time 75 \
        --connect-timeout 10 --max-time 40 --max-filesize "$size" \
        --output "$archive" "$@" &&
        [[ $(wc -c < "$archive") -eq $size ]] &&
        printf '%s  %s\n' "$digest" "$archive" | sha256sum --check --status
}

if ! download --header 'Accept: application/octet-stream' "$asset_api"; then
    download "$asset_tag" || {
        printf '%s\n' 'Could not retrieve the exact Elan v4.2.4 Linux x86_64 archive.' >&2
        exit 1
    }
fi

# Stream only the single verified executable from the archive.
[[ $(tar -tzf "$archive") == elan-init ]]
tar -xOzf "$archive" -- elan-init > "$work/elan-init"
chmod 0700 "$work/elan-init"
"$work/elan-init" -y --no-modify-path --default-toolchain none
