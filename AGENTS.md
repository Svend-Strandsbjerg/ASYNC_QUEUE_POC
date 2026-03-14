# AI Agent Operating Manual

This file defines required behavior for AI agents working in this repository and repositories derived from it.

## Core principles

- Preserve safety, clarity, and reviewability.
- Prefer small, incremental, verifiable changes.
- Avoid unnecessary complexity and speculative abstractions.
- Keep changes aligned to the explicit request.

## Branch and source-control rules

- Always work on a branch.
- Never modify `main` directly.
- Keep commits focused and logically grouped.
- Use descriptive commit messages that explain intent.

## Pull request expectations

For every PR, agents must:

- Explain the problem and why the change is needed.
- Summarize the implementation approach.
- Provide validation evidence (tests/checks run, including failures when relevant).
- Highlight risks, assumptions, and follow-ups.

## Testing rules

- Add or update tests when behavior or logic changes.
- For bug fixes, include regression coverage where practical.
- Do not claim tests were run if they were not.
- If tests cannot be run, state why and what remains unverified.

## Documentation rules

- Update documentation whenever behavior, structure, interfaces, or process changes.
- Keep docs concise, accurate, and consistent with implementation.
- Include onboarding/context updates when introducing new conventions.

## Scope control

- Do not introduce business/product functionality unless explicitly requested.
- Avoid unrelated refactors during targeted tasks.
- Call out out-of-scope findings separately instead of silently changing them.

## Communication standards

- Be explicit about assumptions.
- State risks and tradeoffs clearly.
- Prefer plain language and structured summaries.
- Provide actionable next steps when work is incomplete.

## Secure and compliant behavior

- Never hardcode secrets, credentials, or sensitive tokens.
- Follow repository security policies and least-privilege principles.
- Flag potentially risky operations before/within the PR description.
