---
name: telemetry
description: Unified pipeline telemetry — collects per-stage performance metrics (CPU, memory, I/O) and diagnostic events into structured reports (JSON, text).
version: "1.0"
author: infrastructure
tags:
  - telemetry
  - monitoring
  - pipeline
  - diagnostics
  - performance
capabilities:
  - Collect per-stage timing, CPU, memory, and I/O metrics
  - Aggregate DiagnosticReporter events per pipeline stage
  - Detect performance anomalies (slow stages, high memory, high CPU)
  - Persist structured telemetry reports (JSON + text)
  - Configure via YAML telemetry block in pipeline.yaml
dependencies:
  required:
    - infrastructure.core.logging.diagnostic
    - infrastructure.core.logging.utils
  optional:
    - psutil  # For resource tracking
entry_points:
  - infrastructure.core.telemetry.TelemetryCollector
  - infrastructure.core.telemetry.TelemetryConfig
configuration:
  file: pipeline.yaml
  key: telemetry
  schema:
    enabled: bool
    track_resources: bool
    track_diagnostics: bool
    output_formats: list[str]
    persist_report: bool
    slow_stage_multiplier: float
    high_memory_mb: float
    high_cpu_percent: float
---

# Telemetry SKILL

This module provides unified pipeline telemetry for the infrastructure layer. It bridges `StagePerformanceTracker` resource metrics with `DiagnosticReporter` validation events into a single `TelemetryCollector`.

## When to Use

- When you need to instrument pipeline stage execution with resource tracking
- When you want a structured end-of-run report combining performance + diagnostics
- When configuring telemetry thresholds for CI warning detection

## API Surface

| Symbol | Type | Purpose |
| --- | --- | --- |
| `TelemetryConfig` | dataclass | Configuration with YAML-loadable `from_dict()` |
| `TelemetryCollector` | class | Main lifecycle: `start_stage()` → `end_stage()` → `finalize()` |
| `StageTelemetry` | dataclass | Per-stage record |
| `PipelineTelemetry` | dataclass | Full report with warnings |
| `PerformanceWarning` | dataclass | Individual anomaly record |
