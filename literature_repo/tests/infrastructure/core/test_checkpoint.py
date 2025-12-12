"""Tests for infrastructure.core.checkpoint module.

Comprehensive tests for pipeline checkpoint system including save, load, resume,
and error handling scenarios.
"""

import json
import time
from pathlib import Path
import pytest
import tempfile
import shutil

from infrastructure.core.checkpoint import (
    CheckpointManager,
    PipelineCheckpoint,
    StageResult,
)


class TestStageResult:
    """Test StageResult dataclass."""

    def test_stage_result_creation(self):
        """Test creating a StageResult."""
        result = StageResult(
            name="test_stage",
            exit_code=0,
            duration=1.5,
            timestamp="2024-01-01 12:00:00",
            completed=True
        )
        
        assert result.name == "test_stage"
        assert result.exit_code == 0
        assert result.duration == 1.5
        assert result.timestamp == "2024-01-01 12:00:00"
        assert result.completed is True

    def test_stage_result_default_completed(self):
        """Test StageResult with default completed value."""
        result = StageResult(
            name="test",
            exit_code=0,
            duration=1.0,
            timestamp="2024-01-01 12:00:00"
        )
        
        assert result.completed is True  # Default value


class TestPipelineCheckpoint:
    """Test PipelineCheckpoint dataclass."""

    def test_checkpoint_creation(self):
        """Test creating a PipelineCheckpoint."""
        stage_results = [
            StageResult(
                name="stage_1",
                exit_code=0,
                duration=1.0,
                timestamp="2024-01-01 12:00:00"
            )
        ]
        
        checkpoint = PipelineCheckpoint(
            pipeline_start_time=1000.0,
            last_stage_completed=1,
            stage_results=stage_results,
            total_stages=5,
            checkpoint_time=1001.0
        )
        
        assert checkpoint.pipeline_start_time == 1000.0
        assert checkpoint.last_stage_completed == 1
        assert len(checkpoint.stage_results) == 1
        assert checkpoint.total_stages == 5
        assert checkpoint.checkpoint_time == 1001.0

    def test_checkpoint_to_dict(self):
        """Test converting checkpoint to dictionary."""
        stage_results = [
            StageResult(
                name="stage_1",
                exit_code=0,
                duration=1.0,
                timestamp="2024-01-01 12:00:00"
            )
        ]
        
        checkpoint = PipelineCheckpoint(
            pipeline_start_time=1000.0,
            last_stage_completed=1,
            stage_results=stage_results,
            total_stages=5,
            checkpoint_time=1001.0
        )
        
        data = checkpoint.to_dict()
        
        assert isinstance(data, dict)
        assert data['pipeline_start_time'] == 1000.0
        assert data['last_stage_completed'] == 1
        assert len(data['stage_results']) == 1
        assert data['total_stages'] == 5
        assert data['checkpoint_time'] == 1001.0

    def test_checkpoint_from_dict(self):
        """Test creating checkpoint from dictionary."""
        data = {
            'pipeline_start_time': 1000.0,
            'last_stage_completed': 1,
            'stage_results': [
                {
                    'name': 'stage_1',
                    'exit_code': 0,
                    'duration': 1.0,
                    'timestamp': '2024-01-01 12:00:00',
                    'completed': True
                }
            ],
            'total_stages': 5,
            'checkpoint_time': 1001.0
        }
        
        checkpoint = PipelineCheckpoint.from_dict(data)
        
        assert checkpoint.pipeline_start_time == 1000.0
        assert checkpoint.last_stage_completed == 1
        assert len(checkpoint.stage_results) == 1
        assert checkpoint.stage_results[0].name == 'stage_1'
        assert checkpoint.total_stages == 5
        assert checkpoint.checkpoint_time == 1001.0

    def test_checkpoint_round_trip(self):
        """Test checkpoint serialization round trip."""
        stage_results = [
            StageResult(
                name="stage_1",
                exit_code=0,
                duration=1.0,
                timestamp="2024-01-01 12:00:00"
            ),
            StageResult(
                name="stage_2",
                exit_code=0,
                duration=2.0,
                timestamp="2024-01-01 12:01:00"
            )
        ]
        
        original = PipelineCheckpoint(
            pipeline_start_time=1000.0,
            last_stage_completed=2,
            stage_results=stage_results,
            total_stages=5,
            checkpoint_time=1003.0
        )
        
        # Convert to dict and back
        data = original.to_dict()
        restored = PipelineCheckpoint.from_dict(data)
        
        assert restored.pipeline_start_time == original.pipeline_start_time
        assert restored.last_stage_completed == original.last_stage_completed
        assert len(restored.stage_results) == len(original.stage_results)
        assert restored.stage_results[0].name == original.stage_results[0].name
        assert restored.total_stages == original.total_stages
        assert restored.checkpoint_time == original.checkpoint_time


