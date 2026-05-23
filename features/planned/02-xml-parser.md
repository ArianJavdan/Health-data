# Feature: Streaming Apple Health XML Parser

## Status: planned

## Goal
Build a memory-efficient, streaming XML parser in `health_etl/assets/raw/parser.py` that can handle
`export.xml` files that may exceed 1 GB without loading the entire file into memory.

## What to implement

### `parse_records(path, type_filter)`
- Uses `xml.etree.ElementTree.iterparse` in streaming mode
- Yields `dict` rows for `<Record>` elements matching `type_filter`
- Fields to extract per record: `type`, `sourceName`, `unit`, `startDate`, `endDate`, `value`
- Clears elements from memory after yielding (`elem.clear()`) to keep memory constant

### `parse_workouts(path)`
- Same streaming approach for `<Workout>` elements
- Fields: `workoutActivityType`, `duration`, `durationUnit`, `totalEnergyBurned`, `startDate`, `endDate`
- Also extracts nested `<WorkoutStatistics>` children for per-workout energy, HR, etc.

### `parse_category_records(path, type_filter)`
- Handles `HKCategoryTypeIdentifierSleepAnalysis` which uses integer `value` codes
- Maps value codes to human-readable stage names:
  - 0 → InBed, 1 → Asleep (legacy), 2 → Awake, 3 → Core, 4 → Deep, 5 → REM

## Technical notes
- `startDate` / `endDate` are strings like `2024-01-15 06:42:00 +0200` (space-separated, no colon in offset)
- `datetime.fromisoformat` does **not** reliably parse `+HHMM` offsets without a colon; use
  `datetime.strptime(s, "%Y-%m-%d %H:%M:%S %z")` which handles both `+HHMM` and `+HH:MM` forms
- Apple may export duplicate records from multiple sources (iPhone + Watch); keep the Watch source
  as the primary and flag duplicates for deduplication in the raw asset layer
- The XML root element is `<HealthData>`, containing `<ExportDate>`, `<Me>`, and then thousands of
  `<Record>` and `<Workout>` children

## Dependencies
- None beyond Python stdlib (`xml.etree.ElementTree`, `datetime`)
- Called by all assets in `health_etl/assets/raw/`

## Definition of done
- Parser handles a 500 MB export.xml without exceeding 200 MB peak memory
- All sleep stage value codes are correctly mapped
- Unit tests in `tests/test_metrics/` use a small synthetic XML fixture generated via `conftest.py`
