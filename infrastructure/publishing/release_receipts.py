"""Backwards-compat shim: the module moved to ``infrastructure.publishing.release.release_receipts``.

Historical import paths keep resolving; new code imports the new path
directly."""

from infrastructure.publishing.release.release_receipts import (
    AuthorityStatus,
    CleanCheckoutReceipt,
    CommandReceipt,
    CoverageGapSnapshot,
    RELEASE_RECEIPT_SCHEMA,
    ReleaseMetadataReceipt,
    ReleaseReceiptError,
    ReceiptStatus,
    SubprocessPolicyReceipt,
    VerificationMode,
    build_coverage_gap_snapshot,
    build_release_metadata_receipt,
    build_subprocess_policy_receipt,
    receipt_digest,
    write_receipt,
)

__all__ = [
    "AuthorityStatus",
    "CleanCheckoutReceipt",
    "CommandReceipt",
    "CoverageGapSnapshot",
    "RELEASE_RECEIPT_SCHEMA",
    "ReleaseMetadataReceipt",
    "ReleaseReceiptError",
    "ReceiptStatus",
    "SubprocessPolicyReceipt",
    "VerificationMode",
    "build_coverage_gap_snapshot",
    "build_release_metadata_receipt",
    "build_subprocess_policy_receipt",
    "receipt_digest",
    "write_receipt",
]
