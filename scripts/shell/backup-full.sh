#!/usr/bin/env bash
################################################################################
# Full Backup Script
#
# Creates one write-once-by-this-helper snapshot containing the fixed directories
# `.hermes`, `.cache`, and `output` when their corresponding sources exist.
# Remote snapshots live below `backups/full/` in the SSH account's home.
#
# Usage:
#   bash scripts/shell/backup-full.sh [--dry-run] [remote-host] [snapshot-name]
#   bash scripts/shell/backup-full.sh [--dry-run] --local-root DIR [snapshot-name]
#
# `--local-root` is a real local-filesystem transport for disposable end-to-end
# verification. It does not change the default SSH/rsync behavior.
################################################################################

set -euo pipefail

readonly REMOTE_BASE="backups/full"
readonly METADATA_NAME=".template-full-backup"
readonly METADATA_FORMAT="template-full-backup-v1"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd -P)"

usage() {
    cat <<'EOF'
Usage:
  backup-full.sh [--dry-run] [remote-host] [snapshot-name]
  backup-full.sh [--dry-run] --local-root DIR [snapshot-name]

Arguments:
  remote-host       SSH config alias or user@hostname (default: backup)
  snapshot-name     Safe snapshot identifier (default: YYYY-MM-DD)

Options:
  --local-root DIR  Store snapshots below an absolute local directory.
  --dry-run         Print the resolved source-to-destination plan only.
  -h, --help        Show this help.
EOF
}

fail() {
    local status="$1"
    shift
    printf 'ERROR: %s\n' "$*" >&2
    exit "${status}"
}

