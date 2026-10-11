# Backend Structure

The backend is a FastAPI application located in `backend/`. This page describes the directory layout and the role of each module.

## Directory layout

```
backend/
├── alembic/              # Database migrations (Alembic)
│   └── versions/         # Individual migration scripts
├── app/
│   ├── api/
│   │   ├── api_v1/
│   │   │   ├── api.py        # Main router — registers all endpoint modules
│   │   │   └── endpoints/    # Route handlers (one file per resource)
│   │   └── extras/           # Utility routes
│   ├── core/
│   │   ├── config.py         # Application settings (Pydantic BaseSettings)
│   │   ├── security.py       # JWT creation, password hashing, auth deps
│   │   ├── celery_app.py     # Celery application configuration
│   │   ├── mail.py           # Email configuration
│   │   ├── logging.py        # Logger setup
│   │   ├── exceptions.py     # Custom exception classes
│   │   └── utils.py          # Core utility functions
│   ├── crud/                 # Database CRUD operations (one file per model)
│   ├── db/                   # Database session and base model class
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── tasks/                # Celery async task definitions
│   ├── tests/                # pytest test suite
│   ├── utils/                # Utility modules and external integrations
│   ├── scripts/              # Command-line scripts
│   ├── seeds/                # Database seeding scripts
│   ├── main.py               # FastAPI application initialization
│   ├── middleware.py          # Custom ASGI middleware
│   ├── extensions.py          # Plugin/extension system
│   └── telemetry.py          # OpenTelemetry configuration
├── celery/                   # Celery worker startup scripts
├── potree/                   # Potree library for 3D point cloud visualization
└── pc-gltf-viewer/           # Point cloud glTF viewer
```

## Module roles

| Module | Role |
|--------|------|
| `api/api_v1/endpoints/` | Route handlers — each file defines routes for one resource (e.g., `projects.py`, `flights.py`). Registered in `api.py`. |
| `core/` | Application-wide concerns: settings, security, Celery config, email, logging. |
| `crud/` | Database access layer. Each file wraps SQLAlchemy queries for a specific model. |
| `db/` | Database session factory (`SessionLocal`) and declarative base class. |
| `models/` | SQLAlchemy ORM models mapping to PostgreSQL tables. |
| `schemas/` | Pydantic models for request validation and response serialization. |
| `tasks/` | Celery task definitions for background processing (uploads, image processing, STAC publishing, analytics). |
| `tests/` | pytest modules organized by layer (`api/`, `crud/`, `core/`, `utils/`). |
| `utils/` | Shared utilities and integrations with external tools. |
| `seeds/` | Scripts for populating database tables with initial data. |
