# AGENTS.md

Executable reference for AI agents working in this repo. Follow these rules literally.

> This file is the single source of agent instructions. `CLAUDE.md` contains only `@AGENTS.md`; add new rules here, never there. Keep entries short and actionable: conventions to follow and traps to avoid. For anything longer, link to the existing doc instead of copying it in.

---

## 1. Project Layout

```
backend/                FastAPI service, Celery tasks, Alembic migrations, pytest suite (app/tests)
frontend/               React + TypeScript web application built with Vite
d2s_admin/              Python CLI (standard library only) for the quickstart stack and admin tasks
docs/                   mkdocs-material site in Diátaxis layout, plus the JOSS paper
nginx/ varnish/ tusd/   Reverse proxy, tile cache, and resumable-upload services for the compose stacks
.github/                CI workflows, issue forms, pull request template
docker-compose*.yml     Stack definitions: development, quickstart, production
```

- `backend/` and `frontend/` are independent except for the HTTP API contract: routes under `backend/app/api/api_v1`, Pydantic schemas in `backend/app/schemas`, consumed from `frontend/src`. A change to one side does not require touching the other unless that contract changes.
- If a shared contract changes (request/response shape, route, status code, schema), update every side of it and its tests in the same change.
- Tile URL signing is shared between the backend and the `varnish/` configuration. Change both together.
- `d2s_admin/` depends on nothing else and nothing depends on it.

---

## 2. Commands

Everything runs through Docker Compose from the repo root. Do not run language tools directly on the host. Do not invent alternatives.

| Task | Command |
|---|---|
| Start stack (development, builds from source) | `docker compose up -d` |
| Start stack (quickstart, prebuilt images) | `python3 -m d2s_admin quickstart up` |
| Backend lint + format check | `docker compose exec backend ruff check .` then `docker compose exec backend ruff format --check .` |
| Backend lint + format fix | `docker compose exec backend ruff check --fix .` then `docker compose exec backend ruff format .` |
| Backend test | `docker compose exec backend pytest` |
| Backend migrations | `docker compose exec backend alembic upgrade head` |
| Frontend type check | `docker compose exec frontend npx tsc --noEmit` |
| Frontend lint | `docker compose exec frontend yarn lint` |

The frontend has no automated test suite. `yarn lint` reports findings that predate this file on `main`; the bar is no new findings in the files you touched, not a clean run.

### Dependency updates

The images and CI install from the lockfiles, so regenerate them after editing a dependency manifest:

```sh
# Backend: edit backend/pyproject.toml, then (uv on the host)
cd backend && uv lock
# Frontend: edit from inside the container so yarn.lock matches its yarn
docker compose exec frontend yarn add <package>
```

