# Observer Pattern — Test Cases

## Common Specification
- Input: job name (string)
- Events fired: STARTED, PROCESSING, DONE (in order)
- Logger prints all 3 events
- Notifier only prints on DONE

## Test Cases
| ID | Description | Expected Logger Output | Expected Notifier Output | Java | Python | JS | C++ |
|----|-------------|----------------------|--------------------------|------|--------|----|-----|
| TC1 | Run job | 3 log lines | 1 notify line | PASS | PASS | PASS | PASS |
| TC2 | Multiple observers | Both receive all events | Both respond correctly | PASS | PASS | PASS | PASS |
| TC3 | No observers | No output, no crash | -- | PASS | PASS | PASS | PASS |
