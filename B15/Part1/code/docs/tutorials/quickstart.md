# Getting Started

This tutorial walks you through setting up a local D2S instance using Docker. By the end, you will have a running D2S platform accessible in your browser.

## Prerequisites

You need the following installed on your machine:

- [Python 3](https://www.python.org/) (standard library only — no additional packages required)
- [Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/)

Verify your setup:

```bash
python3 --version
docker --version
docker compose --version
```

!!! note "Platform support"
    D2S containers target the `linux/x86_64` architecture. If you are running Docker Desktop on Apple Silicon (ARM), emulation is handled automatically, but you may notice slower build times and startup.

## Step 1: Initialize the environment

From the root directory of the repository, run:

```bash
python3 -m d2s_admin quickstart init
```

This copies the example environment files and creates the `tusd-data/` upload directory.

## Step 2: Start the services

```bash
python3 -m d2s_admin quickstart up
```

This starts all service containers in the background. It may take up to a minute for the backend to finish initializing.

## Step 3: Create a superuser account

Once the containers are running, create an admin account:

```bash
python3 -m d2s_admin createsuperuser
```

You will be prompted for an email, first name, last name, and password. You can also pass these as flags:

```bash
python3 -m d2s_admin createsuperuser \
  --email admin@example.com \
  --first-name Admin \
  --last-name User \
  --password yourpassword
```

## Step 4: Access D2S

Open your browser and navigate to [http://localhost:8000](http://localhost:8000). Log in with the superuser credentials you just created.

## Stopping D2S

When you're done, stop the containers:

```bash
python3 -m d2s_admin quickstart down
```

## Next steps

- [User Manual](https://docs.gdsl.org/data-to-science-user-manual/) — Learn how to create projects, upload data, and explore visualizations
- [Configuration](../reference/configuration.md) — Customize environment variables for your deployment
