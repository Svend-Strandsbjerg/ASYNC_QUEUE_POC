# Coding Standards

These standards provide generic engineering expectations for repositories built from this foundation.

## Core principles

- Prefer clarity over cleverness.
- Keep functions/modules focused and cohesive.
- Optimize for maintainability and readability.
- Use explicit naming that communicates intent.

## Design expectations

- Prefer simple designs first; add complexity only when justified.
- Avoid premature abstraction and speculative generalization.
- Keep public interfaces small and well-documented.
- Encapsulate side effects and isolate pure logic where practical.

## Naming and structure

- Use consistent naming conventions per language ecosystem.
- Choose names that describe behavior, not implementation details.
- Organize code by responsibility and boundaries.
- Remove dead code and unused paths promptly.

## Reliability and correctness

- Handle errors intentionally; avoid silent failure.
- Validate inputs at boundaries.
- Favor deterministic behavior in core logic.
- Use types/contracts/schemas where available to reduce ambiguity.

## Maintainability guidelines

- Keep files and functions at reviewable size.
- Add comments for non-obvious decisions, not trivial operations.
- Capture architectural tradeoffs in documentation.
- Refactor incrementally instead of large rewrites when possible.

## AI-generated code expectations

- AI-generated changes must meet the same standards as human-written code.
- Contributors are responsible for reviewing and validating generated output.
- Generated code should include tests and docs updates when relevant.
