# Feature: Daily Summary Mart (DuckDB)

## Status: planned

## Goal
Implement `health_etl/assets/mart/daily_summary.py` — the final Dagster asset that joins all metric
Parquet outputs into a single `daily_summary` table in DuckDB, then computes the recovery score,
recovery status label, and training recommendation label.

## Schema of `daily_summary`

| Column | Type | Source |
|---|---|---|
| `date` | date | primary key |
| `sleep_score` | float | sleep_metrics |
| `total_sleep_min` | float | sleep_metrics |
| `deep_pct` | float | sleep_metrics |
| `rem_pct` | float | sleep_metrics |
| `sleep_efficiency` | float | sleep_metrics |
| `hrv_sdnn_ms` | float | hrv_baseline |
| `hrv_zscore` | float | hrv_baseline |
| `hrv_7d_mean` | float | hrv_baseline |
| `rhr_bpm` | float | rhr_baseline |
| `rhr_delta_bpm` | float | rhr_baseline |
| `spo2_avg_pct` | float | vitals_nightly |
| `resp_rate_avg` | float | vitals_nightly |
| `resp_rate_delta` | float | vitals_nightly |
| `wrist_temp_deviation_c` | float | vitals_nightly |
| `temp_flag` | bool | vitals_nightly |
| `vo2max_ml_kg_min` | float | fitness_metrics |
| `vo2max_30d_trend` | float | fitness_metrics |
| `cardio_fitness_level` | str | fitness_metrics |
| `hrr1_bpm` | float | fitness_metrics |
| `daily_load` | float | training_load |
| `atl` | float | training_load |
| `ctl` | float | training_load |
| `acwr` | float | training_load |
| `load_status` | str | training_load |
| `recovery_score` | float | computed |
| `recovery_status` | str | computed |
| `training_recommendation` | str | computed |

## Recovery Score Algorithm

```python
def zscore_to_score(z: float) -> float:
    # z=-2 → 0, z=0 → 50, z=+2 → 100; clamped
    return max(0.0, min(100.0, 50.0 + z * 25.0))

def rhr_delta_to_score(delta_bpm: float) -> float:
    # delta=+10 → 0, delta=0 → 75, delta=-5 → 100; clamped
    return max(0.0, min(100.0, 75.0 - delta_bpm * 7.5))

def resp_delta_to_score(delta: float) -> float:
    # delta=+3 → 0, delta=0 → 80, delta=-1 → 100; clamped
    return max(0.0, min(100.0, 80.0 - delta * 26.7))

def compute_recovery_score(row) -> float:
    hrv_component   = zscore_to_score(row.hrv_zscore)    * 0.40
    rhr_component   = rhr_delta_to_score(row.rhr_delta_bpm) * 0.25
    sleep_component = (row.sleep_score or 50.0)           * 0.25
    resp_component  = resp_delta_to_score(row.resp_rate_delta or 0) * 0.10

    score = hrv_component + rhr_component + sleep_component + resp_component

    if row.temp_flag:
        score = min(score, 45.0)  # illness/alcohol override

    return round(score, 1)
```

## Recovery Status Labels

| Score | Status |
|---|---|
| 85–100 | Well Rested |
| 70–84 | Good |
| 55–69 | OK |
| 40–54 | Tired |
| 0–39 | Fatigued |

## Training Recommendation Labels

| Recovery Status | Load Status | Recommendation |
|---|---|---|
| Well Rested | Optimal or Undertraining | Push Hard |
| Good | Optimal | Train Normally |
| Good | Caution or High Risk | Moderate Intensity |
| OK | any | Moderate Intensity |
| Tired | any | Light Activity Only |
| Fatigued | any | Rest Day |
| any | temp_flag=True | Rest Day |

## Technical notes
- Join on `date` using Polars `join(..., how="left")` starting from a date spine
- The `daily_summary` asset depends on all 6 metric assets
- Write to DuckDB via `DuckDBResource.write_dataframe(df, "daily_summary")`
- Also write as Parquet at `{DATA_DIR}/processed/parquet/mart/daily_summary.parquet`
  so the frontend has a fallback that doesn't require DuckDB

## Dependencies
- `features/planned/04-duckdb-resource.md`
- `features/planned/05-metrics-layer.md`

## Definition of done
- `daily_summary` table is queryable in DuckDB with correct types
- Every date with ≥ sleep + HRV data has a non-null recovery_score
- Days with `temp_flag=True` have `recovery_score ≤ 45`
