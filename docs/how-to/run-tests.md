# Run the Test Suite

This guide explains how to run backend tests for D2S.

## Run all tests

With the containers running, execute the full pytest suite:

```bash
docker compose exec backend pytest
```

## Run a specific test file

```bash
docker compose exec backend pytest app/tests/api/api_v1/test_projects.py
```

## Run tests with verbose output

```bash
docker compose exec backend pytest -v
```

## Run tests matching a keyword

```bash
docker compose exec backend pytest -k "test_create_project"
```
