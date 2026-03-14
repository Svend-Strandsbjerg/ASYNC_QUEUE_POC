# Testing Strategy

This document defines reusable expectations for testing across projects based on this foundation.

## Testing philosophy

- Tests should reduce delivery risk and validate behavior.
- Testing quality matters more than raw coverage percentages.
- Prefer fast feedback loops with deterministic, reliable tests.

## Test layers

### Unit tests

- Required for non-trivial logic.
- Should validate core behavior, edge cases, and error paths.
- Must run quickly and independently.

### Integration tests

- Add when multiple components/services interact.
- Validate contracts, data flow, and boundary behavior.
- Focus on meaningful integration risks.

### Regression tests

- Expected for bug fixes when practical.
- Reproduce the failure condition and verify the fix.
- Prevent recurrence of known defects.

## Test quality expectations

- Avoid brittle assertions tied to irrelevant implementation details.
- Keep fixtures/factories readable and minimal.
- Use clear test names describing expected behavior.
- Remove redundant tests that do not provide additional confidence.

## AI-assisted development requirements

- AI-generated functionality changes should include or update tests.
- If tests are not added, contributors must explain why.
- AI-generated tests should be reviewed for false positives and weak assertions.

## PR testing evidence

Each PR should include:

- Which tests/checks were run
- Results (pass/fail)
- Any known gaps or environment limitations
