# Generate Vector Format Files

Vector layers are automatically exported to GeoParquet and FlatGeobuf formats for efficient access from QGIS and other desktop GIS tools. For existing vector layers created before these features were added, use the backfill command to generate the format files.

## Generate all formats

```bash
docker compose exec backend python app/utils/generate_vector_formats.py
```

## Generate a specific format

```bash
# GeoParquet only
docker compose exec backend python app/utils/generate_vector_formats.py --format parquet

# FlatGeobuf only
docker compose exec backend python app/utils/generate_vector_formats.py --format flatgeobuf
```

## Generate for a specific project

```bash
docker compose exec backend python app/utils/generate_vector_formats.py --project-id <project-uuid>
```

## Force regeneration

To overwrite existing format files:

```bash
docker compose exec backend python app/utils/generate_vector_formats.py --force
```

The command displays progress per format and provides a summary of generated, skipped, and failed files.
