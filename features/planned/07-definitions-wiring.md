# Feature: Wire Everything into Dagster Definitions

## Status: planned

## Goal
Update `health_etl/definitions.py` to register all assets and resources so Dagster can discover,
schedule, and materialize the full pipeline in one command.

## What to do

```python
# health_etl/definitions.py
import os
from dagster import Definitions, load_assets_from_modules, EnvVar

from health_etl.resources.duckdb_resource import DuckDBResource
from health_etl.assets import raw, metrics, mart

raw_assets     = load_assets_from_modules([raw.sleep, raw.heart_rate, raw.vitals,
                                           raw.fitness, raw.workouts], group_name="raw")
metric_assets  = load_assets_from_modules([metrics.sleep_metrics, metrics.hrv_baseline,
                                           metrics.rhr_baseline, metrics.vitals_nightly,
                                           metrics.fitness_metrics, metrics.training_load],
                                          group_name="metrics")
mart_assets    = load_assets_from_modules([mart.daily_summary], group_name="mart")

defs = Definitions(
    assets=[*raw_assets, *metric_assets, *mart_assets],
    resources={
        "duckdb": DuckDBResource(db_path=EnvVar("DUCKDB_PATH")),
    },
)
```

## Source asset for export.xml

Add a `SourceAsset` so Dagster tracks the raw file as the root of the lineage graph:

```python
from dagster import SourceAsset
export_xml = SourceAsset(key="export_xml", description="Apple Health export file at data/raw/export.xml")
```

## Optional: add a `define_asset_job` for full-pipeline runs

```python
from dagster import define_asset_job, AssetSelection
full_pipeline_job = define_asset_job("full_pipeline", selection=AssetSelection.all())
```

Register it in `Definitions(jobs=[full_pipeline_job])`.

## Technical notes
- `load_assets_from_modules` auto-discovers all `@asset`-decorated functions
- Asset groups appear as visual groupings in the Dagster UI lineage graph
- `EnvVar("DUCKDB_PATH")` defers env var resolution to runtime, not import time

## Dependencies
- All previous features must be complete

## Definition of done
- `dagster asset list` shows all assets with correct groups
- `dagster asset materialize --select '*'` runs end-to-end without error
- Dagster UI at `localhost:3000` shows the full lineage graph