Commit the manifest and the lockfile together. The backend image is built with `uv sync --locked`, which fails when `uv.lock` no longer matches `pyproject.toml`. `uv lock` resolves against the `exclude-newer` timestamp in `[tool.uv]`, so it changes only the packages you touched; moving that timestamp is its own change. See [Backend dependencies](docs/how-to/local-development.md#backend-dependencies).

### Traps

- After changing a dependency manifest, lockfile, or dockerfile, rebuild the affected service: `docker compose up -d --build <service>`. Without it, the container keeps running the old dependencies.
- `./backend` and `./frontend` are bind-mounted into their containers; everything else (compose files, `nginx/`, `varnish/`, env files) needs a rebuild or restart to take effect.
- Never run `docker compose down -v` or delete `tusd-data/`. They destroy the database and uploaded data.
- `gdslab/d2s-geo-base:latest` is a mutable tag. Pull it before building the backend image, or an old local copy is used silently.
- If a check fails because a service isn't running, start the stack. Do not fall back to running the check on the host: ruff is pinned to an exact version in `backend/pyproject.toml`, and the GDAL/PDAL bindings exist only inside the image.
- pytest runs with `-n auto` (xdist), one database per worker. Tests must not depend on each other or on fixed row ids.
- Suites gated by `ENABLE_STAC`, `ENABLE_CAMPAIGNS`, `ENABLE_IFORESTER`, `ENABLE_BREEDBASE`, and `MAIL_ENABLED` are skipped when the flag is off, including in CI. Enable the flag locally to run them.
- A production host must pin its own config: `docker compose -f docker-compose.prod.yml` with its env files. Otherwise the development overrides load too, with their bind mounts and host ports.

### Shell and file access

- Read files with the Read tool (use line ranges for large files), not `cat`/`sed`/`head`/`tail` in Bash. This includes command output you need to inspect (JSON, logs, screenshots); don't write a script to parse it.
- Search with the Grep and Glob tools, not `grep`/`find`/`ls` in Bash.
- Make file changes with the Edit or Write tools, not Python, `sed -i`, heredocs, or other scripts.
- In Bash commands, write paths out literally as absolute paths. Don't `cd` first, and don't store paths in shell variables (e.g. `W=... && $W/...`).
- Never pass code to a program through a heredoc, stdin, or an inline flag (`python3 -`, `node -e`, `bash -c`, `<<EOF`), including the project's own scripts. Write it to a file in `.scratch/` (gitignored) with the Write tool and pass the path. A written file is shown for review and its command can match an allow rule; inline code gets neither, so it triggers a prompt.
- For multi-line commit messages, write the message to a file and run `git commit -F <path>`.
- Keep each Bash call to one simple command or a short `&&` chain; avoid subshells and `$(...)` where a literal value works.

---

## 3. Making Changes

**Touch only what the request requires.** For every file you modify, ask: "Did the request mention this file, or does this change directly cause a required change here?" If neither, don't touch it.

- Do not refactor adjacent code.
- Do not add dependencies without asking first (see Section 7).
- Do not add error handling for scenarios the request didn't raise.
- Do match the style (naming, structure, comment style) of surrounding code exactly.
- Comments record what the code cannot say: a constraint, a unit, a non-obvious reason. Do not restate the line.
- Do remove imports, variables, or functions that *your* changes made unused.
- Prefer small, reviewable changes. If a request would produce a large diff, propose splitting it before starting.

### Architecture conventions

- **Backend layers point inward.** Routes in `app/api/api_v1` call `app/crud`; `crud` works on `app/models` and `app/schemas`; `app/core` holds config and security; `app/tasks` holds Celery tasks; `app/utils` holds helpers with no HTTP or database knowledge. `crud`, `models`, and `utils` never import from `api`.
- **Validated, typed models for every boundary.** Every request body, response, and task payload is a Pydantic schema in `app/schemas`. Do not pass raw dicts across a boundary.
- **Shared concerns go through FastAPI dependencies** in `app/api/deps.py` (database session, current user, permissions), not globals or per-route re-implementations.
- **Don't create a file or folder until there's code for it.** A service layer is added when there is logic worth separating from the route, not for symmetry.
- **Name files by what they do.** Never two modules with the same name in different packages.
- Type annotations on all function signatures.

### Backend conventions

- Python is formatted and linted by `ruff`, pinned to an exact version in `backend/pyproject.toml` (the `[tool.ruff]` tables there are the configuration), with 4-space indents, an 88 column line length, and type hints checked by `mypy`. Do not use `black`; it is not installed, and CI runs `ruff format --check`.
- Imports follow PEP 8: standard library, third-party, then local application imports, one blank line between groups, sorted alphabetically within each (ruff's `I` rules enforce this). Keep imports at the top of the file. No wildcard imports. Prefer absolute imports; use relative imports only when it improves local package clarity. Use `if TYPE_CHECKING:` for type-only imports when needed.
- Naming: snake_case for modules and functions, PascalCase for SQLAlchemy models and Pydantic schemas, explicit imports.
- Route notes go in the endpoint's docstring, never as a `#` comment above the decorator.

### Frontend conventions

- TypeScript relies on ESLint with strict TS configs. Components are PascalCase, hooks are camelCase, and files are organized by feature under `frontend/src/`.
- Avoid committing generated assets from `public/` or compiled bundles.

---

## 4. Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <what changed and why>

[optional body: constraints, tradeoffs, or non-obvious context]
```

Valid types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `ci`

Scope = the architectural boundary from Section 1: `api` (backend service and Celery tasks), `web` (frontend), `db` (models and migrations), `admin` (the `d2s_admin` CLI), `infra` (compose files, nginx, varnish, tusd), `ci`, `docs`, `deps`

The message must explain *why*, not just *what*. "Update main.py" is not acceptable.

One logical change per commit. Do not bundle unrelated changes. Group backend and frontend changes into separate commits when possible.

History before this convention used imperative titles with no prefix, and pull request titles carried a `[Type]` tag. For reading it: `[Bug]` is `fix`, `[Feature]` and `[Enhancement]` are `feat`, `[Docs]` is `docs`, and `[Chore]` is `chore`.

### Pull Requests

`.github/PULL_REQUEST_TEMPLATE.md` is the source of truth for pull request structure. It pre-fills the description on GitHub. Fill in its sections rather than composing your own: delete the ones it marks optional when they do not apply, keep its Checklist, and do not tick a box you have not verified.

- The title follows Conventional Commits, same as the commits. `.github/workflows/pr-title.yml` checks it.
- Pull requests merge with a merge commit, so every commit on the branch lands on `main` with its own message. There is no squash to clean them up afterwards.
- Group the Changes bullets by area, adding areas beyond the four it lists (`CI`, `Docs`) when a change touches them. Nest sub-bullets under an area when one line cannot carry it.
- Testing wants commands and their actual results, plus manual QA steps as a URL and the steps to follow. "All passing" without the command is not proof.

---

## 5. Testing

| Changed | Must run |
|---|---|
| `backend/` only | Backend lint + format check, backend test |
| `frontend/` only | Frontend type check, frontend lint |
| Shared contract | Every affected suite |

- New behavior needs a test. Bug fixes need a test that fails without the fix.
- Favor focused pytest modules named `test_<feature>.py` in the matching folder under `backend/app/tests`. Add regression tests whenever modifying CRUD logic or API endpoints.
- Mark optional integrations with the existing `pytest_requires_*` decorators and document any env toggles needed.
- Every new test function has a docstring, even one sentence stating what is tested.
- Frontend changes that touch interactive flows document manual QA steps (URL + steps) in the pull request.
- Do not delete or weaken existing tests to make a change pass.

---

## 6. Pre-Submission Checklist

Do not report a task complete until every item is concretely true, not self-assessed.

- [ ] I can name every file I changed and the reason for each change
- [ ] Every changed line traces directly to the request — nothing extra
- [ ] The correct checks from Section 5 ran and passed
- [ ] Commit message follows Conventional Commits and explains intent
- [ ] Security checked: no secrets in code, no unvalidated input reaching queries or the filesystem, no auth checks bypassed
- [ ] Commit includes the `Assisted-by` trailer (Section 7)
- [ ] Human in the loop: the diff is presented for the author's review, and nothing was committed without their go-ahead (Section 7)

---

## 7. AI Usage

This project follows the [JOSS AI usage policy](https://joss.readthedocs.io/en/latest/policies.html#ai-usage-policy). Contributor-facing policy: [CONTRIBUTING.md](CONTRIBUTING.md#ai-use-policy).

- The human author makes architectural and design decisions. If a request needs one that hasn't been made (new dependency, new data model, change to project structure), stop and ask. Do not choose.
- Every AI-assisted commit ends with the trailer `Assisted-by: <tool> (<model>)`, e.g. `Assisted-by: Claude Code (Claude Fable 5.1)`. Do not add `Claude-Session` trailers or session links to commits or pull request descriptions.
- If the *why* for a commit message isn't clear from the request, ask. Do not invent a rationale.
- The author reviews every change before it is committed. Present the diff and wait; do not commit unprompted.
