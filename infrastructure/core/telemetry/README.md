# Telemetry — Unified Pipeline Metrics

Collects per-stage performance metrics (timing, CPU, memory, I/O) and diagnostic events into a single report at end of pipeline.

## Quick Start

```python
from infrastructure.core.telemetry import TelemetryCollector, TelemetryConfig

config = TelemetryConfig(enabled=True)
collector = TelemetryCollector(config, "my_project", output_dir)
collector.capture_system_info()

collector.start_stage("Analysis", 1)
# ... run stage ...
collector.end_stage("Analysis", 1, success=True)

report = collector.finalize(total_duration=42.0)
```

## Configuration

Add to `pipeline.yaml`:

```yaml
telemetry:
  enabled: true
  track_resources: true       # CPU, memory, I/O via psutil
  track_diagnostics: true     # Aggregate DiagnosticReporter events
  output_formats: [json, text]
  slow_stage_multiplier: 2.0  # Warn when stage > N× average
  high_memory_mb: 1024        # RSS warning threshold
  high_cpu_percent: 90.0      # CPU warning threshold
```

## Output

After pipeline runs, find reports in `projects/{name}/output/reports/`:

- `telemetry.json` — structured JSON report
- `telemetry.txt` — human-readable summary

## See Also

- [AGENTS.md](AGENTS.md) — Machine-readable spec
- [SKILL.md](SKILL.md) — MCP skill descriptor
