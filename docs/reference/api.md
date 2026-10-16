# API Reference

D2S exposes a versioned REST API under `/api/v1/`. FastAPI auto-generates interactive documentation that is available when the application is running.

## Interactive API documentation

| Format | URL | Description |
|--------|-----|-------------|
| Swagger UI | `/docs` | Interactive explorer — try endpoints directly from the browser |
| ReDoc | `/redoc` | Readable, searchable API reference |
| OpenAPI JSON | `/api/v1/openapi.json` | Machine-readable OpenAPI 3.x specification |

## Authentication

Most endpoints require authentication via one of:

- **JWT Bearer Token** — Obtained by logging in through the `/api/v1/auth/login` endpoint. Access tokens are valid for 15 minutes; refresh tokens for 30 days.
- **API Key** — For programmatic access to select endpoints. Passed via the `X-API-Key` header. Each key has any combination of `read`, `create`, `update`, and `delete` scopes and is managed through `/api/v1/api-keys`. The `api_access_token` field on `/api/v1/users/current` is deprecated. It holds the user's key only while they have exactly one active key and that key has the `read` scope, otherwise it is `null`. Clients should list keys through `/api/v1/api-keys`, and d2spy users can set the `D2S_API_KEY` environment variable.

See [Authentication and Authorization](../explanation/authentication.md) for design details.

## Endpoint groups

The API is organized into the following resource groups:

| Group | Prefix | Description |
|-------|--------|-------------|
| Auth | `/auth` | Login, registration, token refresh |
| Users | `/users` | User profiles and account management |
| Teams | `/teams` | Team CRUD and membership |
| Projects | `/projects` | Project CRUD, bookmarks, and membership |
| Flights | `/flights` | Flight records within projects |
| Data Products | `/data_products` | Raster and point cloud data products |
| Raw Data | `/raw_data` | Unprocessed upload management |
| Vector Layers | `/vector_layers` | GeoJSON and shapefile layers |
| Locations | `/locations` | Geographic boundaries |
| Campaigns | `/campaigns` | Field data collection |
| STAC | `/stac` | SpatioTemporal Asset Catalog publishing |
| Admin | `/admin` | User approval, statistics, extensions |
| Health | `/health` | Service health checks |
