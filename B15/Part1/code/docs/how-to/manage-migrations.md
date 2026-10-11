# Manage Database Migrations

D2S uses [Alembic](https://alembic.sqlalchemy.org/) to manage database schema changes. This guide covers creating and applying migrations.

## Apply existing migrations

After pulling new changes or on first setup, apply all pending migrations:

```bash
docker compose exec backend alembic upgrade head
```

## Create a new migration

After modifying SQLAlchemy models, auto-generate a migration:

```bash
docker compose exec backend alembic revision --autogenerate -m "describe the change"
```

Review the generated migration file in `backend/alembic/versions/` before applying it. Auto-generated migrations may need manual adjustments for complex changes.

## Apply the new migration

```bash
docker compose exec backend alembic upgrade head
```

## Check current migration status

```bash
docker compose exec backend alembic current
```

## Downgrade a migration

To revert the most recent migration:

```bash
docker compose exec backend alembic downgrade -1
```
