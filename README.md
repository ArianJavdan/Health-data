# Health Data — Apple Health ETL Pipeline

Dagster pipeline that turns a raw Apple Health `export.xml` into analytics-ready metrics
for a downstream training recommendation engine.

## What it does

Reads Apple Health data → computes recovery, fitness, and training load metrics → writes
a queryable `daily_summary` table to DuckDB that a frontend or AI can consume.

**Key output metrics per day:**
- `recovery_score` (0–100) + `recovery_status` label (Well Rested / Good / OK / Tired / Fatigued)
- `training_recommendation` (Push Hard / Train Normally / Moderate Intensity / Light Activity Only / Rest Day)
- Sleep: `sleep_score`, `deep_pct`, `rem_pct`, `sleep_efficiency`
- HRV: `hrv_sdnn_ms`, `hrv_zscore` vs 7-day baseline
- Resting HR: `rhr_bpm`, `rhr_delta_bpm` vs 7-day baseline
- Fitness: `vo2max_ml_kg_min`, `cardio_fitness_level`, `vo2max_30d_trend`
- Training load: `atl`, `ctl`, `acwr`, `load_status`

## Stack

| Layer | Tool |
|---|---|
| Orchestration | Dagster |
| Data processing | Polars |
| XML parsing | Python stdlib (`xml.etree.ElementTree`) |
| Intermediate storage | Parquet (pyarrow) |
| Analytics DB | DuckDB |

## Getting started

```bash
# 1. Install dependencies (requires uv)
uv sync

# 2. Copy env config
cp .env.example .env

# 3. Place your Apple Health export
#    Health app → profile picture → Export All Health Data → unzip → copy export.xml
cp ~/Downloads/apple_health_export/export.xml data/raw/export.xml

# 4. Run the full pipeline
dagster asset materialize --select '*'

# 5. Query results
duckdb data/processed/health.duckdb \
  "SELECT date, recovery_score, recovery_status, training_recommendation FROM daily_summary ORDER BY date DESC LIMIT 7"
```

## Development roadmap

See `features/planned/` for detailed specs of each remaining step.

| Step | Feature | Status |
|---|---|---|
| 1 | Project scaffold | **done** |
| 2 | Streaming XML parser | planned |
| 3 | Raw ingestion assets (XML → Parquet) | planned |
| 4 | DuckDB resource | planned |
| 5 | Metrics computation layer | planned |
| 6 | Daily summary mart | planned |
| 7 | Definitions wiring | planned |
| 8 | Test suite | planned |
