"""Explicit focused test owners for shared helpers without matching filenames.

These aliases select complete real test files, not exemptions or evidence that
their runtime fits the smoke deadline. Unlisted helpers retain broad fallback.
"""

SOURCE_TEST_OWNERS: dict[str, tuple[str, ...]] = {
    "scripts/shell/setup-system-deps.sh": ("tests/infra_tests/test_system_deps_prepared_python.py",),
    "infrastructure/core/testing/_pytest_runtime_controls.py": (
        "tests/infra_tests/core/test_pytest_runtime_controls.py",
        "tests/infra_tests/reporting/test_pipeline_test_runner_integration.py",
        "tests/infra_tests/core/test_project_test_measurement.py",
    ),
    "infrastructure/reporting/pipeline_test_runner.py": (
        "tests/infra_tests/reporting/test_pipeline_test_runner.py",
        "tests/infra_tests/reporting/test_pipeline_test_runner_integration.py",
        "tests/infra_tests/reporting/test_project_verifier.py",
        "tests/infra_tests/core/test_project_test_measurement.py",
    ),
    "infrastructure/project/public_root_lane_worker.py": ("tests/infra_tests/project/test_root_case_lanes.py",),
    "infrastructure/project/public_root_lane_readback.py": ("tests/infra_tests/project/test_root_case_lanes.py",),
    "infrastructure/core/testing/pytest_receipt.py": (
        "tests/infra_tests/core/test_pytest_receipt.py",
        "tests/infra_tests/core/test_ci_infra.py",
    ),
    "infrastructure/core/testing/pytest_observations.py": (
        "tests/infra_tests/core/test_pytest_observations.py",
        "tests/infra_tests/core/test_pytest_receipt.py",
        "tests/infra_tests/core/test_ci_infra.py",
    ),
    "infrastructure/core/testing/ci_infra.py": (
        "tests/infra_tests/core/test_ci_infra.py",
        "tests/infra_tests/core/test_ci_infra_partition.py",
        "tests/infra_tests/core/test_pytest_receipt.py",
    ),
    "infrastructure/core/pipeline/artifact_contracts.py": (
        "tests/infra_tests/core/pipeline/test_artifact_contracts.py",
        "tests/infra_tests/core/pipeline/test_stage_attempt_admission.py",
    ),
    "infrastructure/core/pipeline/stage_admission.py": (
        "tests/infra_tests/core/pipeline/test_artifact_contracts.py",
        "tests/infra_tests/core/pipeline/test_stage_attempt_admission.py",
    ),
    "infrastructure/core/testing/test_runner_outputs.py": (
        "tests/infra_tests/core/test_test_runner_receipts.py",
        "tests/infra_tests/reporting/test_result_loaders.py",
        "tests/infra_tests/reporting/test_project_verifier.py",
        "tests/infra_tests/reporting/test_pipeline_test_runner_integration.py",
    ),
    "infrastructure/core/_bounded_kill.py": (
        "tests/infra_tests/project/test_public_acceptance_auxiliary_supervision.py",
        "tests/infra_tests/core/test_execution_boundary.py",
        "tests/infra_tests/core/test_execution_custody_boundary.py",
        "tests/infra_tests/core/test_bounded_run_guardian.py",
        "tests/infra_tests/core/test_guardian_startup_budget.py",
        "tests/infra_tests/core/test_pipeline_control_extensions.py",
        "tests/infra_tests/core/pipeline/test_multi_project_guardian_custody.py",
        "tests/infra_tests/core/pipeline/test_stage_source_launch.py",
        "tests/infra_tests/reporting/test_native_original_launch_correctness.py",
    ),
    "infrastructure/core/pipeline/fingerprint_files.py": (
        "tests/infra_tests/core/pipeline/test_fingerprint_observations.py",
    ),
    "infrastructure/core/pipeline/fingerprints.py": (
        "tests/infra_tests/core/pipeline/test_fingerprint_observations.py",
        "tests/infra_tests/core/pipeline/test_distribution_identity.py",
    ),
    "infrastructure/core/pipeline/_stage_protocol.py": (
        "tests/infra_tests/core/pipeline/test_stage_source_launch.py",
        "tests/infra_tests/core/pipeline/test_stage_attempt_admission.py",
        "tests/infra_tests/core/test_analysis_launch.py",
        "tests/infra_tests/core/test_project_test_measurement.py",
    ),
    "infrastructure/core/pipeline/stage_launch.py": (
        "tests/infra_tests/core/pipeline/test_stage_source_launch.py",
        "tests/infra_tests/core/pipeline/test_stage_attempt_admission.py",
        "tests/infra_tests/core/test_analysis_launch.py",
        "tests/infra_tests/core/test_project_test_measurement.py",
    ),
    "infrastructure/core/pipeline/stage_worker.py": (
        "tests/infra_tests/core/pipeline/test_stage_source_launch.py",
        "tests/infra_tests/core/pipeline/test_stage_attempt_admission.py",
        "tests/infra_tests/core/test_analysis_launch.py",
        "tests/infra_tests/core/test_project_test_measurement.py",
    ),
    "infrastructure/core/pipeline/execution_environment.py": (
        "tests/infra_tests/core/test_execution_policy.py",
        "tests/infra_tests/core/pipeline/test_cache_identity.py",
    ),
    "infrastructure/core/testing/_ci_execution_files.py": ("tests/infra_tests/core/test_ci_execution_user.py",),
    "infrastructure/publishing/_standalone_git.py": ("tests/infra_tests/publishing/test_standalone_git_reads.py",),
    "infrastructure/publishing/_standalone_provider_admission.py": (
        "tests/infra_tests/publishing/test_standalone_install_projection.py",
        "tests/infra_tests/publishing/test_standalone_git_reads.py",
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
    "infrastructure/rendering/latex_texttt.py": (
        "tests/infra_tests/rendering/test_latex_texttt.py",
        "tests/infra_tests/rendering/test_latex_texttt_native.py",
    ),
    "infrastructure/rendering/latex_utils.py": (
        "tests/infra_tests/rendering/test_latex_utils.py",
        "tests/infra_tests/rendering/test_latex_texttt_native.py",
    ),
    "infrastructure/rendering/_slides_math_header.py": (
        "tests/infra_tests/rendering/test_slides_math_header.py",
        "tests/infra_tests/rendering/test_latex_texttt_native.py",
    ),
    "infrastructure/project/public_acceptance_auxiliary_pipeline_failure.py": (
        "tests/infra_tests/project/test_public_acceptance_auxiliary.py",
        "tests/infra_tests/project/test_auxiliary_audited_bootstrap.py",
    ),
    "infrastructure/project/public_acceptance_auxiliary_pipeline_environment.py": (
        "tests/infra_tests/project/test_public_acceptance_auxiliary.py",
        "tests/infra_tests/project/test_auxiliary_audited_bootstrap.py",
        "tests/infra_tests/project/test_public_acceptance_auxiliary_cli.py",
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
        "tests/infra_tests/project/test_installed_companion_custody.py",
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
    "infrastructure/reporting/native_tool_producer.py": (
        "tests/infra_tests/reporting/test_native_stage_child_contracts.py",
        "tests/infra_tests/rendering/test_native_render_custody.py",
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
