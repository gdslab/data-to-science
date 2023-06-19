# Backend Structure
## Root directory tree
<pre>
.
├── alembic
│   └── versions
└── app
    ├── api
    │   └── api_v1
    │       └── endpoints
    ├── core
    ├── crud
    ├── db
    ├── models
    ├── schemas
    └── tests
        └── api
            └── api_v1
</pre>

| Folder          | Description                                     |
| --------------- | ----------------------------------------------- |
| **alembic**     | Database migrations                             |
| **app**         | FastAPI application                             |
| **app/api**     | Versioned API endpoints                         |
| **app/core**    | Application settings and security               |
| **app/db**      | Base database class and session                 |
| **app/crud**    | Basic and model specific CRUD utility functions |
| **app/models**  | Database models                                 |
| **app/schemas** | Pydantic schemas                                |
| **app/tests**   | Tests for API endpoints                         |

## *app/api* file tree
<pre>
.
├── api_v1
│   ├── api.py
│   └── endpoints
│       ├── auth.py
│       ├── groups.py
│       ├── projects.py
│       └── users.py
└── deps.py
</pre>

| File                             | Description                                                |
| -----------------------------    | ---------------------------------------------------------- |
| **api_v1/api.py**                | Setup main APIRouter, establish endpoint prefixes and tags |
| **api_v1/endpoints**             | FastAPI endpoints ("routes")                               |
| **api_v1/endpoints/auth.py**     | Endpoints used for authentication                          |
| **api_v1/endpoints/groups.py**   | Endpoints used for groups related operations               |
| **api_v1/endpoints/projects.py** | Endpoints used for projects related operations             |
| **api_v1/endpoints/users.py**    | Endpoints used for user related operations                 |
| **deps.py**                      | Dependencies used by endpoints (e.g., db session creation) |

## *app/core* file tree
<pre>
.
├── config.py
└── security.py
</pre>

| File                          | Description                                                |
| ----------------------------- | ---------------------------------------------------------- |
| **config.py**                 | Creates Settings class using environment variables         |
| **security.py**               | JWT token creation and password validation                 |

## *app/crud* file tree
<pre>
.
├── base.py
└── crud_user.py
</pre>

| File                | Description                                                           |
| ------------------- | --------------------------------------------------------------------- |
| **base.py**         | CRUD class that provides create, read, update, and remove methods     |
| **crud_user.py**    | CRUD operations specific to the user model (e.g., find user by email) |

## *app/db* file tree
<pre>
.
├── base_class.py
├── base.py
└── session.py

</pre>

| File                          | Description                                                               |
| ----------------------------- | ------------------------------------------------------------------------- |
| **base_class.py**             | Creates Base class used by database models                                |
| **base.py**                   | Imports base class and database models prior to use by Alembic            |
| **session.py**                | Setup engine and Session class for communicating with PostgreSQL database |

## *app/models* file tree
<pre>
.
└── user.py
</pre>

| File                          | Description                        |
| ----------------------------- | ---------------------------------- |
| **user.py**                   | Database model for the users table | 


## *app/schemas* file tree
<pre>
└── user.py
</pre>

| File                          | Description                                                               |
| ----------------------------- | ------------------------------------------------------------------------- |
| **user.py**                   | Pydantic schemas for request/response models                              |

## *app/tests* file tree
<pre>
├── api
│   └── api_v1
│       └── test_users.py
└── conftest.py
</pre>

| File                         | Description                                                                |
| ---------------------------- | -------------------------------------------------------------------------- |
| **api/api_v1/test_users.py** | Tests for /users/ endpoints                                                |
| **conftest.py**              | Testing configurations (e.g., creates TestClient used by endpoint modules) |