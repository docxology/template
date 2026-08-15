#!/usr/bin/env bash
################################################################################
# Restore Test Script
#
# Restores a completed full-backup snapshot into a newly created scratch
# directory, verifies the versioned layout, then runs a checksum-based rsync
# comparison against the snapshot. It never deletes or overwrites a prior
# restore directory.
#
# Usage:
#   bash scripts/shell/restore-test.sh [--list] [remote-host] [snapshot-name]
#   bash scripts/shell/restore-test.sh [--list] --local-root DIR [snapshot-name]
################################################################################

set -euo pipefail

readonly REMOTE_BASE="backups/full"
readonly METADATA_NAME=".template-full-backup"
readonly METADATA_FORMAT="template-full-backup-v1"

usage() {
    cat <<'EOF'
Usage:
  restore-test.sh [--list] [--scratch-parent DIR] [remote-host] [snapshot-name]
  restore-test.sh [--list] [--scratch-parent DIR] --local-root DIR [snapshot-name]

Arguments:
  remote-host          SSH config alias or user@hostname (default: backup)
  snapshot-name        Safe snapshot identifier (default: YYYY-MM-DD)

Options:
  --local-root DIR     Read snapshots below an absolute local directory.
  --scratch-parent DIR Create the unique restore directory below DIR.
  --list               List the snapshot without creating a restore directory.
  -h, --help           Show this help.
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

validate_absolute_directory() {
    local option_name="$1"
    local value="$2"
    if [[ "${value}" != /* ]] || [[ "${value}" == *$'\n'* ]] || [[ "${value}" == *$'\r'* ]]; then
        fail 2 "${option_name} must be an absolute directory without line breaks."
    fi
    if [[ ! -d "${value}" ]]; then
        fail 2 "${option_name} does not exist or is not a directory: ${value}"
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

count_files() {
    local directory="$1"
    local count=0
    local _file_path=""
    while IFS= read -r -d '' _file_path; do
        ((count += 1))
    done < <(find "${directory}" -type f -print0)
    printf '%s' "${count}"
}

LOCAL_ROOT=""
SCRATCH_PARENT="${TMPDIR:-/tmp}"
LIST_ONLY=0
POSITIONAL=()

while (( $# > 0 )); do
    case "$1" in
        --local-root)
            (( $# >= 2 )) || fail 2 "--local-root requires a directory argument."
            [[ -z "${LOCAL_ROOT}" ]] || fail 2 "--local-root may be specified only once."
            LOCAL_ROOT="$2"
            shift 2
            ;;
        --scratch-parent)
            (( $# >= 2 )) || fail 2 "--scratch-parent requires a directory argument."
            SCRATCH_PARENT="$2"
            shift 2
            ;;
        --list)
            LIST_ONLY=1
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
    validate_absolute_directory "--local-root" "${LOCAL_ROOT}"
    LOCAL_ROOT="$(cd -- "${LOCAL_ROOT}" && pwd -P)"
    [[ "${LOCAL_ROOT}" != "/" ]] || fail 2 "Resolved --local-root must not be /."
    SNAPSHOT_SOURCE="${LOCAL_ROOT}/${SNAPSHOT}"
    REMOTE_SNAPSHOT_DIR=""
else
    (( ${#POSITIONAL[@]} <= 2 )) || fail 2 "Expected at most a remote host and snapshot name."
    REMOTE="${POSITIONAL[0]:-backup}"
    SNAPSHOT="${POSITIONAL[1]:-$(date +%Y-%m-%d)}"
    validate_remote "${REMOTE}"
    REMOTE_SNAPSHOT_DIR="${REMOTE_BASE}/${SNAPSHOT}"
    SNAPSHOT_SOURCE="${REMOTE}:${REMOTE_SNAPSHOT_DIR}"
fi
validate_snapshot "${SNAPSHOT}"

require_command rsync
if [[ -z "${LOCAL_ROOT}" ]]; then
    require_command ssh
fi

printf '=== Restore Test ===\n'
printf 'Snapshot : %s\n' "${SNAPSHOT}"
if [[ -n "${LOCAL_ROOT}" ]]; then
    printf 'Transport: local filesystem\n'
    printf 'Source   : %s\n' "${SNAPSHOT_SOURCE}"
    [[ -d "${SNAPSHOT_SOURCE}" ]] || fail 1 "Backup snapshot not found: ${SNAPSHOT_SOURCE}"
    SNAPSHOT_SOURCE="$(cd -- "${SNAPSHOT_SOURCE}" && pwd -P)"
else
    printf 'Transport: SSH/rsync via %s\n' "${REMOTE}"
    printf 'Remote filesystem path: %s\n' "${REMOTE_SNAPSHOT_DIR}"
    printf 'Rsync source          : %s\n' "${SNAPSHOT_SOURCE}"
    # The path is intentionally expanded locally after strict snapshot validation.
    # shellcheck disable=SC2029
    if ssh "${REMOTE}" "test -d '${REMOTE_SNAPSHOT_DIR}'"; then
        :
    else
        status=$?
        fail "${status}" "Backup snapshot not found or inaccessible. Remote filesystem path: ${REMOTE_SNAPSHOT_DIR}"
    fi
fi

if (( LIST_ONLY == 1 )); then
    printf '\nSnapshot listing (read-only):\n'
    if rsync --list-only -- "${SNAPSHOT_SOURCE}/"; then
        :
    else
        status=$?
        fail "${status}" "Could not list snapshot: ${SNAPSHOT_SOURCE}"
    fi
    exit 0
fi

validate_absolute_directory "--scratch-parent" "${SCRATCH_PARENT}"
SCRATCH_PARENT="$(cd -- "${SCRATCH_PARENT}" && pwd -P)"
if [[ -n "${LOCAL_ROOT}" ]] && path_is_within "${SCRATCH_PARENT}" "${LOCAL_ROOT}"; then
    fail 2 "--scratch-parent must be outside the local backup root: ${LOCAL_ROOT}"
fi

if [[ -n "${LOCAL_ROOT}" ]]; then
    metadata_path="${SNAPSHOT_SOURCE}/${METADATA_NAME}"
    [[ -f "${metadata_path}" ]] || fail 1 "Snapshot metadata is missing: ${metadata_path}"
    metadata_content="$(< "${metadata_path}")" || fail 1 "Snapshot metadata is unreadable: ${metadata_path}"
else
    # The path is intentionally expanded locally after strict snapshot validation.
    # shellcheck disable=SC2029
    if metadata_content="$(ssh "${REMOTE}" "cat '${REMOTE_SNAPSHOT_DIR}/${METADATA_NAME}'")"; then
        :
    else
        status=$?
        fail "${status}" "Snapshot metadata is missing or unreadable. Remote filesystem path: ${REMOTE_SNAPSHOT_DIR}/${METADATA_NAME}"
    fi
fi

format_seen=0
snapshot_seen=0
revision_seen=0
REPOSITORY_REVISION=""
EXPECTED_DIRECTORIES=()
MISSING_DIRECTORIES=()
while IFS= read -r metadata_line || [[ -n "${metadata_line}" ]]; do
    case "${metadata_line}" in
        "format=${METADATA_FORMAT}")
            ((format_seen += 1))
            ;;
        "snapshot=${SNAPSHOT}")
            ((snapshot_seen += 1))
            ;;
        repository_revision=*)
            ((revision_seen += 1))
            REPOSITORY_REVISION="${metadata_line#repository_revision=}"
            if [[ "${REPOSITORY_REVISION}" != "unavailable" && ! "${REPOSITORY_REVISION}" =~ ^[0-9a-f]{40,64}$ ]]; then
                fail 1 "Snapshot metadata contains an invalid repository revision."
            fi
            ;;
        directory=.hermes|directory=.cache|directory=output)
            directory_name="${metadata_line#directory=}"
            if (( ${#EXPECTED_DIRECTORIES[@]} > 0 )); then
                for existing_name in "${EXPECTED_DIRECTORIES[@]}"; do
                    [[ "${existing_name}" != "${directory_name}" ]] || fail 1 "Snapshot metadata repeats directory: ${directory_name}"
                done
            fi
            EXPECTED_DIRECTORIES+=("${directory_name}")
            ;;
        missing=.hermes|missing=.cache|missing=output)
            directory_name="${metadata_line#missing=}"
            if (( ${#MISSING_DIRECTORIES[@]} > 0 )); then
                for existing_name in "${MISSING_DIRECTORIES[@]}"; do
                    [[ "${existing_name}" != "${directory_name}" ]] || fail 1 "Snapshot metadata repeats missing directory: ${directory_name}"
                done
            fi
            MISSING_DIRECTORIES+=("${directory_name}")
            ;;
        *)
            fail 1 "Snapshot metadata contains an unsupported or mismatched record: ${metadata_line}"
            ;;
    esac
done <<< "${metadata_content}"

(( format_seen == 1 )) || fail 1 "Snapshot metadata must contain exactly one format=${METADATA_FORMAT} record."
(( snapshot_seen == 1 )) || fail 1 "Snapshot metadata must contain exactly one snapshot=${SNAPSHOT} record."
(( revision_seen == 1 )) || fail 1 "Snapshot metadata must contain exactly one repository_revision record."
(( ${#EXPECTED_DIRECTORIES[@]} > 0 )) || fail 1 "Snapshot metadata contains no backed-up directories."
for directory_name in .hermes .cache output; do
    contract_count=0
    for existing_name in "${EXPECTED_DIRECTORIES[@]}"; do
        [[ "${existing_name}" != "${directory_name}" ]] || ((contract_count += 1))
    done
    if (( ${#MISSING_DIRECTORIES[@]} > 0 )); then
        for existing_name in "${MISSING_DIRECTORIES[@]}"; do
            [[ "${existing_name}" != "${directory_name}" ]] || ((contract_count += 1))
        done
    fi
    (( contract_count == 1 )) || fail 1 "Snapshot metadata must classify ${directory_name} exactly once as directory or missing."
done

if ! CONTROL_DIR="$(mktemp -d "${SCRATCH_PARENT%/}/restore-test-${SNAPSHOT}.XXXXXX")"; then
    fail 1 "Could not create a unique restore control directory below ${SCRATCH_PARENT}."
fi
chmod 700 "${CONTROL_DIR}" || fail 1 "Could not restrict restore control directory permissions: ${CONTROL_DIR}"
TEST_DIR="${CONTROL_DIR}/restored"
(umask 077 && mkdir "${TEST_DIR}") || fail 1 "Could not create private restored tree: ${TEST_DIR}"
printf 'Control  : %s\n' "${CONTROL_DIR}"
printf 'Target   : %s\n\n' "${TEST_DIR}"

printf 'Restoring to the new scratch directory...\n'
if rsync --archive --compress -- "${SNAPSHOT_SOURCE}/" "${TEST_DIR}/"; then
    :
else
    status=$?
    fail "${status}" "Restore rsync failed. Partial scratch restore retained at ${TEST_DIR}"
fi

for directory_name in "${EXPECTED_DIRECTORIES[@]}"; do
    [[ -d "${TEST_DIR}/${directory_name}" ]] || fail 1 "Restored snapshot is missing declared directory ${directory_name}. Scratch restore retained at ${TEST_DIR}"
done

restored_metadata="$(< "${TEST_DIR}/${METADATA_NAME}")" || fail 1 "Restored metadata is unreadable: ${TEST_DIR}/${METADATA_NAME}"
[[ "${restored_metadata}" == "${metadata_content}" ]] || fail 1 "Snapshot metadata changed during restore. Scratch restore retained at ${CONTROL_DIR}"
shopt -s dotglob nullglob
for top_entry in "${TEST_DIR}"/*; do
    top_name="${top_entry##*/}"
    top_allowed=0
    [[ "${top_name}" != "${METADATA_NAME}" ]] || top_allowed=1
    for directory_name in "${EXPECTED_DIRECTORIES[@]}"; do
        [[ "${top_name}" != "${directory_name}" ]] || top_allowed=1
    done
    (( top_allowed == 1 )) || fail 1 "Restored snapshot contains undeclared top-level entry ${top_name}. Scratch restore retained at ${CONTROL_DIR}"
done
shopt -u dotglob nullglob

VERIFY_OUTPUT="${CONTROL_DIR}/rsync-verify.txt"
(umask 077 && : > "${VERIFY_OUTPUT}") || fail 1 "Could not create private verification output: ${VERIFY_OUTPUT}"
if rsync --recursive --links --perms --times --checksum --delete \
    --dry-run --itemize-changes --omit-dir-times -- \
    "${SNAPSHOT_SOURCE}/" "${TEST_DIR}/" > "${VERIFY_OUTPUT}" 2>&1; then
    :
else
    status=$?
    fail "${status}" "Checksum comparison failed to run. Diagnostic output: ${VERIFY_OUTPUT}; scratch restore retained at ${TEST_DIR}"
fi
if [[ -s "${VERIFY_OUTPUT}" ]]; then
    printf 'Checksum comparison reported differences:\n' >&2
    sed -n '1,80p' "${VERIFY_OUTPUT}" >&2
    fail 1 "Restored content differs from the snapshot. Full comparison: ${VERIFY_OUTPUT}; scratch restore retained at ${TEST_DIR}"
fi

RECEIPT="${CONTROL_DIR}/receipt.txt"
(
    umask 077
    {
        printf 'format=template-restore-test-v1\n'
        printf 'snapshot=%s\n' "${SNAPSHOT}"
        printf 'repository_revision=%s\n' "${REPOSITORY_REVISION}"
        printf 'command=restore-test.sh\n'
        printf 'exit_status=0\n'
        printf 'source=%s\n' "${SNAPSHOT_SOURCE}"
        printf 'target=%s\n' "${TEST_DIR}"
        printf 'verification=rsync-checksum-clean\n'
        for directory_name in "${EXPECTED_DIRECTORIES[@]}"; do
            file_count="$(count_files "${TEST_DIR}/${directory_name}")"
            printf 'directory=%s files=%s\n' "${directory_name}" "${file_count}"
        done
        if (( ${#MISSING_DIRECTORIES[@]} > 0 )); then
            for directory_name in "${MISSING_DIRECTORIES[@]}"; do
                printf 'missing=%s\n' "${directory_name}"
            done
        fi
        printf 'limitation=no-encryption-retention-or-credential-policy-verified\n'
        printf 'limitation=no-creation-time-digest-or-at-rest-integrity-verification\n'
        printf 'limitation=no-source-quiescence-or-coherent-snapshot-guarantee\n'
        printf 'limitation=rsync-archive-excludes-hardlinks-acls-and-xattrs\n'
    } > "${RECEIPT}"
) || fail 1 "Restore verified, but the receipt could not be written: ${RECEIPT}"

printf '\n=== Verification ===\n'
for directory_name in "${EXPECTED_DIRECTORIES[@]}"; do
    file_count="$(count_files "${TEST_DIR}/${directory_name}")"
    printf 'OK %s: %s files restored\n' "${directory_name}" "${file_count}"
done
printf 'OK checksum comparison: no differences\n'
printf 'Receipt  : %s\n' "${RECEIPT}"
printf 'Inspect  : %s\n' "${TEST_DIR}"
printf 'Cleanup is intentionally manual; this script never removes a prior restore.\n'
