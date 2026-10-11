# Strategy Pattern — Test Cases

## Common Specification
- Input: user (string), resource (string)
- Rules:
  - OwnerPolicy: resource must start with "user:"
  - RolePolicy("admin"): user's role must equal "admin"
- Error case: unknown user treated as "viewer" (denied by RolePolicy)

## Test Cases
| ID | Policy | User | Resource | Expected | Java | Python | JS | C++ |
|----|--------|------|----------|----------|------|--------|----|-----|
| TC1 | Owner | alice | alice:dataset1 | ALLOW | PASS | PASS | PASS | PASS |
| TC2 | Owner | bob | alice:dataset1 | DENY | PASS | PASS | PASS | PASS |
| TC3 | Role(admin) | alice | any | ALLOW | PASS | PASS | PASS | PASS |
| TC4 | Role(admin) | bob | any | DENY | PASS | PASS | PASS | PASS |
| TC5 | Role(admin) | unknown | any | DENY | PASS | PASS | PASS | PASS |
