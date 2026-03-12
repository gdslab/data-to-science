# Data Pipeline

This page explains how user-uploaded data flows through D2S — from upload to storage to visualization.

## Upload flow

D2S uses [tusd](https://tus.io/) for resumable file uploads. This ensures that large files (orthomosaics, point clouds) can be uploaded reliably, even over unstable connections.

1. The client initiates an upload through the tusd service.
2. tusd stores the file in a configured upload directory (`TUSD_STORAGE`).
3. Once the upload completes, tusd notifies the FastAPI backend via a webhook.
4. The backend creates a database record and dispatches a Celery task for processing.

## Data product types

D2S supports the following data product types when uploading to a flight:

| Type | Accepted formats | Description |
|------|-----------------|-------------|
| **DEM** | `.tif` | Digital elevation models |
| **Ortho** | `.tif` | Orthomosaic imagery |
| **Point Cloud** | `.las`, `.laz` | 3D point cloud data |
| **Panoramic** | `.jpg`, `.jpeg`, `.png`, `.webp`, `.avif` | Panoramic imagery |
| **3DGS** | `.ply`, `.zip` | 3D Gaussian Splatting models (`.zip` for LCC format) |
| **Other** | `.tif` | User-defined raster type with a custom label |

## Processing

Processing tasks run asynchronously via Celery workers. The specific processing depends on the data type:

### Raster data — DEM, Ortho, and Other (GeoTIFF)

Uploaded GeoTIFFs are converted to Cloud Optimized GeoTIFFs (COGs). COGs use internal tiling and overviews to support efficient HTTP range requests, enabling clients to fetch only the tiles they need at the appropriate zoom level. DEM, Ortho, and Other types all follow this same conversion pipeline.

### Point cloud data (LAS/LAZ)

Point cloud files are converted to Cloud Optimized Point Cloud (COPC) format. Like COGs, COPC files support range requests, allowing the Potree viewer to stream point data progressively.

### 3D Gaussian Splatting (PLY/ZIP)

3D Gaussian Splatting (3DGS) uploads are validated and copied to static file storage. Uploads can be a `.ply` file or a `.zip` file in the LCC format. Once validated, the data product is made available for visualization through a WebGL-based viewer.

### Panoramic imagery

Panoramic images are validated (checking dimensions to confirm the image has the expected aspect ratio for panoramic content) and copied to static file storage.

### Vector data (GeoJSON/Shapefile)

Vector uploads are ingested into PostgreSQL/PostGIS tables. Optionally, GeoParquet and FlatGeobuf format files are generated for desktop GIS access.

## Task tracking

Each processing task creates a `Job` record in the database. The frontend polls for job status updates, displaying progress indicators to the user. When processing completes, the data product record is updated with the final file location and metadata.

## Storage layout

Processed files are organized on disk by project, flight, and data product UUIDs:

```
projects/
└── <project-uuid>/
    └── flights/
        └── <flight-uuid>/
            └── data_products/
                └── <data-product-uuid>/
                    └── <file-uuid>.tif  (or .copc.laz, .ply, .jpg, etc.)
```

## Visualization

Once processed, data is served to the frontend through specialized services:

- **Raster tiles** (DEM, Ortho, Other) — TiTiler reads COG files and generates map tiles on the fly.
- **Vector tiles** — pg_tileserv generates Mapbox Vector Tiles (MVT) from PostGIS tables.
- **Point clouds** — The Potree viewer fetches COPC data directly via HTTP range requests.
- **3D Gaussian Splatting** — Rendered via a WebGL-based viewer.
- **Panoramic imagery** — Displayed through a dedicated panoramic viewer.

Raster and vector tile requests pass through a Varnish caching layer with signed URLs for access control. See [Tile Serving](tile-serving.md) for details.
