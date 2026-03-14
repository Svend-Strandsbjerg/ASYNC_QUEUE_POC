# Repository Operating Model

## Purpose

This document defines the operating architecture for repositories created from this foundation. It focuses on governance and delivery mechanics rather than product architecture.

## Source of truth

- GitHub is the canonical system for source code, issues, pull requests, and workflow history.
- `main` represents the latest reviewed, merge-ready state.
- All non-trivial changes must be traceable to an issue/task/request.

## Branch-based development model

- Contributors (human or AI) work in short-lived branches.
- Direct pushes to `main` are disallowed by policy.
- Branch names should indicate intent (for example: `docs/ci-foundation`, `chore/update-templates`).

## Pull request workflow

- Every change is delivered through a pull request.
- PRs must explain:
  - what changed,
  - why the change is needed,
  - how it was validated,
  - risks/assumptions.
- PRs should remain small and reviewable whenever possible.

## CI quality gates

The CI pipeline should evolve with the repository and typically enforce:

- Repository hygiene checks
- Standards/lint checks
- Test execution
- Any required security or policy checks

In this foundation stage, CI focuses on repository structure and documentation integrity. Workflow-file syntax validation is kept in a separate dedicated workflow so CI definitions can be validated independently of the main repository hygiene pipeline. Product-specific build/test jobs are added when product code exists.

## Documentation requirements

Repositories created from this template are documentation-driven:

- `README.md` for onboarding and intent
- `ARCHITECTURE.md` for operating model and key decisions
- Standards and process docs under `docs/`
- PR-level documentation updates whenever behavior/process/structure changes

## Testing requirements

- Logic changes require unit tests.
- Bug fixes require regression tests where practical.
- Integration tests are added when components interact across boundaries.
- Tests must verify behavior and reduce risk, not only increase coverage metrics.

## Human review and merge policy

- At least one human reviewer approves before merge to `main`.
- Required CI checks must pass before merge.
- Urgent exceptions should be rare, documented, and followed by retrospective cleanup.

## Change management principles

- Prefer incremental changes over broad rewrites.
- Make assumptions explicit in PR descriptions.
- Capture non-obvious tradeoffs in architecture/process docs.
- Keep templates and standards generic unless intentionally specializing for a specific project.
