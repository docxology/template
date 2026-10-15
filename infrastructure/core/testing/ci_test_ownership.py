"""Explicit focused test owners for shared helpers without matching filenames.

These aliases select complete real test files, not exemptions or evidence that
their runtime fits the smoke deadline. Unlisted helpers retain broad fallback.
"""

SOURCE_TEST_OWNERS: dict[str, tuple[str, ...]] = {
    "infrastructure/core/pipeline/fingerprints.py": (
        "tests/infra_tests/core/pipeline/test_fingerprint_observations.py",
    ),
    "infrastructure/publishing/_standalone_git.py": ("tests/infra_tests/publishing/test_standalone_git_reads.py",),
    "infrastructure/publishing/_standalone_provider_admission.py": (
        "tests/infra_tests/publishing/test_standalone_install_projection.py",
    ),
    "infrastructure/reporting/native_mermaid_runtime_selection.py": (
        "tests/infra_tests/reporting/test_native_mermaid_runtime_profile.py",
    ),
    "infrastructure/reporting/native_mermaid_source_reference.py": (
        "tests/infra_tests/reporting/test_native_mermaid_runtime_profile.py",
    ),
    "infrastructure/rendering/_mermaid_v11.py": ("tests/infra_tests/reporting/test_native_mermaid_runtime_profile.py",),
    "infrastructure/rendering/_mermaid_v11_adapter.mjs": (
        "tests/infra_tests/reporting/test_native_mermaid_runtime_profile.py",
    ),
    "infrastructure/rendering/_mermaid_v11_batch_adapter.mjs": (
        "tests/infra_tests/reporting/test_native_mermaid_runtime_profile.py",
    ),
    "infrastructure/reporting/native_format_acceptance_contracts.py": (
        "tests/infra_tests/reporting/test_native_original_launch_correctness.py",
        "tests/infra_tests/reporting/test_native_format_acceptance.py",
    ),
    "infrastructure/reporting/native_original_supervisor.py": (
        "tests/infra_tests/reporting/test_native_original_launch_correctness.py",
    ),
    "infrastructure/core/pipeline/stages.py": (
        "tests/infra_tests/reporting/test_native_original_launch_correctness.py",
        "tests/infra_tests/core/pipeline/test_stage_attempt_admission.py",
    ),
    "infrastructure/project/public_acceptance_auxiliary_pipeline_failure.py": (
        "tests/infra_tests/project/test_public_acceptance_auxiliary.py",
        "tests/infra_tests/project/test_auxiliary_audited_bootstrap.py",
    ),
    "infrastructure/project/public_acceptance_auxiliary_pipeline_environment.py": (
        "tests/infra_tests/project/test_public_acceptance_auxiliary.py",
        "tests/infra_tests/project/test_auxiliary_audited_bootstrap.py",
    ),
    "infrastructure/project/public_acceptance_auxiliary_supervision.py": (
        "tests/infra_tests/project/test_public_acceptance_auxiliary.py",
        "tests/infra_tests/project/test_auxiliary_audited_bootstrap.py",
    ),
    "infrastructure/project/public_acceptance_auxiliary_transfer_validation.py": (
        "tests/infra_tests/project/test_public_acceptance_auxiliary.py",
        "tests/infra_tests/project/test_auxiliary_audited_bootstrap.py",
    ),
    "infrastructure/project/installed_domain_acceptance.py": (
        "tests/infra_tests/project/test_installed_acceptance.py",
        "tests/infra_tests/project/test_installed_domain_acceptance.py",
    ),
    "infrastructure/project/public_acceptance_auxiliary_cli.py": (
        "tests/infra_tests/project/test_public_acceptance_auxiliary_cli.py",
    ),
    "infrastructure/reporting/native_current_reader_inputs.py": (
        "tests/infra_tests/reporting/test_native_whole_portability.py",
        "tests/infra_tests/reporting/test_native_revalidation_data.py",
    ),
    "infrastructure/reporting/native_revalidation_progress.py": (
        "tests/infra_tests/reporting/test_native_whole_portability.py",
        "tests/infra_tests/reporting/test_native_revalidation_data.py",
    ),
    "infrastructure/reporting/native_installed_launcher.py": (
        "tests/infra_tests/reporting/test_native_installed_launch_contract.py",
        "tests/infra_tests/reporting/test_native_whole_portability.py",
    ),
    "infrastructure/reporting/native_installed_invocation.py": (
        "tests/infra_tests/reporting/test_native_installed_launch_contract.py",
        "tests/infra_tests/reporting/test_native_whole_portability.py",
    ),
    "infrastructure/reporting/native_installed_custody_capture.py": (
        "tests/infra_tests/reporting/test_native_installed_custody_capture.py",
    ),
    "infrastructure/project/public_acceptance_evidence.py": (
        "tests/infra_tests/project/test_auxiliary_audited_bootstrap.py",
        "tests/infra_tests/project/test_public_acceptance_auxiliary.py",
    ),
    "infrastructure/project/installed_acceptance_validation.py": (
        "tests/infra_tests/project/test_installed_acceptance.py",
    ),
    "infrastructure/project/installed_acceptance_worker.py": (
        "tests/infra_tests/project/test_installed_acceptance.py",
        "tests/infra_tests/project/test_acceptance_build_policy.py",
    ),
    "infrastructure/project/public_acceptance_auxiliary_bootstrap.py": (
        "tests/infra_tests/project/test_auxiliary_audited_bootstrap.py",
        "tests/infra_tests/project/test_public_acceptance_auxiliary.py",
    ),
    "infrastructure/project/public_acceptance_auxiliary_pipeline.py": (
        "tests/infra_tests/project/test_auxiliary_audited_bootstrap.py",
        "tests/infra_tests/project/test_public_acceptance_auxiliary.py",
    ),
    "infrastructure/project/public_acceptance_auxiliary_validation.py": (
        "tests/infra_tests/project/test_public_acceptance_auxiliary.py",
    ),
    "infrastructure/project/public_acceptance_auxiliary_worker.py": (
        "tests/infra_tests/project/test_public_acceptance_auxiliary.py",
    ),
    "infrastructure/publishing/release_plan_transaction.py": ("tests/infra_tests/publishing/test_release_plan.py",),
    "infrastructure/reporting/native_current_nomination_batch.py": (
        "tests/infra_tests/reporting/test_native_revalidation_data.py",
    ),
    "infrastructure/reporting/native_format_joint_source.py": (
        "tests/infra_tests/reporting/test_native_revalidation_data.py",
        "tests/infra_tests/reporting/test_native_format_acceptance.py",
    ),
    "infrastructure/reporting/native_source_provider_bootstrap.py": (
        "tests/infra_tests/reporting/test_native_stage_child_contracts.py",
    ),
    "infrastructure/reporting/release_readiness_snapshot.py": (
        "tests/infra_tests/reporting/test_readiness_snapshot.py",
    ),
    "infrastructure/reporting/release_readiness_validators.py": (
        "tests/infra_tests/reporting/test_native_format_acceptance.py",
        "tests/infra_tests/reporting/test_required_readiness.py",
    ),
    "infrastructure/reporting/native_pdfium_provider_data.py": (
        "tests/infra_tests/reporting/test_native_revalidation_data.py",
    ),
    "infrastructure/reporting/native_pdfium_revalidation.py": (
        "tests/infra_tests/reporting/test_native_revalidation_data.py",
    ),
    "infrastructure/reporting/native_pdfium_runtime_data.py": (
        "tests/infra_tests/reporting/test_native_revalidation_data.py",
    ),
    "infrastructure/reporting/native_office_diagram_runtime.py": (
        "tests/infra_tests/reporting/test_native_pdfium_batch_data.py",
    ),
}

__all__ = ["SOURCE_TEST_OWNERS"]
