# Backend Directory Overview

The following summarizes the structure of the backend folder:

<pre>
.
├── alembic
│   └── versions
├── app
│   ├── api
│   │   ├── api_v1
│   │   │   ├── endpoints
│   ├── core
│   ├── crud
│   ├── db
│   ├── models
│   │   └── utils
│   ├── schemas
│   ├── seeds
│   ├── tasks
│   ├── tests
│   │   ├── api
│   │   │   └── api_v1
│   │   ├── core
│   │   ├── crud
│   │   ├── data
│   │   ├── toolbox
│   │   └── utils
│   └── utils
│       ├── AgTC
│       ├── cleanup
│       ├── toolbox
│       └── tusd
├── celery
└── potree

</pre>

| Folder          | Description                                     |
| --------------- | ----------------------------------------------- |
| **alembic**     | Database migrations                             |
| **app**         | FastAPI application                             |
| **app/api**     | Versioned API endpoints                         |
| **app/core**    | Application settings and security               |
| **app/crud**    | Basic and model specific CRUD utility functions |
| **app/db**      | Base database class and session                 |
| **app/models**  | Database models                                 |
| **app/schemas** | Pydantic schemas                                |
| **app/seeds**   | Scripts for seeding data tables                 |
| **app/tasks**   | Asynchronous Celery tasks                       |
| **app/tests**   | Tests for API endpoints                         |
| **app/utils**   | Misc utility classes and methods                |
| **celery**      | Celery service startup scripts                  |
| **potree**      | Potree library for point cloud visualization    |
