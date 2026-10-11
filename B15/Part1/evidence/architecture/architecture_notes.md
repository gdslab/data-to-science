# Baseline Architecture: Data to Science (D2S)

## 1. Architectural Overview

The **Data to Science** platform is organized as a multi-tier, distributed web system composed of modern asynchronous micro-frameworks and geospatial processing engines:

1. **Frontend Presentation Tier (React 18 / TypeScript)**:
   - Provides an interactive geospatial portal built with Vite, TailwindCSS, and Material UI.
   - Embeds map viewports (MapLibre/OpenLayers) and 3D point cloud viewers (Potree/PlayCanvas).
   - Manages user sessions using the React Context API (`AuthContext.tsx`) and transparently re-authenticates expired sessions via Axios response interceptors (`api.ts`).

2. **API & Interface Tier (FastAPI / Starlette)**:
   - Exposes RESTful endpoints organized modularly under `app/api/api_v1/endpoints/`.
   - Utilizes FastAPI's Dependency Injection system (`app/api/deps.py`) to enforce authentication, authorization, and database session lifecycles.
   - Enforces rate limiting (`slowapi`), distributed tracing (`OpenTelemetry`), and security middlewares.

3. **Data Access & Persistence Tier (SQLAlchemy 2.0 / PostgreSQL + PostGIS)**:
   - Employs the **Repository Pattern** via a generic base class (`CRUDBase`) and dedicated domain repositories (`CRUDDataProduct`, `CRUDProject`, `CRUDUser`).
   - Maps spatial entities and STAC properties into PostgreSQL tables with PostGIS extensions for spatial queries and GeoJSON serialization.

4. **Static Asset Authorization Tier (Starlette / Custom Proxy)**:
   - Employs the **Decorator / Proxy Pattern** via `ProtectedStaticFiles`, wrapping `RangedStaticFiles` to guard static geospatial files (GeoTIFF, COPC LAZ).
   - Validates JWT session cookies and API keys prior to streaming multi-gigabyte raster files, and dynamically compiles on-demand parquet datasets.

5. **Asynchronous Task & Workflow Tier (Celery / Redis / RabbitMQ)**:
   - Dispatches background jobs for upload finalization, STAC indexing, and point cloud preview generation.
   - Interfaces via RPC client (`RpcClient`) to remote compute nodes running photogrammetry algorithms (Agisoft Metashape or OpenDroneMap) utilizing the **Strategy Pattern**.

---

## 2. Source Locations by Architectural Layer

| Architectural Layer | Baseline Source Files |
|---|---|
| **Frontend Client** | `frontend/src/main.tsx`, `App.tsx`, `router.tsx`, `AuthContext.tsx`, `api.ts` |
| **API Interface & Routing** | `backend/app/main.py`, `backend/app/api/api_v1/api.py`, `backend/app/api/api_v1/endpoints/*` |
| **Dependency Injection** | `backend/app/api/deps.py`, `backend/app/core/security.py` |
| **Persistence / Repository** | `backend/app/crud/base.py`, `backend/app/crud/crud_data_product.py`, `crud_project.py`, `crud_user.py` |
| **Domain Models** | `backend/app/models/data_product.py`, `project.py`, `flight.py`, `user.py`, `project_member.py` |
| **Static File Authorization** | `backend/app/utils/ProtectedStaticFiles.py`, `backend/app/utils/staticfiles.py` |
| **Asynchronous Tasks & Workers** | `backend/app/tasks/upload_tasks.py`, `post_upload_tasks.py`, `raw_image_processing_tasks.py`, `stac_tasks.py` |
| **External Photogrammetry RPC** | `backend/app/utils/RpcClient.py`, `backend/app/tasks/raw_image_processing_tasks.py` |

The diagram `architecture.mmd` models these interactions and communication flows.
