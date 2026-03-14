# Contributing Guide

Thanks for contributing to this repository foundation.

This guide applies to both human contributors and AI agents.

## Contribution model

- All work is done in branches.
- All changes are submitted through pull requests.
- Direct commits to `main` are not allowed.

## Getting started

1. Read `README.md`, `ARCHITECTURE.md`, and `AGENTS.md`.
2. Confirm task scope and acceptance criteria.
3. Create a branch from `main`.
4. Make focused, reviewable changes.
5. Run relevant checks/tests.
6. Open a PR using `.github/pull_request_template.md`.

## What good contributions look like

- Clear problem statement and scope boundaries
- Minimal, maintainable implementation
- Tests that validate behavior and prevent regressions
- Documentation updates when process/behavior/structure changes
- Transparent assumptions and risk notes

## Pull request requirements

PRs should include:

- Summary of changes
- Problem being solved
- Testing evidence
- Documentation updates
- Risks and assumptions

Use the checklist in the PR template before requesting review.

## AI-assisted contribution expectations

When using AI agents/tools:

- Review generated output before submission.
- Ensure generated code/docs follow repository standards.
- Validate claims (tests run, behavior, and side effects).
- Keep AI-generated changes scoped; avoid large unreviewable diffs.

## Review and merge

- At least one human reviewer approval is required.
- Required CI checks must pass.
- Address reviewer feedback with follow-up commits on the same branch.
- Merge only after approval and green checks.
