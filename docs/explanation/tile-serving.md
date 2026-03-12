# Tile Serving

This page explains how D2S serves geospatial data as map tiles to the frontend — covering raster tiles, vector tiles, point clouds, and the caching layer.

## Overview

D2S uses three specialized services to render different data types as tiles, all fronted by a Varnish caching layer:

```
Client → Varnish Cache → TiTiler (raster)
                       → pg_tileserv (vector)
                       → Direct HTTP (point cloud)
```

## Raster tiles (TiTiler)

[TiTiler](https://developmentseed.org/titiler/) is a dynamic tile server that reads Cloud Optimized GeoTIFFs (COGs) and generates map tiles on demand. Because COGs use internal tiling and overviews, TiTiler can serve tiles at any zoom level by reading only the relevant bytes from the file via HTTP range requests.

The frontend requests tiles using standard `{z}/{x}/{y}` URL patterns. TiTiler supports dynamic band selection, rescaling, and color map application — the frontend uses these capabilities for visualization controls like band combination selection and color ramp adjustments.

## Vector tiles (pg_tileserv)

[pg_tileserv](https://github.com/CrunchyData/pg_tileserv) connects directly to the PostgreSQL/PostGIS database and generates Mapbox Vector Tiles (MVT) from spatial tables. When a user uploads a shapefile or GeoJSON, the data is stored in PostGIS and immediately available as vector tiles.

Vector tiles are rendered client-side by MapLibre GL JS, which allows dynamic styling and interaction without re-fetching data from the server.

## Point cloud visualization (Potree)

Point cloud data in COPC format is not served as traditional map tiles. Instead, the [Potree](https://potree.github.io/) WebGL viewer fetches point data directly via HTTP range requests against the COPC file. Potree handles level-of-detail rendering, loading more points as the user zooms in.

## Caching with Varnish

All tile requests (raster and vector) are routed through [Varnish](https://varnish-cache.org/), an HTTP caching layer. Varnish serves previously generated tiles from its cache, reducing the load on TiTiler and pg_tileserv.

Tiles are accessed via signed URLs that encode:

- The resource being accessed (project, flight, data product)
- An expiration timestamp
- A cryptographic signature derived from `TILE_SIGNING_SECRET`

Varnish validates the signature and expiration before serving the tile or forwarding the request to the upstream service. This ensures that only authorized users with valid, time-limited URLs can access tile data.

## Why this architecture?

- **Cloud-native formats** (COG, COPC) eliminate the need to pre-generate tile pyramids, reducing storage and processing overhead.
- **Dynamic tile generation** allows the frontend to request custom visualizations (band combinations, color maps) without storing multiple versions of the same data.
- **Caching** ensures that frequently accessed tiles are served quickly without regenerating them.
- **Signed URLs** decouple tile access control from the main API authentication system, allowing tiles to be cached and served efficiently.
