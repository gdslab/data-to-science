# Contributing to Data to Science (D2S)

Contributions, feedback, and discussion are welcome.

## Getting Help

- **Found a bug?** Open an [issue](https://github.com/gdslab/data-to-science/issues)
- **Have an idea or feature request?** Start a [discussion](https://github.com/gdslab/data-to-science/discussions) for exploratory ideas, or open an [issue](https://github.com/gdslab/data-to-science/issues) for concrete, actionable requests
- **Have a question?** Open a [discussion](https://github.com/gdslab/data-to-science/discussions)
- **Found a security vulnerability?** Do not open a public issue. Follow [SECURITY.md](SECURITY.md).

When reporting a bug, please include:

- A brief description of the problem
- Steps to reproduce it
- Expected and observed behavior
- Relevant logs, screenshots, or configuration details

Everyone participating in this project is expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## AI Use Policy

You may use AI tools to assist your contributions. You are fully responsible for everything you submit.

> **Policy:** This project requires a human in the loop. You are the author and are accountable for all submitted code. Review all tool-generated content thoroughly before submitting it.

This policy is consistent with the [JOSS AI usage policy](https://joss.readthedocs.io/en/latest/policies.html#ai-usage-policy), which this project follows.

### Guidelines

Contributors using AI tools must:

- **Test all code thoroughly.** Submit only code you have verified works.
- **Understand your contributions.** You must be able to explain every change you submit.
- **Make the design decisions yourself.** AI tools may help implement a design; they should not choose it.
- **Write issues and PR descriptions in your own words.**
- **Disclose AI assistance** with an `Assisted-by` commit trailer (see [Commit Messages](#commit-messages)) and in the PR template.
- **Take responsibility** for code quality, correctness, and follow-up if review finds problems.

*__Note:__ AI-generated code submitted with little thought behind it isn't much help. Maintainers can generate a fix themselves, often faster than reviewing yours. If that's where you are, open an issue instead.*

### Unacceptable Submissions

Pull requests and issues may be closed without review if they contain:

- Untested code or failing checks
- Verbose AI-generated descriptions
- Evidence the contributor doesn't understand the submission

Using AI to learn and develop is encouraged. Using it to bypass understanding is not.

## Development Environment

The whole project runs through Docker Compose. You do not need Python or Node installed on your machine. [uv](https://docs.astral.sh/uv/) is needed only if you change backend Python dependencies.

The first run copies the example environment and compose files, pulls the geospatial base image, and builds the service images:

```bash
git clone https://github.com/gdslab/data-to-science
cd data-to-science
cp backend.example.env backend.env
cp db.example.env db.env
cp .env.example .env
cp frontend.example.env frontend.env
cp frontend/.env.example frontend/.env
cp frontend/example.env.development frontend/.env.development
cp docker-compose.example.yml docker-compose.yml
docker pull gdslab/d2s-geo-base:latest
docker compose build
docker compose up -d
```

The web application is then available at `http://localhost:8000`. The [Local Development Setup](https://gdslab.github.io/data-to-science/how-to/local-development/) guide explains each step, the environment variables, and how dependencies are locked.

If you change a dependency manifest, a lockfile, or a container definition, rebuild the affected service:

```bash
docker compose up -d --build <service>
```

## Contributing Code

If you plan a significant change, open an issue or discussion first to coordinate and avoid duplicated effort.

### Before Opening a PR

Run the checks for the part of the codebase you changed. If you changed a shared contract (routes, request/response shapes, status codes, schema), run every affected suite.

```bash
# Backend
docker compose exec backend ruff check .
docker compose exec backend ruff format --check .
docker compose exec backend pytest

# Frontend
docker compose exec frontend npx tsc --noEmit
docker compose exec frontend yarn lint
```

CI runs the backend checks on every pull request, and they must pass before it can merge. The frontend checks are not yet enforced by CI, so please run them yourself. `yarn lint` currently reports findings that predate this guide; a change must not add to them. `ruff check --fix .` and `ruff format .` apply what the first two backend commands report.

New behavior needs a test. Bug fixes need a test that fails without the fix. The frontend has no automated test suite, so frontend changes that touch interactive flows document manual QA steps (URL, steps, expected result) in the pull request instead.

### Commit Messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

```
<type>(<scope>): <what changed and why>

[optional body: constraints, tradeoffs, or non-obvious context]

[optional trailer: Assisted-by: <tool> (<model>)]
```

- **Types:** `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `ci`
- **Scopes:** `api` (backend service and Celery tasks), `web` (frontend), `db` (models and migrations), `admin` (the `d2s_admin` CLI), `infra` (compose files, nginx, varnish, tusd), `ci`, `docs`, `deps`

Keep one logical change per commit. The message should explain *why*, not just *what*.

If an AI tool helped write the code in a commit, add an `Assisted-by` trailer naming the tool and model, for example `Assisted-by: Claude Code (Claude Fable 5.1)`. Do not include `Claude-Session` trailers or links to agent sessions: they mean nothing to collaborators who do not use the same tool.

### Pull Requests

Fork the repository, create a feature branch, and open a pull request against the `main` branch of [gdslab/data-to-science](https://github.com/gdslab/data-to-science).

**Title:** Use the Conventional Commits format, for example `fix(api): return 404 for a missing flight instead of 500`. A CI check validates the title. Pull requests are merged with a merge commit, so every commit on the branch keeps its own message; write each one in the same format.

**Description:** GitHub pre-fills new pull requests with a template. Complete the relevant sections and the checklist. Sections marked optional may be deleted when they don't apply.

Please call out any database migrations or new environment variables so reviewers can update their local setup, and include screenshots for UI changes.

Pull requests opened before this convention used a `[Type]` prefix in the title. For reading older history: `[Bug]` is `fix`, `[Feature]` and `[Enhancement]` are `feat`, `[Docs]` is `docs`, and `[Chore]` is `chore`.
