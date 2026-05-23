# Feature: Metrics Computation Layer (Parquet → Parquet)

## Status: planned

## Goal
Implement the Layer 2 Dagster assets in `health_etl/assets/metrics/` that consume raw Parquet files
and compute the health/fitness metrics the recommendation engine will reason over.

## Assets to implement

### `sleep_metrics` (`sleep_metrics.py`)
Inputs: `raw_sleep_records`

Per-night aggregation (night = sleep session crossing midnight):
- `total_sleep_min` = sum of Core + Deep + REM durations
- `in_bed_min` = total tracked window including Awake intervals
- `sleep_efficiency` = total_sleep_min / in_bed_min * 100
- `deep_sleep_min`, `deep_pct` = Deep stage totals
- `rem_sleep_min`, `rem_pct` = REM stage totals
- `awakenings_count` = count of Awake intervals > 2 min
- `longest_uninterrupted_min` = longest continuous sleep run

Sleep score (0-100):
```
duration_score     = clamp(total_sleep_min / 480, 0, 1)  # 8h target
consistency_score  = 1 - (awakenings_count / 10).clamp(0, 1)
quality_score      = (deep_pct/20 + rem_pct/25) / 2      # targets: 20% deep, 25% REM
sleep_score = 40*duration_score + 30*consistency_score + 30*quality_score
```

---

### `hrv_baseline` (`hrv_baseline.py`)
Inputs: `raw_hrv_records`

Per-day computation:
- `hrv_sdnn_ms` = mean of all nightly HRV readings for that night
- `hrv_7d_mean`, `hrv_7d_std` = rolling 7-day mean/std (requires ≥7 nights)
- `hrv_28d_mean` = rolling 28-day mean (used as long-term baseline)
- `hrv_zscore` = (hrv_sdnn_ms - hrv_7d_mean) / hrv_7d_std; null if < 7 days of data

---

### `rhr_baseline` (`rhr_baseline.py`)
Inputs: `raw_rhr_records`

Per-day:
- `rhr_bpm` = daily resting HR from Apple
- `rhr_7d_mean` = rolling 7-day mean
- `rhr_delta_bpm` = rhr_bpm - rhr_7d_mean  (positive = elevated = stress)

---

### `vitals_nightly` (`vitals_nightly.py`)
Inputs: `raw_vitals_records`

Per-night aggregation:
- `spo2_avg_pct` = mean SpO2 during sleep window
- `resp_rate_avg` = mean respiratory rate during sleep
- `resp_rate_28d_mean` = rolling 28-day mean of resp_rate_avg
- `resp_rate_delta` = resp_rate_avg - resp_rate_28d_mean
- `wrist_temp_deviation_c` = raw deviation value (Apple provides this directly)
- `temp_flag` = True if wrist_temp_deviation_c > 0.5°C

---

### `fitness_metrics` (`fitness_metrics.py`)
Inputs: `raw_fitness_records`

VO2 Max (Apple provides irregular estimates ~weekly):
- Forward-fill to daily cadence
- `vo2max_30d_trend` = linear regression slope over last 30 days (ml/kg/min per day)
- `cardio_fitness_level` classification by age/sex bands (Apple's thresholds):
  - Male 20-29: Low<36, Below Avg 36-41, Above Avg 41-46, High 46-52, Very High >52
  - Adjust thresholds per user age/sex if profile data is available in the export

Heart Rate Recovery:
- `hrr1_bpm` = latest available HRR1 value (measured post-workout; may be sparse)

---

### `training_load` (`training_load.py`)
Inputs: `raw_workout_records`

Per-day:
- `daily_load` = Σ(effort_score × duration_min) for all workouts that day
  - If `effort_score` is null, estimate from active energy: `energy_kcal / 5` as proxy
- `atl` = exponentially weighted moving average with 7-day span (acute training load)
- `ctl` = exponentially weighted moving average with 28-day span (chronic training load)
- `acwr` = atl / ctl (null if ctl == 0)
- `load_status`:
  - acwr < 0.8  → "Undertraining"
  - 0.8–1.3     → "Optimal"
  - 1.3–1.5     → "Caution"
  - > 1.5       → "High Risk"

## Technical notes
- All rolling window operations: use Polars `Expr.rolling_mean(window_size, min_periods=...)` 
- EWMA: Polars `Expr.ewm_mean(span=7)` and `ewm_mean(span=28)`
- Use `group_by("date").agg(...)` for per-day aggregations
- Output Parquet paths: `{DATA_DIR}/processed/parquet/metrics/{asset_name}.parquet`

## Dependencies
- `features/planned/03-raw-assets.md` must be complete first

## Definition of done
- All 6 metric assets materialize cleanly
- Recovery components (hrv_zscore, rhr_delta_bpm, sleep_score, resp_rate_delta, temp_flag)
  are all present in their respective outputs
- Unit tests in `tests/test_metrics/` validate the scoring math
