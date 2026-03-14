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

## Async Queue POC

Denne repository indeholder en lille, isoleret proof-of-concept for et business-neutralt async queue-framework.

### Kør POC-demo

```bash
python examples/async_queue_poc.py
```

Forventet output:

- Step A: queue oprettes/findes via scope-baseret opslag, og initial snapshot vises.
- Step B: queue pauses, 4 items tilføjes, dispatch forsøges men bliver korrekt skippet.
- Step C: queue unpauses, dispatch køres, og items ender i terminal state.
- Step D: dispatch forsøges igen uden redispatch af terminale items.
- Fake transport-log viser præcis hvilke items der blev “sendt” og i hvilken rækkefølge.


### Kør lokalt backend + UI

Installer dependencies og start FastAPI-servicen (inkl. UI):

```bash
pip install -r requirements.txt
uvicorn async_integration_foundation.local_ui_app:app --reload
```

URL'er:

- UI: `http://127.0.0.1:8000/`
- API docs: `http://127.0.0.1:8000/docs`
- Queue API base: `http://127.0.0.1:8000/api`

Kort demo-flow i UI:

1. Udfyld scope-felter i midterkolonnen og klik **Create/Get Queue**.
2. Vælg queue i venstre kolonne.
3. Klik **Pause** og tilføj 3-5 items via **Add Item**.
4. Bekræft at items står som `PENDING`, og at sent-log er tom mens queue er paused.
5. Klik **Resume** og derefter **Dispatch**.
6. Se items gå til `DISPATCHED` samt entries i højre kolonne under sent-log.
7. Klik **Dispatch** igen og bekræft at intet redispatches.

UI'et viser både aktive/open/paused queues og queues med historisk dispatch via summary-badges i venstre kolonne.

### Kør tests

```bash
pytest -q
```

### Hvad POC'en verificerer

- Scope-baseret `get_or_create_queue` ergonomi via repository-abstraktion.
- Pause/resume lifecycle, hvor `resume` genskaber forrige state i stedet for blindt at sætte `OPEN`.
- Centraliserede dispatch-regler: kun dispatchable items sendes, terminale items redispatches ikke.
- Metadata isolation: input-metadata deep-copy'es, så caller-mutation ikke ændrer queueens lagrede metadata.
- Snapshot/read model giver nok signal til inspektion og debugging (state, items, activity log).

### Antagelser og gaps

- Fake transport returnerer altid succes for at holde POC'en minimal og deterministisk.
- Repository er in-memory (ingen persistens eller concurrent locking i denne demo).
- Naturligt næste skridt er at koble samme abstractions til en persistent repository-implementering og mere avanceret dispatch-fejlhåndtering.