class TestCheckpointManager:
    """Test CheckpointManager functionality."""

    def test_manager_initialization_default(self):
        """Test CheckpointManager with default directory."""
        manager = CheckpointManager()
        
        assert manager.checkpoint_dir.exists()
        assert manager.checkpoint_dir.name == ".checkpoints"
        assert manager.checkpoint_file.name == "pipeline_checkpoint.json"

    def test_manager_initialization_custom(self):
        """Test CheckpointManager with custom directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = Path(tmpdir) / "custom_checkpoints"
            manager = CheckpointManager(checkpoint_dir=custom_dir)
            
            assert manager.checkpoint_dir == custom_dir
            assert manager.checkpoint_dir.exists()
            assert manager.checkpoint_file == custom_dir / "pipeline_checkpoint.json"

    def test_save_checkpoint(self):
        """Test saving a checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            manager = CheckpointManager(checkpoint_dir=checkpoint_dir)
            
            stage_results = [
                StageResult(
                    name="stage_1",
                    exit_code=0,
                    duration=1.0,
                    timestamp="2024-01-01 12:00:00"
                )
            ]
            
            manager.save_checkpoint(
                pipeline_start_time=1000.0,
                last_stage_completed=1,
                stage_results=stage_results,
                total_stages=5
            )
            
            assert manager.checkpoint_file.exists()
            
            # Verify file contents
            with open(manager.checkpoint_file, 'r') as f:
                data = json.load(f)
            
            assert data['pipeline_start_time'] == 1000.0
            assert data['last_stage_completed'] == 1
            assert len(data['stage_results']) == 1
            assert data['total_stages'] == 5
            assert 'checkpoint_time' in data

    def test_load_checkpoint_exists(self):
        """Test loading an existing checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            manager = CheckpointManager(checkpoint_dir=checkpoint_dir)
            
            # Save a checkpoint first
            stage_results = [
                StageResult(
                    name="stage_1",
                    exit_code=0,
                    duration=1.0,
                    timestamp="2024-01-01 12:00:00"
                )
            ]
            
            manager.save_checkpoint(
                pipeline_start_time=1000.0,
                last_stage_completed=1,
                stage_results=stage_results,
                total_stages=5
            )
            
            # Load it back
            checkpoint = manager.load_checkpoint()
            
            assert checkpoint is not None
            assert checkpoint.pipeline_start_time == 1000.0
            assert checkpoint.last_stage_completed == 1
            assert len(checkpoint.stage_results) == 1
            assert checkpoint.total_stages == 5

    def test_load_checkpoint_not_exists(self):
        """Test loading when checkpoint doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            manager = CheckpointManager(checkpoint_dir=checkpoint_dir)
            
            checkpoint = manager.load_checkpoint()
            
            assert checkpoint is None

    def test_load_checkpoint_corrupted(self):
        """Test loading a corrupted checkpoint file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            manager = CheckpointManager(checkpoint_dir=checkpoint_dir)
            
            # Create a corrupted checkpoint file
            manager.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
            manager.checkpoint_file.write_text("invalid json content {")
            
            # Should return None and log warning
            checkpoint = manager.load_checkpoint()
            
            assert checkpoint is None

    def test_clear_checkpoint(self):
        """Test clearing a checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            manager = CheckpointManager(checkpoint_dir=checkpoint_dir)
            
            # Save a checkpoint
            stage_results = [
                StageResult(
                    name="stage_1",
                    exit_code=0,
                    duration=1.0,
                    timestamp="2024-01-01 12:00:00"
                )
            ]
            
            manager.save_checkpoint(
                pipeline_start_time=1000.0,
                last_stage_completed=1,
                stage_results=stage_results,
                total_stages=5
            )
            
            assert manager.checkpoint_file.exists()
            
            # Clear it
            manager.clear_checkpoint()
            
            assert not manager.checkpoint_file.exists()

    def test_clear_checkpoint_not_exists(self):
        """Test clearing when checkpoint doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            manager = CheckpointManager(checkpoint_dir=checkpoint_dir)
            
            # Should not raise error
            manager.clear_checkpoint()

    def test_checkpoint_exists_true(self):
        """Test checkpoint_exists when checkpoint exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            manager = CheckpointManager(checkpoint_dir=checkpoint_dir)
            
            # Save a checkpoint
            stage_results = [
                StageResult(
                    name="stage_1",
                    exit_code=0,
                    duration=1.0,
                    timestamp="2024-01-01 12:00:00"
                )
            ]
            
            manager.save_checkpoint(
                pipeline_start_time=1000.0,
                last_stage_completed=1,
                stage_results=stage_results,
                total_stages=5
            )
            
            assert manager.checkpoint_exists() is True

    def test_checkpoint_exists_false(self):
        """Test checkpoint_exists when checkpoint doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            manager = CheckpointManager(checkpoint_dir=checkpoint_dir)
            
            assert manager.checkpoint_exists() is False

    def test_checkpoint_exists_corrupted(self):
        """Test checkpoint_exists with corrupted file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            manager = CheckpointManager(checkpoint_dir=checkpoint_dir)
            
            # Create corrupted file
            manager.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
            manager.checkpoint_file.write_text("invalid json")
            
            assert manager.checkpoint_exists() is False

    def test_save_checkpoint_multiple_stages(self):
        """Test saving checkpoint with multiple stage results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            manager = CheckpointManager(checkpoint_dir=checkpoint_dir)
            
            stage_results = [
                StageResult(
                    name="stage_1",
                    exit_code=0,
                    duration=1.0,
                    timestamp="2024-01-01 12:00:00"
                ),
                StageResult(
                    name="stage_2",
                    exit_code=0,
                    duration=2.0,
                    timestamp="2024-01-01 12:01:00"
                ),
                StageResult(
                    name="stage_3",
                    exit_code=0,
                    duration=1.5,
                    timestamp="2024-01-01 12:02:00"
                )
            ]
            
            manager.save_checkpoint(
                pipeline_start_time=1000.0,
                last_stage_completed=3,
                stage_results=stage_results,
                total_stages=5
            )
            
            checkpoint = manager.load_checkpoint()
            
            assert checkpoint is not None
            assert len(checkpoint.stage_results) == 3
            assert checkpoint.last_stage_completed == 3

    def test_save_checkpoint_failure_handling(self):
        """Test handling of save checkpoint failures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            manager = CheckpointManager(checkpoint_dir=checkpoint_dir)
            
            # Make directory read-only to cause save failure
            checkpoint_dir.chmod(0o444)
            
            try:
                stage_results = [
                    StageResult(
                        name="stage_1",
                        exit_code=0,
                        duration=1.0,
                        timestamp="2024-01-01 12:00:00"
                    )
                ]
                
                # Should not raise exception, just log warning
                manager.save_checkpoint(
                    pipeline_start_time=1000.0,
                    last_stage_completed=1,
                    stage_results=stage_results,
                    total_stages=5
                )
            finally:
                # Restore permissions
                checkpoint_dir.chmod(0o755)













