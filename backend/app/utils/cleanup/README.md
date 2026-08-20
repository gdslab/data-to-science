# Cleanup utilities

Permanently removes data that has been soft deleted, along with the static files
that belong to it. Deleting a project, flight, data product, or raw data in the
web app only deactivates it: the record stays in the database with
`is_active = false` and a `deactivated_at` timestamp, and its files stay on disk.
This script is what finally removes both.

Records are kept for **two weeks** after deactivation (`RETENTION_WEEKS` in
`common.py`) so an accidental deletion can still be reversed by an administrator
before the files are gone.

Nothing runs this script automatically. It is run by hand from the backend
container.

## Running it

Always start with a dry run. `--check-only` reports what would be removed
without touching a single file or record:

```bash
docker compose exec backend python -m app.utils.cleanup.cleanup_main --check-only
```

Then run it for real:

```bash
docker compose exec backend python -m app.utils.cleanup.cleanup_main
```

Both print one line per category plus the total space involved, and log one line
per record removed so a run leaves an audit trail:

```
Projects removed: 2 (154.30 MB)
Flights removed: 1 (12.00 MB), skipped: 1
Data products and raw data removed: 4 (88.10 MB)
Stale jobs removed: 3 (5.20 MB)
Space freed up: 259.60 MB
```

A dry run and the real run that follows it report the same totals, so the
`--check-only` output is a reliable preview. A record more than one category
can see — a deactivated data product that also has a stale upload job, say — is
counted by the first category that covers it and by no other, in both modes.

Individual categories can be skipped:

| Flag                                 | Effect                                              |
| ------------------------------------ | --------------------------------------------------- |
| `--check-only`                       | Report only, remove nothing                          |
| `--skip-projects`                    | Leave deactivated projects alone                     |
| `--skip-flights`                     | Leave deactivated flights alone                      |
| `--skip-data-products-and-raw-data`  | Leave deactivated data products and raw data alone   |
| `--skip-stale-jobs`                  | Leave stale upload jobs alone                        |

The script exits non-zero if a record could not be removed. A failed record is
logged and the run continues, so one bad record does not stop the rest.

## What each category removes

**Projects** (`cleanup_projects.py`) — projects deactivated more than two weeks
ago. Removing a project removes `static/projects/<project_id>/` and, through
database cascades, its flights, data products, and raw data.

**Flights** (`cleanup_flights.py`) — flights deactivated more than two weeks ago.
Removing a flight removes its directory and cascades to its data products and
raw data.

**Data products and raw data** (`cleanup_data_products_and_raw_data.py`) —
individually deactivated data products and raw data, and their directories.

**Stale jobs** (`cleanup_stale_jobs.py`) — `upload-data-product` and
`upload-raw-data` jobs started more than two weeks ago that never finished
successfully, either because they are still stuck in `PENDING`/`STARTED` or
because they ended as `FAILED`. The partial data product or raw data the upload
created is removed with the job, which is what frees the disk space; the job
record is removed by the database cascade. A stale job whose upload record is
already gone is removed on its own.

Deactivating a project cascades to its flights and data products, so the same
files can be visible to more than one category. Each record is only counted and
removed once per run.

That deduplication is `cleanup_main.run`'s job: it passes what each category
removed to the categories after it. The category functions do not do it for
themselves, so calling one directly (as the tests do) and adding up the results
by hand counts a flight's files again under its project. Go through `run` for
any total that has to be accurate.

## What it refuses to remove

Cleanup is destructive and cannot be undone, so it leaves anything that still
looks in use. Skipped records are counted in the report and logged with the
reason.

- **Every project that still has a copy of anything in S3** (a non-null
  `s3_url` on any of its data products or raw data). The database row is the
  only record of the S3 object, so removing it would leave the object behind
  with nothing pointing at it. This normally cannot happen — the `deactivate`
  methods in `app/crud` refuse a project, flight, data product, or raw data
  while its project is published in a STAC catalog, and unpublishing deletes
  the S3 objects and clears `s3_url` — but an unpublish that fails part way
  through deliberately keeps `s3_url` set so it can be retried. Unpublish the
  project first, then run cleanup.

  The hold covers the whole project, not only the records holding an `s3_url`.
  The point of keeping the project is that the deletion can still be reversed
  once the unpublish succeeds, and that is only true while the flights and data
  inside it are still there.
- **Data that finished processing** (`is_initial_processing_completed`) or that
  has a successful job, when a stale upload job points at it. A stale upload job
  is not on its own evidence that the data is unusable.

## Adding it to a schedule

There is no Celery beat entry for this yet. Validate it by hand first — a dry
run, then a real run — before adding one alongside the entries in
`app/tasks/admin_tasks.py`.

## Known gaps

These are not cleaned up by this script:

- The `locations` row belonging to a removed project.
- Vector layers scoped to a flight, and their `.fgb` files, when the flight is
  removed but its project is not. `vector_layers.is_active` is never acted on at
  all.
- Indoor projects and indoor project data.
- Job records other than the two upload job names. They hold no files, so they
  cost database rows rather than disk space.

## Tests

`app/tests/utils/test_cleanup.py`:

```bash
docker compose exec backend pytest app/tests/utils/test_cleanup.py
```