validate_snapshot() {
    local value="$1"
    if (( ${#value} > 128 )) || [[ ! "${value}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
        fail 2 "Invalid snapshot name '${value}'. Use 1-128 ASCII letters, digits, dots, underscores, or hyphens; the first character must be alphanumeric."
    fi
}

validate_remote() {
    local value="$1"
    if [[ ! "${value}" =~ ^([A-Za-z0-9][A-Za-z0-9._-]*@)?[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
        fail 2 "Invalid remote host '${value}'. Use an SSH alias, hostname, or user@hostname without options, whitespace, slashes, or colons."
    fi
}

validate_local_root() {
    local value="$1"
    if [[ "${value}" != /* ]] || [[ "${value}" == "/" ]] || [[ "${value}" == *$'\n'* ]] || [[ "${value}" == *$'\r'* ]]; then
        fail 2 "--local-root must be an absolute directory other than / and must not contain line breaks."
    fi
    if [[ -e "${value}" && ! -d "${value}" ]]; then
        fail 2 "--local-root is not a directory: ${value}"
    fi
}

require_command() {
    local command_name="$1"
    command -v "${command_name}" >/dev/null 2>&1 || fail 127 "Required command is unavailable: ${command_name}"
}

path_is_within() {
    local candidate="${1%/}/"
    local parent="${2%/}/"
    [[ "${candidate}" == "${parent}"* ]]
}

run_logged() {
    local description="$1"
    shift
    local -a statuses=()
    local command_status=0
    local tee_status=0

    set +e
    "$@" 2>&1 | tee -a "${LOG}"
    statuses=("${PIPESTATUS[@]}")
    set -e

    command_status="${statuses[0]}"
    tee_status="${statuses[1]}"
    if (( command_status != 0 )); then
        printf 'ERROR: %s failed with exit code %s. Partial snapshot retained at %s; lock retained at %s\n' \
            "${description}" "${command_status}" "${PARTIAL_DISPLAY}" "${LOCK_DISPLAY}" | tee -a "${LOG}" >&2
        return "${command_status}"
    fi
    if (( tee_status != 0 )); then
        printf 'ERROR: Could not write backup log %s while %s ran. Partial snapshot retained at %s\n' \
            "${LOG}" "${description}" "${PARTIAL_DISPLAY}" >&2
        return "${tee_status}"
    fi
    return 0
}

LOCAL_ROOT=""
DRY_RUN=0
POSITIONAL=()

while (( $# > 0 )); do
    case "$1" in
        --local-root)
            (( $# >= 2 )) || fail 2 "--local-root requires a directory argument."
            [[ -z "${LOCAL_ROOT}" ]] || fail 2 "--local-root may be specified only once."
            LOCAL_ROOT="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --*)
            fail 2 "Unknown option: $1"
            ;;
        *)
            POSITIONAL+=("$1")
            shift
            ;;
    esac
done

if [[ -n "${LOCAL_ROOT}" ]]; then
    (( ${#POSITIONAL[@]} <= 1 )) || fail 2 "Local mode accepts only an optional snapshot name."
    SNAPSHOT="${POSITIONAL[0]:-$(date +%Y-%m-%d)}"
    REMOTE=""
    validate_local_root "${LOCAL_ROOT}"
else
    (( ${#POSITIONAL[@]} <= 2 )) || fail 2 "Expected at most a remote host and snapshot name."
    REMOTE="${POSITIONAL[0]:-backup}"
    SNAPSHOT="${POSITIONAL[1]:-$(date +%Y-%m-%d)}"
    validate_remote "${REMOTE}"
fi
validate_snapshot "${SNAPSHOT}"

[[ -n "${HOME:-}" ]] || fail 2 "HOME must be set so the .hermes source can be resolved."
if [[ "${HOME}" != /* ]] || [[ "${HOME}" == "/" ]] || [[ "${HOME}" == *:* ]] || [[ "${HOME}" == *$'\n'* ]] || [[ "${HOME}" == *$'\r'* ]]; then
    fail 2 "HOME must be an absolute directory other than / and must not contain colons or line breaks."
fi
[[ -d "${HOME}" ]] || fail 2 "HOME does not exist or is not a directory: ${HOME}"
HOME="$(cd -- "${HOME}" && pwd -P)"

SOURCE_PATHS=("${HOME}/.hermes" "${REPO_ROOT}/.cache" "${REPO_ROOT}/output")
SOURCE_LABELS=(".hermes" ".cache" "output")
PRESENT_INDEXES=()
MISSING_INDEXES=()

for index in "${!SOURCE_PATHS[@]}"; do
    if [[ -d "${SOURCE_PATHS[${index}]}" ]]; then
        PRESENT_INDEXES+=("${index}")
    else
        MISSING_INDEXES+=("${index}")
    fi
done

(( ${#PRESENT_INDEXES[@]} > 0 )) || fail 1 "No backup sources exist. Expected at least one of: ${SOURCE_PATHS[*]}"

if [[ -n "${LOCAL_ROOT}" ]]; then
    FINAL_DIR="${LOCAL_ROOT%/}/${SNAPSHOT}"
    PARTIAL_DIR="${LOCAL_ROOT%/}/.${SNAPSHOT}.partial.$$"
    FINAL_DISPLAY="${FINAL_DIR}"
    PARTIAL_DISPLAY="${PARTIAL_DIR}"
    LOCK_DIR="${LOCAL_ROOT%/}/.${SNAPSHOT}.lock"
    LOCK_DISPLAY="${LOCK_DIR}"
else
    REMOTE_FINAL_DIR="${REMOTE_BASE}/${SNAPSHOT}"
    REMOTE_PARTIAL_DIR="${REMOTE_BASE}/.${SNAPSHOT}.partial.$$"
    FINAL_DISPLAY="${REMOTE}:${REMOTE_FINAL_DIR}"
    PARTIAL_DISPLAY="${REMOTE}:${REMOTE_PARTIAL_DIR}"
    REMOTE_LOCK_DIR="${REMOTE_BASE}/.${SNAPSHOT}.lock"
    LOCK_DISPLAY="${REMOTE}:${REMOTE_LOCK_DIR}"
fi

printf '=== Full Backup ===\n'
printf 'Snapshot : %s\n' "${SNAPSHOT}"
if [[ -n "${LOCAL_ROOT}" ]]; then
    printf 'Transport: local filesystem\n'
    printf 'Target   : %s\n' "${FINAL_DIR}"
else
    printf 'Transport: SSH/rsync via %s\n' "${REMOTE}"
    printf 'Remote filesystem path: %s\n' "${REMOTE_FINAL_DIR}"
    printf 'Rsync target          : %s\n' "${FINAL_DISPLAY}"
fi

for index in "${!SOURCE_PATHS[@]}"; do
    source_path="${SOURCE_PATHS[${index}]}"
    label="${SOURCE_LABELS[${index}]}"
    if [[ -d "${source_path}" ]]; then
        if [[ -n "${LOCAL_ROOT}" ]]; then
            destination="${FINAL_DIR}/${label}/"
        else
            destination="${REMOTE}:${REMOTE_FINAL_DIR}/${label}/"
        fi
        printf 'Source   : %s/ -> %s\n' "${source_path}" "${destination}"
    else
        printf 'Missing  : %s (will be skipped)\n' "${source_path}"
    fi
done

if (( DRY_RUN == 1 )); then
    printf 'Dry run only: no directories were created and no SSH or rsync command was run.\n'
    exit 0
fi

require_command rsync
if [[ -z "${LOCAL_ROOT}" ]]; then
    require_command ssh
fi

METADATA_FILE=""
LOCK_ACTIVE=0
cleanup_on_exit() {
    local original_status=$?
    trap - EXIT
    if [[ -n "${METADATA_FILE}" && -f "${METADATA_FILE}" ]]; then
        rm -f -- "${METADATA_FILE}" || true
    fi
    if (( LOCK_ACTIVE == 1 )); then
        printf 'ERROR: Snapshot lock retained for fail-closed inspection: %s\n' "${LOCK_DISPLAY}" >&2
        if (( original_status == 0 )); then
            original_status=1
        fi
    fi
    exit "${original_status}"
}
trap cleanup_on_exit EXIT

if [[ -n "${LOCAL_ROOT}" ]]; then
    mkdir -p -- "${LOCAL_ROOT}" || fail 1 "Could not create local backup root: ${LOCAL_ROOT}"
    LOCAL_ROOT="$(cd -- "${LOCAL_ROOT}" && pwd -P)" || fail 1 "Could not resolve local backup root: ${LOCAL_ROOT}"
    [[ "${LOCAL_ROOT}" != "/" ]] || fail 2 "Resolved --local-root must not be /."
    FINAL_DIR="${LOCAL_ROOT}/${SNAPSHOT}"
    PARTIAL_DIR="${LOCAL_ROOT}/.${SNAPSHOT}.partial.$$"
    FINAL_DISPLAY="${FINAL_DIR}"
    PARTIAL_DISPLAY="${PARTIAL_DIR}"
    LOCK_DIR="${LOCAL_ROOT}/.${SNAPSHOT}.lock"
    LOCK_DISPLAY="${LOCK_DIR}"

    for index in "${PRESENT_INDEXES[@]}"; do
        source_real="$(cd -- "${SOURCE_PATHS[${index}]}" && pwd -P)"
        if path_is_within "${FINAL_DIR}" "${source_real}"; then
            fail 2 "Local snapshot target ${FINAL_DIR} is inside backup source ${source_real}."
        fi
    done

    if ! (umask 077 && mkdir "${LOCK_DIR}"); then
        fail 1 "Snapshot is locked by another writer or stale lock: ${LOCK_DIR}"
    fi
    LOCK_ACTIVE=1
    if [[ -e "${FINAL_DIR}" || -L "${FINAL_DIR}" ]]; then
        rmdir "${LOCK_DIR}" || fail 1 "Snapshot exists and its lock could not be released: ${LOCK_DIR}"
        LOCK_ACTIVE=0
        fail 1 "Snapshot already exists; refusing to overwrite: ${FINAL_DIR}"
    fi
    [[ ! -e "${PARTIAL_DIR}" && ! -L "${PARTIAL_DIR}" ]] || fail 1 "Partial snapshot path already exists; refusing to reuse it: ${PARTIAL_DIR}"
    (umask 077 && mkdir -- "${PARTIAL_DIR}") || fail 1 "Could not create partial snapshot directory: ${PARTIAL_DIR}"
else
    remote_prepare="umask 077; mkdir -p '${REMOTE_BASE}'; mkdir '${REMOTE_LOCK_DIR}' || { printf '%s\\n' 'snapshot lock exists: ${REMOTE_LOCK_DIR}' >&2; exit 75; }; { test ! -e '${REMOTE_FINAL_DIR}' && test ! -L '${REMOTE_FINAL_DIR}'; } || { rmdir '${REMOTE_LOCK_DIR}' || true; printf '%s\\n' 'snapshot already exists: ${REMOTE_FINAL_DIR}' >&2; exit 73; }; { test ! -e '${REMOTE_PARTIAL_DIR}' && test ! -L '${REMOTE_PARTIAL_DIR}'; } || { rmdir '${REMOTE_LOCK_DIR}' || true; printf '%s\\n' 'partial snapshot already exists: ${REMOTE_PARTIAL_DIR}' >&2; exit 73; }; mkdir '${REMOTE_PARTIAL_DIR}' || { rmdir '${REMOTE_LOCK_DIR}' || true; exit 74; }"
    # Values are intentionally expanded locally after strict host/snapshot validation.
    # shellcheck disable=SC2029
    if ssh "${REMOTE}" "${remote_prepare}"; then
        LOCK_ACTIVE=1
    else
        status=$?
        fail "${status}" "Could not create the remote partial snapshot. Remote filesystem path: ${REMOTE_PARTIAL_DIR}"
    fi
fi

if ! LOG="$(mktemp "/tmp/backup-full-${SNAPSHOT}.XXXXXX")"; then
    fail 1 "Could not create a private backup log under /tmp. Partial snapshot retained at ${PARTIAL_DISPLAY}"
fi
chmod 600 "${LOG}" || fail 1 "Could not restrict backup log permissions: ${LOG}"

printf 'Log      : %s\n\n' "${LOG}" | tee -a "${LOG}"

for index in "${PRESENT_INDEXES[@]}"; do
    source_path="${SOURCE_PATHS[${index}]}"
    label="${SOURCE_LABELS[${index}]}"
    if [[ -n "${LOCAL_ROOT}" ]]; then
        destination="${PARTIAL_DIR}/${label}/"
    else
        destination="${REMOTE}:${REMOTE_PARTIAL_DIR}/${label}/"
    fi

    printf 'Backing up %s/ as %s/\n' "${source_path}" "${label}" | tee -a "${LOG}"
    if run_logged "rsync for ${label}" \
        rsync --archive --compress --progress -- \
        "${source_path}/" "${destination}"; then
        :
    else
        status=$?
        exit "${status}"
    fi
done

if ! METADATA_FILE="$(mktemp "/tmp/backup-full-metadata-${SNAPSHOT}.XXXXXX")"; then
    fail 1 "Could not create snapshot metadata. Partial snapshot retained at ${PARTIAL_DISPLAY}"
fi
chmod 600 "${METADATA_FILE}" || fail 1 "Could not restrict snapshot metadata permissions. Partial snapshot retained at ${PARTIAL_DISPLAY}"
REPOSITORY_REVISION="unavailable"
if command -v git >/dev/null 2>&1; then
    candidate_revision="$(git -C "${REPO_ROOT}" rev-parse --verify HEAD 2>/dev/null || true)"
    if [[ "${candidate_revision}" =~ ^[0-9a-f]{40,64}$ ]]; then
        REPOSITORY_REVISION="${candidate_revision}"
    fi
fi
{
    printf 'format=%s\n' "${METADATA_FORMAT}"
    printf 'snapshot=%s\n' "${SNAPSHOT}"
    printf 'repository_revision=%s\n' "${REPOSITORY_REVISION}"
    for index in "${PRESENT_INDEXES[@]}"; do
        printf 'directory=%s\n' "${SOURCE_LABELS[${index}]}"
    done
    if (( ${#MISSING_INDEXES[@]} > 0 )); then
        for index in "${MISSING_INDEXES[@]}"; do
            printf 'missing=%s\n' "${SOURCE_LABELS[${index}]}"
        done
    fi
} > "${METADATA_FILE}"

if [[ -n "${LOCAL_ROOT}" ]]; then
    metadata_destination="${PARTIAL_DIR}/${METADATA_NAME}"
else
    metadata_destination="${REMOTE}:${REMOTE_PARTIAL_DIR}/${METADATA_NAME}"
fi
if run_logged "snapshot metadata transfer" \
    rsync --archive -- "${METADATA_FILE}" "${metadata_destination}"; then
    :
else
    status=$?
    exit "${status}"
fi

if [[ -n "${LOCAL_ROOT}" ]]; then
    [[ ! -e "${FINAL_DIR}" && ! -L "${FINAL_DIR}" ]] || fail 1 "Snapshot appeared outside the cooperating-writer lock. Partial snapshot retained at ${PARTIAL_DIR}"
    mv -- "${PARTIAL_DIR}" "${FINAL_DIR}" || fail 1 "Could not finalize local snapshot. Partial snapshot retained at ${PARTIAL_DIR}"
    rmdir "${LOCK_DIR}" || fail 1 "Snapshot finalized, but its lock could not be released: ${LOCK_DIR}"
    LOCK_ACTIVE=0
else
    remote_finalize="{ test ! -e '${REMOTE_FINAL_DIR}' && test ! -L '${REMOTE_FINAL_DIR}'; } || { printf '%s\\n' 'snapshot appeared outside the cooperating-writer lock: ${REMOTE_FINAL_DIR}' >&2; exit 73; }; mv '${REMOTE_PARTIAL_DIR}' '${REMOTE_FINAL_DIR}'"
    # Values are intentionally expanded locally after strict host/snapshot validation.
    # shellcheck disable=SC2029
    if ssh "${REMOTE}" "${remote_finalize}"; then
        :
    else
        status=$?
        fail "${status}" "Could not finalize the remote snapshot. Partial snapshot retained at ${REMOTE_PARTIAL_DIR}"
    fi
    # shellcheck disable=SC2029
    if ssh "${REMOTE}" "rmdir '${REMOTE_LOCK_DIR}'"; then
        LOCK_ACTIVE=0
    else
        status=$?
        fail "${status}" "Remote snapshot finalized, but its lock could not be released: ${REMOTE_LOCK_DIR}"
    fi
fi

printf '\nFull backup completed: %s\n' "${FINAL_DISPLAY}" | tee -a "${LOG}"
if [[ -n "${LOCAL_ROOT}" ]]; then
    printf 'Test restore: bash scripts/shell/restore-test.sh --local-root %q %q\n' "${LOCAL_ROOT}" "${SNAPSHOT}"
else
    printf 'Test restore: bash scripts/shell/restore-test.sh %q %q\n' "${REMOTE}" "${SNAPSHOT}"
fi
