# ASYNC_QUEUE_POC

Minimal proof-of-concept for queue flow verification, now with a **thin interactive CLI layer** so flow can be demonstrated manually.

## What is included

- Minimal queue/domain core (`Queue`) for pause/resume/add/dispatch/snapshot behavior.
- Thin CLI wrapper with commands:
  - `create-queue`
  - `pause-queue`
  - `add-item`
  - `show-snapshot`
  - `resume-queue`
  - `dispatch`
- Tests for both domain behavior and interactive wrapper behavior.

## Project structure

- `async_queue_poc/domain.py`: queue/domain logic.
- `async_queue_poc/cli.py`: CLI wrapper around existing queue logic.
- `tests/test_domain_queue.py`: domain tests.
- `tests/test_cli_wrapper.py`: wrapper-level interaction test.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Run tests

```bash
pytest
```

## Run interactive CLI demo


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
python -m async_queue_poc.cli
```

Then run commands, for example:

```text
create-queue demo
add-item demo job-1
show-snapshot demo
pause-queue demo
dispatch demo
resume-queue demo
dispatch demo
show-snapshot demo
```

## Notes

- POC stays minimal and focused on framework/flow verification.
- CLI layer is intentionally thin and reuses domain logic without rewriting core behavior.
