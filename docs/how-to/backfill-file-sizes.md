# Backfill Data Product and Raw Data File Sizes

Data products and raw data persist their on-disk byte size in a `file_size` column so that per-user **data usage** (shown on the admin Project Storage and User Activity pages) can be computed as a fast SQL `SUM` instead of walking the filesystem on every request.

New uploads record `file_size` automatically when initial processing finishes. For records created **before** this column was added, run the backfill once per environment to populate the existing rows. This command does **not** run automatically.

## Prerequisites

Apply the migration that adds the `file_size` columns first:

```bash
docker compose exec backend alembic upgrade head
```

## Run the backfill

```bash
docker compose exec backend python app/utils/backfill_file_sizes.py
```

The command walks each active data product and raw data directory that is still missing a `file_size`, stores the computed size, and prints a per-record line plus a summary of successes and errors. It only touches rows where `file_size` is `NULL`, so it is safe to re-run.

## What counts as data usage

Data usage totals cover **data products** (rasters, point clouds, etc.) and **raw data** only.

Vector layers are **not** included. Vector data is stored as per-feature rows in the database (PostGIS geometry plus JSONB properties) rather than as a single file, and the GeoParquet/FlatGeobuf files exported for download are not measured. Because vector data is typically small relative to rasters and point clouds, it is intentionally excluded from the data-usage figures.
