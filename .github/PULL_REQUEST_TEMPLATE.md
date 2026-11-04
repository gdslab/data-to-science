<!--
Thank you for contributing to Data to Science (D2S)!

PR title follows Conventional Commits, the same format as every commit on the branch:
  type(scope): what changed and why
Types and scopes are listed in AGENTS.md Section 4 and CONTRIBUTING.md.
Example: fix(api): reject uploads that produce empty COPC output

Sections marked (optional) may be deleted when not applicable.
-->

## Summary

<!-- 1-3 sentences: what changed and why. Focus on user/developer impact. -->

## Changes

<!-- Bulleted list grouped by area; delete groups that don't apply and add
     others (CI, Docs) when a change touches them.
     For bug fixes, a brief root-cause note here is welcome. -->

- Backend:
- Frontend:
- Database:
- Config:

## Testing

<!-- Commands run + results, and manual QA steps (URL, steps, expected result), e.g.:
- `docker compose exec backend pytest` — all passing
- `docker compose exec frontend npx tsc --noEmit` — no errors -->

## AI Assistance

<!-- Tools that helped write this change and how you verified the result, or "None". -->

## Screenshots (optional)

<!-- Required for UI changes: before/after images or a short demo. -->

## Breaking Changes (optional)

<!-- Migrations to run, new environment variables, rebuild requirements. -->

## Related Issues

<!-- Closes #123 / Related to #456 — or state that no tracking issue exists. -->

## Checklist

- [ ] Backend tests pass: `docker compose exec backend pytest`
- [ ] Backend lint passes: `docker compose exec backend ruff check . && docker compose exec backend ruff format --check .`
- [ ] Frontend type check passes: `docker compose exec frontend npx tsc --noEmit`
- [ ] Frontend lint adds no new findings: `docker compose exec frontend yarn lint`
- [ ] I have self-reviewed the diff
- [ ] I can explain every change in this pull request
- [ ] Documentation (docs/, README) is updated, or no updates are needed
- [ ] Schema/migration changes are called out above, or there are none
- [ ] AI-assisted commits carry the `Assisted-by` trailer, or no AI assistance was used
