# Feature: Raw Ingestion Assets (XML → Parquet)

## Status: planned

## Goal
Implement the Layer 1 Dagster assets that read `data/raw/export.xml` via the streaming parser and
write typed, deduplicated Polars DataFrames as Parquet files to `data/processed/parquet/raw/`.

## Assets to implement

Each asset lives in `health_etl/assets/raw/` and is decorated with `@asset`.

### `raw_sleep_records` (`sleep.py`)
- Source: `HKCategoryTypeIdentifierSleepAnalysis`
- Output schema: `date date, start_ts timestamp, end_ts timestamp, stage str, duration_min f64, source str`
- Deduplication: prefer `sourceName` containing "Watch"; drop exact duplicates on (start_ts, end_ts, stage)

### `raw_hrv_records` (`heart_rate.py`)
- Source: `HKQuantityTypeIdentifierHeartRateVariabilitySDNN`
- Output schema: `date date, ts timestamp, hrv_sdnn_ms f64, source str`
- One row per measurement; Apple Watch measures HRV nightly during sleep

### `raw_rhr_records` (`heart_rate.py`)
- Source: `HKQuantityTypeIdentifierRestingHeartRate`
- Output schema: `date date, rhr_bpm f64, source str`
- Apple provides one daily estimate; keep latest per day if multiple

### `raw_heart_rate_records` (`heart_rate.py`)
- Source: `HKQuantityTypeIdentifierHeartRate`
- Output schema: `date date, ts timestamp, hr_bpm f64, context str, source str`
- High-frequency during workouts; sampled at rest otherwise

### `raw_vitals_records` (`vitals.py`)
- Sources: `OxygenSaturation`, `RespiratoryRate`, `AppleSleepingWristTemperature`
- Output schema: `date date, ts timestamp, metric str, value f64, unit str, source str`
- Wide format with `metric` column to keep all three in one table

### `raw_fitness_records` (`fitness.py`)
- Sources: `VO2Max`, `HeartRateRecoveryOneMinute`
- Output schema: `date date, ts timestamp, metric str, value f64, unit str, source str`

### `raw_workout_records` (`workouts.py`)
- Sources: `HKWorkout` elements + `PhysicalEffort`, `EstimatedWorkoutEffortScore`, `ActiveEnergyBurned`
- Output schema: `date date, start_ts timestamp, end_ts timestamp, activity_type str,
  duration_min f64, energy_kcal f64, effort_score f64, source str`

## Technical notes
- All assets declare `deps=["export_xml"]` (a `SourceAsset` pointing to `data/raw/export.xml`)
- Use Polars `LazyFrame` → `.collect()` for the transformations so the chain is lazy
- Write Parquet with `pyarrow` engine: `df.write_parquet(path, use_pyarrow=True)`
- Output paths follow the pattern `{DATA_DIR}/processed/parquet/raw/{asset_name}.parquet`
- Read `DATA_DIR` from environment via `python-dotenv`

## Dependencies
- `features/planned/02-xml-parser.md` must be complete first

## Definition of done
- All 7 assets materialize without error against a real `export.xml`
- Each Parquet file has correct column types (no string dates)
- Row counts are logged as Dagster asset metadata
