# Checkpoint and Resume System

The pipeline includes a checkpoint system that allows resuming from the last successful stage after interruption.

## Overview

The checkpoint system automatically saves pipeline state after each successful stage, enabling resume capability for long-running pipelines.

## How It Works

### Automatic Checkpointing

Checkpoints are automatically saved after each successful stage:

1. **Stage Completion**: After a stage completes successfully (exit code 0)
2. **State Saving**: Pipeline state is saved to `project/output/.checkpoints/pipeline_checkpoint.json`
3. **State Includes**:
   - Pipeline start time
   - Last completed stage number
   - Stage results (name, exit code, duration, timestamp)
   - Total number of stages

### Checkpoint Structure

```json
{
  "pipeline_start_time": 1701234567.89,
  "last_stage_completed": 3,
  "total_stages": 6,
  "checkpoint_time": 1701234600.12,
  "stage_results": [
    {
      "name": "00_setup_environment",
      "exit_code": 0,
      "duration": 1.5,
      "timestamp": "2024-01-01 12:00:00",
      "completed": true
    },
    ...
  ]
}
```

## Using Resume

### Python Script (`execute_pipeline.py`)

```bash
# Resume from checkpoint
python3 scripts/execute_pipeline.py --resume

# Start fresh (clears checkpoint on success)
python3 scripts/execute_pipeline.py --core-only
```

### Shell Script (`run.sh`)

```bash
# Resume from checkpoint
./run.sh --pipeline --resume

# Start fresh
./run.sh --pipeline
```

## Checkpoint Validation

The system validates checkpoints before resuming:

- **File Existence**: Checkpoint file must exist
- **Format Validation**: JSON structure must be valid
- **Consistency Checks**: Stage counts and results must be consistent
- **Integrity Verification**: All completed stages must have exit code 0

### Validation Errors

If checkpoint validation fails, the pipeline will:
1. Log the validation error
2. Start a fresh pipeline instead
3. Provide instructions to clear the checkpoint if needed

```bash
# Clear corrupted checkpoint manually
rm -f project/output/.checkpoints/pipeline_checkpoint.json
```

## Checkpoint Lifecycle

### Creation

- Checkpoints are created after each successful stage
- Saved to: `project/output/.checkpoints/pipeline_checkpoint.json`
- Overwrites previous checkpoint (only latest state kept)

### Loading

- Checkpoint is loaded when `--resume` flag is used
- Validated before use
- Pipeline resumes from `last_stage_completed + 1`

### Cleanup

- Checkpoint is automatically cleared on successful pipeline completion
- Manual cleanup: `rm -f project/output/.checkpoints/pipeline_checkpoint.json`

## Resume Behavior

### What Gets Skipped

When resuming:
- **Clean Stage**: Skipped (output directories not cleaned)
- **Completed Stages**: Skipped (not re-executed)
- **Failed Stage**: Re-executed (pipeline resumes from failure point)

### What Gets Preserved

- **Pipeline Start Time**: Preserved from original run
- **Stage Durations**: Preserved for completed stages
- **Output Files**: Preserved from completed stages

### Example Resume Flow

```
Original Run:
  Stage 0: Clean ✓
  Stage 1: Setup ✓ (checkpoint saved)
  Stage 2: Tests ✓ (checkpoint saved)
  Stage 3: Analysis ✗ (pipeline interrupted)

Resume Run:
  Stage 0: Clean (skipped)
  Stage 1: Setup (skipped - already completed)
  Stage 2: Tests (skipped - already completed)
  Stage 3: Analysis (re-executed)
  Stage 4: PDF Rendering (executed)
  ...
```

## Checkpoint Manager API

### Python API

```python
from infrastructure.core.checkpoint import CheckpointManager, StageResult

# Initialize manager
manager = CheckpointManager()

# Save checkpoint
manager.save_checkpoint(
    pipeline_start_time=time.time(),
    last_stage_completed=3,
    stage_results=[...],
    total_stages=6
)

# Load checkpoint
checkpoint = manager.load_checkpoint()

# Validate checkpoint
is_valid, error_msg = manager.validate_checkpoint()

# Clear checkpoint
manager.clear_checkpoint()

# Check if exists
exists = manager.checkpoint_exists()
```

## Troubleshooting

### Checkpoint Not Found

**Symptom**: Resume fails with "checkpoint not found"

**Solutions**:
- Check if checkpoint file exists: `ls project/output/.checkpoints/`
- Verify checkpoint directory was created
- Start fresh pipeline if checkpoint intentionally cleared

### Corrupted Checkpoint

**Symptom**: Validation fails with "corrupted checkpoint"

**Solutions**:
```bash
# Clear corrupted checkpoint
rm -f project/output/.checkpoints/pipeline_checkpoint.json

# Restart pipeline
python3 scripts/execute_pipeline.py --core-only
```

### Checkpoint Out of Date

**Symptom**: Checkpoint references stages that no longer exist

**Solutions**:
- Clear old checkpoint
- Start fresh pipeline
- Checkpoint will be recreated with current stage structure

### Resume Starts from Wrong Stage

**Symptom**: Pipeline resumes from incorrect stage

**Solutions**:
- Check checkpoint contents: `cat project/output/.checkpoints/pipeline_checkpoint.json`
- Verify `last_stage_completed` value
- Clear checkpoint if incorrect

## Best Practices

### When to Use Resume

✅ **Use resume when**:
- Pipeline was interrupted (Ctrl+C, system crash)
- Long-running pipeline needs to continue after interruption
- Testing specific stages without re-running entire pipeline

❌ **Don't use resume when**:
- Code changes were made (may cause inconsistencies)
- Dependencies changed
- Starting fresh is preferred

### Checkpoint Maintenance

- **Automatic**: Checkpoints cleared on successful completion
- **Manual**: Clear checkpoints before major changes
- **Version Control**: Checkpoints are in `.gitignore` (not committed)

## Implementation Details

### Checkpoint Location

- **Default**: `project/output/.checkpoints/pipeline_checkpoint.json`
- **Custom**: Can specify custom directory in `CheckpointManager(checkpoint_dir=...)`

### Checkpoint Format

- **Format**: JSON
- **Encoding**: UTF-8
- **Indentation**: 2 spaces (human-readable)

### Error Handling

- **Save Failures**: Logged as warnings, pipeline continues
- **Load Failures**: Logged as warnings, pipeline starts fresh
- **Validation Failures**: Logged as errors, pipeline starts fresh

## See Also

- [`infrastructure/core/checkpoint.py`](../../infrastructure/core/checkpoint.py) - Implementation
- [`../../scripts/execute_pipeline.py`](../../scripts/execute_pipeline.py) - Resume integration
- [`troubleshooting-guide.md`](../operational/troubleshooting-guide.md) - Troubleshooting guide


