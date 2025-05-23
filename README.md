# Data To Science Engine

## Getting started

### Prerequisites

[Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) are required to run the container with the following instructions. If you can successfully run `docker --version` and `docker compose --version` from a terminal then you are ready to proceed to the next section.

### Copy env example files

1. Navigate to the root directory of the repository.
2. Copy `backend.example.env` to a new file named `backend.env`.
   ```
   cp backend.example.env backend.env
   ```
3. Copy `db.example.env` to a new file named `db.env`.
   ```
   cp db.example.env db.env
   ```
4. Copy `.env.example` to a new file named `.env`.
   ```
   cp .env.example .env
   ```
5. Copy `frontend.example.env` to a new file named `frontend.env`.
   ```
   cp frontend.example.env frontend.env
   ```
6. Copy `frontend/.env.example` to a new file named `frontend/.env`.
   ```
   cp frontend/.env.example frontend/.env
   ```
7. Copy `frontend/example.env.development` to a new file named `frontend/.env.development`.
   ```
   cp frontend/example.env.development frontend/.env.development
   ```

### Customize env files

1. Open `.env`. Below is a list of the environment variables that can be set inside `.env`.

   **Environment variables**

- `EXTERNAL_STORAGE`: Location where raw image zips and metadata will be sent for image processing jobs. It could be a mapped network drive or any other directory on the host machine. This **should be left empty** unless you have set up an image processing backend that works with the D2S image processing Celery task.
- `TUSD_STORAGE`: Location of Docker managed volume or mapped host directory that stores user uploaded datasets.
- `TILE_SIGNING_SECRET`: Secret key used for creating a signed URL that the client can use to access raster tiles and MVT tiles.

2. Open `frontend.env`. Below is a list of the environment variables that can be set inside `frontend.env`.

   **Environment variables**

- `VITE_MAPBOX_ACCESS_TOKEN`: Mapbox access token for satellite imagery (optional).

3. Open `backend.env` in a text editor. Below is a list of the environment variables that can be set inside `backend.env`. You may use the default values or change them as needed.

   If you do not assign a value to `SECRET_KEY`, a key will automatically be generated for you. Note to developers: A new key will be generated each time a change is made to the backend code. This will invalidate any JWT tokens signed with the previous key. To prevent this behavior, set a secret key in `backend.env`.

   **Environment variables**

   - `API_PROJECT_NAME`: Name that will appear in the FastAPI docs.
   - `API_DOMAIN`: Domain used for accessing the application (e.g., http://localhost or https://customdomain)
   - `CELERY_BROKER_URL`: Address for local redis service.
   - `CELERY_RESULT_BACKEND`: Address for local redis service.
   - `MAIL_ENABLED`: Enable SMTP email by changing value from 0 to 1.
   - `MAIL_SERVER`: SMTP server address.
   - `MAIL_USERNAME`: Username for SMTP server.
   - `MAIL_PASSWORD`: Password for SMTP server.
   - `MAIL_FROM`: Sender email address.
   - `MAIL_FROM_NAME`: Name of sender.
   - `MAIL_ADMINS`: List of emails that should receive admin mail separated by commas.
   - `MAIL_PORT`: SMTP server port.
   - `MAPBOX_ACCESS_TOKEN`: Mapbox access token for satellite imagery (optional).
   - `POINT_LIMIT`: Total number of points to be used when generating point cloud preview images.
   - `SECRET_KEY`: Secret key for signing and verifying JWT tokens.

4. Open `db.env` in a text editor. `POSTGRES_PASSWORD` should be assigned a secure password. The other environment variables can be left on the default values. `POSTGRES_HOST` should always be set to `db` unless the database service name is changed from `db` to another name in `docker-compose.yml`.

   If you change `POSTGRES_USER` or `POSTGRES_HOST`, you must also update these environment variables with the new values under the `db` service in `docker-compose.yml`.

5. Open `frontend/.env` in a text editor. You may use the default values or change them as needed.

   **Environment variables**

   - `VITE_API_V1_STR`: Path for API endpoints. Do not change from default value unless the path has been changed in the backend.
   - `VITE_BRAND_FULL`: Full name of application.
   - `VITE_BRAND_SHORT`: Abbreviated name of application.
   - `VITE_BRAND_SLOGAN`: Slogan that appears on landing page.
   - `VITE_TITLE`: Page title.
   - `VITE_META_DESCRIPTION`: Description for search results and browser tabs.
   - `VITE_META_OG_TITLE`: Title for social media shares.
   - `VITE_META_OG_DESCRIPTION`: Description for social media shares.
   - `VITE_META_OG_TYPE`: Content type (e.g., 'website', 'article').
   - `VITE_SHOW_CONTACT_FORM`: Boolean (0 or 1) to indicate if Contact Form link should be shown (requires email service).

6. Open `frontend/.env.development` in a text editor. You may use the default values or change them as needed.

   Environment variables:

   - `VITE_META_OG_IMAGE`: Preview image URL for social media shares.
   - `VITE_META_OG_URL`: Hostname for site.

### Build Docker images for services

1. In the root repository directory where `docker-compose.example.yml` is located. Copy it to a new file named `docker-compose.yml`.

   ```
   cp docker-compose.example.yml docker-compose.yml
   ```

2. Build Docker images for the frontend, backend, and proxy services with the following command:
   ```
   docker compose build
   ```

### Start the containers

1. Use the following command to run the service containers in the background:
   ```
   docker compose up -d
   ```

### Stop the containers

1. Use the following command to stop the containers:
   ```
   docker compose stop
   ```

### Accessing the web application

The Data To Science web application can be accessed from `http://localhost:8000`. Replace `localhost` with the `DOMAIN` environment variable if it was changed to a different value. If port `8000` is already use, or you want to use a different port, change the port in `docker-compose.yml` under the `proxy` service's `ports` setting.

# Additional information

The above sections should provide all the necessary steps to get Data To Science up and running. These next sections provide additional information about using `docker-compose-dev.yml` for development, accessing the FastAPI documentation, and running the backend tests.

## Accessing the API

After running `docker compose up -d`, you should be able to access the web API from [http://localhost:8000/docs](http://localhost:8000/docs) or [http://localhost:8000/redoc](http://localhost:8000/redoc). The first URL will display the Swagger UI documentation for the API and the second URL will display the ReDoc documentation. The API endpoints can be tried out from either URL.

## Running backend tests

The `pytest` library can be used to run tests for the FastAPI backend. Use the following command to run the full test suite:

```
docker compose exec backend pytest
```

## Database migrations with Alembic

If you make any changes the database models, run the following command to create a new migration:

```
docker compose exec backend alembic revision --autogenerate -m "migration comment"
```

After creating the new migration, use the following command to update to the tables in the database:

```
docker compose exec backend alembic upgrade head
```
