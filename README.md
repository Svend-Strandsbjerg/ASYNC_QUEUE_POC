# AI-First Engineering Repository Foundation

This repository is a **reusable project foundation** for teams that build software with both human engineers and AI agents.

It is intentionally generic: it provides standards, process guidance, contribution workflows, and CI quality gates without introducing product-specific code.

## Why this foundation exists

Many projects fail to scale safely with AI assistance because expectations are implicit or inconsistent. This foundation makes those expectations explicit from day one:

- Branch-based development (no direct work on `main`)
- Pull requests as the unit of change and review
- Documented standards for code, tests, and docs
- CI checks that validate repository hygiene
- Human-reviewed merges for production-quality governance

## How this supports AI-assisted development

This template treats AI agents as first-class contributors while preserving engineering quality:

- `AGENTS.md` defines operating rules for AI contributors
- PR templates require clear scope, test evidence, and risk notes
- Process docs define a reproducible issue → branch → PR workflow
- Testing and documentation standards prevent "code-only" changes

## How to use this template for future projects

1. Create a new repository from this foundation.
2. Update placeholders (CODEOWNERS, support contacts, security policy details, CI language/runtime steps).
3. Add product code incrementally under agreed project directories.
4. Keep standards/process documentation up to date as the project evolves.
5. Protect `main` with required status checks and human review rules.

## Development workflow (high level)

1. Start from an issue/task with clear scope and acceptance criteria.
2. Create a short-lived branch.
3. Implement a small, reviewable change.
4. Add or update tests and docs as relevant.
5. Open a pull request using the provided template.
6. Pass CI checks and complete human review.
7. Merge into `main` only after approval.

## Repository map

- `ARCHITECTURE.md`: Operating model for source control, CI, review, and quality gates.
- `AGENTS.md`: Rules for AI agents contributing safely.
- `CONTRIBUTING.md`: Contribution guide for humans and AI agents.
- `docs/standards/`: Engineering, testing, and documentation standards.
- `docs/process/`: Repeatable workflows for development and PR execution.
- `.github/`: PR template, issue templates, and CI workflows (repository hygiene plus workflow-file validation).
- `tests/`: Test scaffolding and repository-level validation scripts.

## Non-goals of this repository

This foundation intentionally does **not** include:

- Business/domain logic
- Product UI/API features
- Demo application layers
- Project-specific architecture implementations

Those belong in downstream repositories created from this template.
