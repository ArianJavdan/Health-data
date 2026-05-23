# Feature: DuckDB Resource

## Status: planned

## Goal
Implement a Dagster `ConfigurableResource` in `health_etl/resources/duckdb_resource.py` that manages
a DuckDB connection and provides a simple interface for the mart layer to write tables.

## What to implement

### `DuckDBResource(ConfigurableResource)`
```python
class DuckDBResource(ConfigurableResource):
    db_path: str  # read from DUCKDB_PATH env var

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        ...

    def write_dataframe(self, df: pl.DataFrame, table_name: str, if_exists: str = "replace") -> None:
        # Uses duckdb's native Polars integration: conn.execute("CREATE OR REPLACE TABLE ... AS SELECT * FROM df")
        ...
```

## Technical notes
- DuckDB has native zero-copy integration with Polars DataFrames via Arrow: no intermediate serialization
- Use `duckdb.connect(db_path)` — DuckDB creates the file if it doesn't exist
- The resource should be configured in `definitions.py` to read `DUCKDB_PATH` from the environment
- For the frontend to query the database, it just needs read access to the `.duckdb` file

## Dependencies
- No other features required; can be built standalone

## Definition of done
- `DuckDBResource` can be instantiated in tests with an in-memory path (`:memory:`)
- Writing a Polars DataFrame creates a queryable DuckDB table
- The resource is registered in `definitions.py`
