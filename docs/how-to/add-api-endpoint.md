# Add an API Endpoint

This guide walks through the steps to add a new endpoint to the D2S backend.

## Overview

Adding a new endpoint typically involves changes across several layers:

1. **Model** — Define or update SQLAlchemy models in `backend/app/models/`
2. **Schema** — Define Pydantic request/response schemas in `backend/app/schemas/`
3. **CRUD** — Implement database operations in `backend/app/crud/`
4. **Endpoint** — Create the route handler in `backend/app/api/api_v1/endpoints/`
5. **Router** — Register the endpoint in `backend/app/api/api_v1/api.py`
6. **Tests** — Add test coverage in `backend/app/tests/`

## Step 1: Define the model

If your endpoint requires a new database table, create a model in `backend/app/models/`. Follow existing conventions — models use PascalCase and inherit from the project's base class.

## Step 2: Create Pydantic schemas

Define request and response schemas in `backend/app/schemas/`. At minimum, create schemas for create, update, and read operations.

## Step 3: Implement CRUD operations

Add database operations in `backend/app/crud/`. Follow the existing pattern of extending the base CRUD class.

## Step 4: Create the endpoint

Create a new file in `backend/app/api/api_v1/endpoints/` with your route handlers. Use FastAPI's dependency injection for authentication and authorization:

```python
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/")
def list_items(current_user = Depends(get_current_approved_user)):
    ...
```

## Step 5: Register the router

Add the new router to `backend/app/api/api_v1/api.py`:

```python
from app.api.api_v1.endpoints import your_module

api_router.include_router(
    your_module.router,
    prefix="/your-resource",
    tags=["your-resource"],
)
```

## Step 6: Add tests

Create a test file in `backend/app/tests/` following the `test_<feature>.py` naming convention. See the [Run the Test Suite](run-tests.md) guide for running tests.
