# AI Agent Workflow

This workflow describes how AI agents should be used safely and effectively in repositories created from this foundation.

## Role of AI agents

AI agents are implementation assistants, not autonomous owners of production changes.
Human reviewers remain accountable for correctness, risk decisions, and merge approval.

## Standard AI contribution flow

1. **Understand the request**: restate scope, constraints, and assumptions.
2. **Plan the change**: identify affected files, tests, and docs.
3. **Implement incrementally**: prefer small, reviewable commits.
4. **Validate claims**: run checks/tests and report outcomes accurately.
5. **Prepare PR context**: summarize approach, risks, and follow-ups.

## Safety and quality requirements

- Never work directly on `main`.
- Avoid introducing unrelated changes.
- Update tests and documentation when relevant.
- Clearly call out assumptions, limitations, and uncertain areas.
- Do not fabricate command results or validation evidence.

## Reviewability rules

- Keep diffs focused and understandable.
- Explain non-obvious decisions.
- Prefer explicitness over hidden behavior.
- Flag any potentially risky operations for reviewers.

## Escalation expectations

When uncertain, AI contributions should surface:

- Ambiguous requirements
- Potentially breaking changes
- Security or compliance concerns
- Gaps in testability or observability

These should be highlighted in PR notes for human resolution.
