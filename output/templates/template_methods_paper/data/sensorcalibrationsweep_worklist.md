# Worklist: SensorCalibrationSweep v1.0 (automated)

1. **Record reference baseline reading** — `measure` on `automated` (step_id=1)
2. **Compute calibration offset** — `compute` on `automated` (step_id=2)
3. **Operator sign-off on computed offset** — `annotate` on `human` (step_id=3)
4. **Validate calibration within tolerance** — `validate` on `automated` (step_id=4)
