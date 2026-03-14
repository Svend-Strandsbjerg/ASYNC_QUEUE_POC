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

Start interactive shell:

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
