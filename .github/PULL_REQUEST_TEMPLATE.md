<!--
Thank you for contributing to Data to Science (D2S)!

PR title format: [Type] Brief description in sentence case
Types: [Feature] [Enhancement] [Bug] [Refactor] [Docs] [Test] [Chore]
Example: [Bug] Fix point cloud upload succeeding with empty COPC output

Sections marked (optional) may be deleted when not applicable.
-->

## Summary

<!-- 1-3 sentences: what changed and why. Focus on user/developer impact. -->

## Changes

<!-- Bulleted list grouped by area; delete groups that don't apply.
     For bug fixes, a brief root-cause note here is welcome. -->

- Backend:
- Frontend:
- Database:
- Config:

## Testing

<!-- Commands run + results, and manual QA steps (URL, steps, expected result), e.g.:
- `docker compose exec backend pytest` — all passing
- `docker compose exec frontend npx tsc --noEmit` — no errors -->

## Screenshots (optional)

<!-- Required for UI changes: before/after images or a short demo. -->

## Breaking Changes (optional)

<!-- Migrations to run, new environment variables, rebuild requirements. -->

## Related Issues

<!-- Closes #123 / Related to #456 — or state that no tracking issue exists. -->

## Checklist

- [ ] Backend tests pass: `docker compose exec backend pytest`
- [ ] Backend lint passes: `docker compose exec backend ruff check . && docker compose exec backend ruff format --check .`
- [ ] TypeScript check passes: `docker compose exec frontend npx tsc --noEmit`
- [ ] I have self-reviewed the diff
- [ ] Documentation (docs/, README) is updated, or no updates are needed
- [ ] Schema/migration changes are called out above, or there are none
