# PS2 API

## Getting started
### Prerequisites
[Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) are required to run the container with the following instructions. If you can successfully run `docker --version` and `docker compose --version` from a terminal then you are ready to proceed to the next section.
### Build the container image (can be skipped)
1. In your terminal, navigate to the root directory for this repo. You should be at the same level as `Dockerfile` and `docker-compose.yml`.
2. Build the container image with the following command:
    ```
    docker compose build
    ```
It is not necessary to explicitly run the build command. The image described in the `Dockerfile` will automatically be built when `docker compose up` is run (see the next section).
### Start the container in detached mode
1. Use the following command to start a container with the built image and run it in the background:
    ```
    docker compose up -d
    ```
    Note, the above command will only build the container image if it does not already exist. If you have made changes to the Dockerfile and previously built the container image, the following command will rebuild the image and start the container:
    ```
    docker compose up --build -d
    ```
### Stop the container
1. Use the following command to stop the container:
    ```
    docker compose stop
    ```
## Accessing the API
After running `docker compose up -d`, you should be able to access the web API from [http://127.0.0.1/docs](http://127.0.1/docs) or [http://127.0.0.1/redoc](http://127.0.0.1/redoc). The first URL will display the Swagger UI documentation for the API and the second URL will display the ReDoc documentation. The API endpoints can be tried out from either URL.
## Running the API tests
The `pytest` library can be used to run the API tests. Use the following command to start a test session:
```
docker compose exec api pytest
```