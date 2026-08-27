# Contributing to Data to Science (D2S)

We welcome contributions, feedback, and discussion from the community.

## Reporting Bugs

If you encounter a bug or unexpected behavior, please open an issue on GitHub:

- https://github.com/gdslab/data-to-science/issues

When possible, include:

- A brief description of the problem
- Steps to reproduce the issue
- Expected and observed behavior
- Relevant logs, screenshots, or configuration details

## Suggesting Features and Enhancements

Feature requests and ideas for improvements are welcome. Please start a discussion or open an issue on GitHub:

- Discussions: https://github.com/gdslab/data-to-science/discussions
- Issues: https://github.com/gdslab/data-to-science/issues

Discussions are recommended for exploratory ideas or questions, while issues are best for concrete, actionable feature requests.

## Asking Questions and Starting Conversations

General questions, use-case discussions, and design conversations can be started in GitHub Discussions:

- https://github.com/gdslab/data-to-science/discussions

## Contributing Code

We welcome code contributions. If you plan to make a significant change, we recommend opening an issue or discussion first to coordinate and avoid duplicated effort.

## Pull Requests

To contribute code, fork the repository, create a feature branch, and open a pull request against the `main` branch of [gdslab/data-to-science](https://github.com/gdslab/data-to-science).

**Title format:** `[Type] Brief description in sentence case`, where type is one of `[Feature]`, `[Enhancement]`, `[Bug]`, `[Refactor]`, `[Docs]`, `[Test]`, or `[Chore]`. For example: `[Bug] Fix point cloud upload succeeding with empty COPC output`.

**Description:** GitHub pre-fills new pull requests with our template. Please complete the relevant sections and the checklist; sections marked optional may be deleted when they do not apply.

**Before opening a PR**, run these checks locally:

```bash
docker compose exec backend pytest
docker compose exec backend ruff check .
docker compose exec backend ruff format --check .
docker compose exec frontend npx tsc --noEmit
```

The first three run again on every pull request and must pass before it can be
merged. The TypeScript check is not yet enforced by CI, so please run it yourself.

Ruff replaces black, flake8 and isort; `ruff check --fix .` and `ruff format .`
apply what the first two report. See
[Local Development Setup](https://gdslab.github.io/data-to-science/how-to/local-development/)
for details.

Please also mention any schema or migration changes in the PR description so reviewers can rebuild their local containers, and include screenshots for UI changes.
