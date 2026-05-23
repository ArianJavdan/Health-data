# Feature: Test Suite

## Status: planned

## Goal
Write a pytest suite that validates metric computations against synthetic data, so the pipeline can
be confidently iterated without requiring a real `export.xml`.

## What to implement

### `tests/conftest.py` — synthetic fixtures

```python
import pytest
import polars as pl
from datetime import date, datetime, timedelta

@pytest.fixture
def sample_sleep_records():
    """14 nights of sleep data with realistic stage durations."""
    rows = []
    for i in range(14):
        night = date(2024, 1, 1) + timedelta(days=i)
        base = datetime(2024, 1, i+1, 23, 0)
        rows += [
            {"date": night, "start_ts": base, "end_ts": base + timedelta(hours=1, minutes=30), "stage": "Core"},
            {"date": night, "start_ts": base + timedelta(hours=1, minutes=30), "end_ts": base + timedelta(hours=2, minutes=45), "stage": "Deep"},
            {"date": night, "start_ts": base + timedelta(hours=2, minutes=45), "end_ts": base + timedelta(hours=4), "stage": "REM"},
            {"date": night, "start_ts": base + timedelta(hours=4), "end_ts": base + timedelta(hours=7), "stage": "Core"},
        ]
    return pl.DataFrame(rows)

@pytest.fixture
def sample_hrv_records():
    """14 nights of HRV readings centred at 55ms with small variance."""
    ...

@pytest.fixture
def sample_rhr_records():
    """14 days of RHR readings centred at 52 bpm."""
    ...
```

### `tests/test_metrics/test_sleep_metrics.py`
- Assert `sleep_score` is between 0 and 100
- Assert `deep_pct` + `rem_pct` + core_pct ≈ 100 (within floating point)
- Assert a night with 0 min deep sleep scores lower than one with 20% deep sleep

### `tests/test_metrics/test_recovery_score.py`
- Assert `temp_flag=True` always produces `recovery_score ≤ 45`
- Assert perfect inputs (hrv_zscore=+2, rhr_delta=-3, sleep_score=95, resp_delta=-0.5)
  produce score > 85
- Assert terrible inputs (hrv_zscore=-2, rhr_delta=+8, sleep_score=20) produce score < 40
- Assert recovery_status labels match the score bands

### `tests/test_metrics/test_training_load.py`
- Assert ACWR = 1.0 when atl == ctl
- Assert a week of high-volume training raises ACWR above 1.3
- Assert `load_status` == "Optimal" for ACWR in 0.8–1.3

## Technical notes
- Import the pure computation functions directly (not the Dagster assets) for unit tests
- Factor the scoring math out of the asset functions into standalone helpers so they are testable
  without Dagster context
- Use `pytest.approx` for floating point comparisons

## Dependencies
- `features/planned/05-metrics-layer.md` and `features/planned/06-daily-mart.md` must be complete

## Definition of done
- `pytest tests/` passes with zero failures
- Coverage of all score computation branches (temp_flag, low/high z-scores, boundary bands)
