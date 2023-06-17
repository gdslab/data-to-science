# Backend Structure
## Root directory tree
<pre>
├── api
│   └── api_v1
│       └── endpoints
├── core
├── db
├── models
├── schemas
└── tests
    └── api
        └── api_v1
</pre>

| Folder      | Description             |
| ----------- | ----------------------- |
| **api**     | Versioned API endpoints |
| **core**    | Config settings         |
| **db**      | Database utilities      |
| **models**  | Database models         |
| **schemas** | Pydantic schemas        |
| **tests**   | Tests for API endpoints |

## *api* file tree
<pre>
├── api_v1
│   ├── api.py
│   └── endpoints
│       ├── auth.py
│       └── users.py
└── deps.py
</pre>

| File                          | Description                                                |
| ----------------------------- | ---------------------------------------------------------- |
| **deps.py**                   | Dependencies used by endpoints (e.g., db session creation) |
| **api_v1/api.py**             | Setup main APIRouter, establish endpoint prefixes and tags |
| **api_v1/endpoints/auth.py**  | Endpoints used for authentication                          |
| **api_v1/endpoints/users.py** | Endpoints used for user related operations                 |

## *core* file tree
<pre>
└── config.py
</pre>

| File                          | Description                                                |
| ----------------------------- | ---------------------------------------------------------- |
| **config.py**                 | Creates Settings class using environment variables         |

## *db* file tree
<pre>
├── base_class.py
└── session.py
</pre>

| File                          | Description                                                               |
| ----------------------------- | ------------------------------------------------------------------------- |
| **base_class.py**             | Creates Base class used by database models                                |
| **session.py**                | Setup engine and Session class for communicating with PostgreSQL database |

## *models* file tree
*Coming soon*

## *schemas* file tree
<pre>
└── user.py
</pre>

| File                          | Description                                                               |
| ----------------------------- | ------------------------------------------------------------------------- |
| **user.py**                   | Pydantic schemas for request/response models                              |

## *tests* file tree
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