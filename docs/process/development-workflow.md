# Development Workflow

This workflow defines how work moves from request to merge in repositories using this foundation.

## 1) Intake and scope

- Start from an issue, request, or task.
- Clarify scope, constraints, and acceptance criteria.
- Identify testing and documentation implications before coding.

## 2) Branch creation

- Create a branch from `main`.
- Use a descriptive branch name tied to the task intent.
- Avoid mixing unrelated work in a single branch.

## 3) Implementation

- Make focused, incremental commits.
- Keep changes aligned to accepted scope.
- Prefer readability and maintainability over clever shortcuts.

## 4) Validation

- Run relevant tests and checks.
- Add/update tests for behavior changes and bug fixes.
- Confirm documentation updates are included where needed.

## 5) Pull request

- Open a PR using the repository template.
- Provide clear summary, testing evidence, and risk/assumption notes.
- Ensure PR remains reviewable in size and scope.

## 6) Review and iteration

- Address reviewer feedback in follow-up commits.
- Re-run checks after substantial updates.
- Resolve open questions before merge.

## 7) Merge

- Merge only after required approvals and green checks.
- Prefer merge strategies consistent with team policy.
- Delete merged branches to keep repository hygiene.
