#!/usr/bin/env bash
# Prepare the exact Elan launcher and Lean compiler used by the hosted checks.
set -euo pipefail

if [[ $(uname -s) != Linux || $(uname -m) != x86_64 ]]; then
    printf '%s\n' 'The pinned CI Lean assets require Linux x86_64.' >&2
    exit 1
fi

pin=leanprover/lean4:v4.35.0
test "$(< projects/templates/template_active_inference/lean/lean-toolchain)" = "$pin"
test "$(< projects/templates/template_formal/formal/lean/lean-toolchain)" = "$pin"
elan_home="$HOME/.elan"
toolchains="$elan_home/toolchains"
[[ ! -L $elan_home && ! -L $toolchains ]]

work=$(mktemp -d "$RUNNER_TEMP/ci-lean.XXXXXX")
stage=
cleanup() {
    rm -rf -- "$work"
    if [[ -n $stage ]]; then rm -rf -- "$stage"; fi
}
trap cleanup EXIT

download() {
    local archive=$1 size=$2 digest=$3 max_time=$4
    shift 4
    curl --disable --fail --silent --show-error --location --max-redirs 5 \
        --proto '=https' --proto-redir '=https' --retry 2 --retry-max-time "$((2 * max_time))" \
        --connect-timeout 15 --max-time "$max_time" --max-filesize "$size" \
        --output "$archive" "$@" &&
        [[ $(wc -c < "$archive") -eq $size ]] &&
        printf '%s  %s\n' "$digest" "$archive" | sha256sum --check --status
}

fetch_archive() {
    local archive=$1 size=$2 digest=$3 max_time=$4 api=$5 tag=$6
    if ! download "$archive" "$size" "$digest" "$max_time" --header 'Accept: application/octet-stream' "$api"; then
        download "$archive" "$size" "$digest" "$max_time" "$tag" || {
            printf 'Could not retrieve verified CI archive %s.\n' "$archive" >&2
            return 1
        }
    fi
}

elan_archive="$work/elan.tar.gz"
fetch_archive "$elan_archive" 4996571 \
    42b94d4244e8353142c456ec0e4ca6528fd898a6c604d4059f494e706e431f63 40 \
    https://api.github.com/repos/leanprover/elan/releases/assets/529114798 \
    https://github.com/leanprover/elan/releases/download/v4.2.4/elan-x86_64-unknown-linux-gnu.tar.gz
[[ $(tar -tzf "$elan_archive") == elan-init ]]
tar -xOzf "$elan_archive" -- elan-init > "$work/elan-init"
chmod 0700 "$work/elan-init"
ELAN_HOME="$elan_home" "$work/elan-init" -y --no-modify-path --default-toolchain none

# Elan encodes the version-qualified remote name as this physical directory.
# The hosted execution account copies the complete toolchains tree.
compiler="$toolchains/leanprover--lean4---v4.35.0"
compiler_archive="$work/lean-4.35.0-linux.tar.zst"
compiler_digest=7289597a44543246c9227b8cae501767e095ce17f6d448b95fc4a8dc97268f6d
stamp=.template-lean-archive-sha256

verify_compiler() {
    local candidate=$1
    [[ -d $candidate && ! -L $candidate && -d $candidate/bin && ! -L $candidate/bin &&
        -f $candidate/bin/lean && ! -L $candidate/bin/lean && -x $candidate/bin/lean &&
        -f $candidate/bin/lake && ! -L $candidate/bin/lake && -x $candidate/bin/lake ]] &&
        printf '%s  %s\n' \
            bf8d54e4714cc4b03d3f6bb34c83b7202b87e49c8bfcbff6895c085bb90ceb38 "$candidate/bin/lean" \
            8ba83c98f76562d03b8dbc33f1057151ba6cbb121679dde76b2260ccc90495e1 "$candidate/bin/lake" | sha256sum --check --status
}

if [[ ! -e $compiler && ! -L $compiler ]]; then
    fetch_archive "$compiler_archive" 594481375 "$compiler_digest" 420 \
        'https://api.github.com/repos/leanprover/lean4/releases/assets/634574462?download=1' \
        https://github.com/leanprover/lean4/releases/download/v4.35.0/lean-4.35.0-linux.tar.zst
    mkdir -p -- "$toolchains"
    stage=$(mktemp -d "$toolchains/.template-lean.XXXXXX")
    tar --zstd --extract --file "$compiler_archive" --directory "$stage" --no-same-owner
    candidate="$stage/lean-4.35.0-linux"
    verify_compiler "$candidate"
    printf '%s\n' "$compiler_digest" > "$candidate/$stamp"
    mv --no-clobber --no-target-directory -- "$candidate" "$compiler"
fi

if ! verify_compiler "$compiler" || [[ ! -f $compiler/$stamp || -L $compiler/$stamp ]] ||
    [[ $(< "$compiler/$stamp") != "$compiler_digest" ]]; then
    printf '%s\n' 'Existing Lean compiler slot lacks the exact verified release bytes.' >&2
    exit 1
fi
version=$("$compiler/bin/lean" --version)
[[ $version == 'Lean (version 4.35.0,'* ]]
printf '%s\n' "$version"
