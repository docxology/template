#!/usr/bin/env python3
"""Download M4 timeseries benchmark data or generate synthetic fallbacks.

Downloads the M4 monthly subset (1000 points per series max) from the
Hugging Face Transformers/M4 dataset if available. Falls back to generating
synthetic realistic patterns (trend + seasonality + noise) saved as JSON
when the dataset is unavailable.

Data saved as JSON files under:
    tests/fixtures/timeseries/m4_monthly/*.json
    tests/fixtures/timeseries/synthetic/*.json  (fallback)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

# Repository root
ROOT = Path(__file__).parent.parent.parent.resolve()

# Output directory
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "timeseries"
M4_OUTPUT = FIXTURES_DIR / "m4_monthly"
SYNTHETIC_OUTPUT = FIXTURES_DIR / "synthetic"

# Maximum points per series (M4 monthly series vary in length; we truncate to 1000)
MAX_POINTS = 1000

# Number of series to sample from M4 (or generate synthetically)
NUM_SERIES = 10  # Reasonable for integration tests; can be increased


def try_download_m4() -> bool:
    """Attempt to download M4 monthly data from Hugging Face datasets.

    Returns:
        True if successful, False otherwise.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        print("⊘ 'datasets' library not available; will use synthetic fallback.")
        return False

    try:
        print("⬇ Loading M4 monthly dataset from Hugging Face...")
        # nosec B615 — research fixture: streaming-mode load of the public
        # M4 forecasting dataset for benchmark seed data only. No model
        # weights or executable assets. The hub-side dataset has a stable
        # schema; if `datasets` later supports content-addressed pinning by
        # SHA we will adopt it here.
        dataset = load_dataset("m4", split="monthly", streaming=True)  # nosec B615
        # Streaming to avoid downloading full dataset (which is huge)
        print(f"✓ Dataset loaded (streaming). Sampling {NUM_SERIES} series...")

        M4_OUTPUT.mkdir(parents=True, exist_ok=True)
        count = 0
        for i, item in enumerate(dataset):
            if count >= NUM_SERIES:
                break
            # item structure: typically {"start": "...", "target": [...], "feat_static_cat": [...], ...}
            # The M4 dataset has "target" as the time series values
            target = item.get("target", [])
            if not target:
                continue
            # Truncate to MAX_POINTS
            values = [float(x) for x in target[:MAX_POINTS]]
            series_id = item.get("instance", str(i))
            # Safe filename
            safe_id = str(series_id).replace("/", "_").replace("\\", "_")
            outpath = M4_OUTPUT / f"series_{safe_id}.json"
            outpath.write_text(json.dumps({"values": values, "id": str(series_id), "length": len(values)}))
            count += 1
            print(f"  ✓ Saved series {count}/{NUM_SERIES}: {outpath.name} ({len(values)} points)")

        print(f"✓ Downloaded {count} M4 monthly series.")
        return True
    except Exception as e:
        print(f"✗ Failed to download M4 dataset: {e}", file=sys.stderr)
        return False


def generate_synthetic_timeseries() -> None:
    """Generate synthetic realistic time series with trend, seasonality, and noise.

    Saves JSON files to tests/fixtures/timeseries/synthetic/.
    """
    SYNTHETIC_OUTPUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed=42)

    for i in range(NUM_SERIES):
        length = rng.integers(500, MAX_POINTS + 1)
        t = np.arange(length)

        # Randomly vary parameters per series
        trend_coef = rng.uniform(-0.5, 0.5)
        seasonal_period = 12  # monthly data: yearly seasonality
        seasonal_amp = rng.uniform(2.0, 10.0)
        noise_scale = rng.uniform(0.5, 3.0)

        trend = trend_coef * t
        seasonal = seasonal_amp * np.sin(2 * np.pi * t / seasonal_period + rng.uniform(0, 2*np.pi))
        noise = rng.normal(0, noise_scale, size=length)

        values = trend + seasonal + noise
        values = values.tolist()

        outpath = SYNTHETIC_OUTPUT / f"synthetic_{i+1:03d}.json"
        outpath.write_text(json.dumps({
            "values": values,
            "id": f"synthetic_{i+1:03d}",
            "length": len(values),
            "parameters": {
                "trend_coef": float(trend_coef),
                "seasonal_period": int(seasonal_period),
                "seasonal_amp": float(seasonal_amp),
                "noise_scale": float(noise_scale),
            }
        }))
        print(f"  ✓ Generated synthetic series {i+1}/{NUM_SERIES}: {outpath.name} ({len(values)} points)")

    print(f"✓ Generated {NUM_SERIES} synthetic time series.")


def main() -> None:
    """Entry point: download M4 data or generate synthetic fallback."""
    import subprocess

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    # Check M4: if directory exists and has full set of series, skip.
    if M4_OUTPUT.exists():
        existing = list(M4_OUTPUT.glob("*.json"))
        if len(existing) >= NUM_SERIES:
            print(f"⊘ M4 monthly data already complete ({len(existing)} series) at {M4_OUTPUT}, skipping download.")
            return
        else:
            print(f"⚠ M4 data incomplete ({len(existing)} series). Removing and re-downloading...")
            subprocess.run(["rm", "-rf", str(M4_OUTPUT)], check=False)

    # Try to download real M4 data
    success = try_download_m4()
    if success:
        return  # done

    # Fallback to synthetic data
    print("⇢ Falling back to synthetic data generation...")
    if SYNTHETIC_OUTPUT.exists():
        existing_synth = list(SYNTHETIC_OUTPUT.glob("*.json"))
        if len(existing_synth) >= NUM_SERIES:
            print(f"⊘ Synthetic data already complete ({len(existing_synth)} series) at {SYNTHETIC_OUTPUT}, skipping generation.")
            return
        else:
            print(f"⚠ Synthetic data incomplete ({len(existing_synth)} series). Regenerating...")
            subprocess.run(["rm", "-rf", str(SYNTHETIC_OUTPUT)], check=False)

    generate_synthetic_timeseries()
    print("\nAll timeseries benchmark data ready.")


if __name__ == "__main__":
    main()
