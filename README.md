# ASYNC_QUEUE_POC

Minimal proof-of-concept for queue flow verification.

## What is included

- Existing in-memory queue domain (`async_queue_poc.domain`) with pause/resume/add/dispatch/snapshot behavior.
- CLI wrapper (`async_queue_poc.cli`) for terminal-driven interaction.
- FastAPI wrapper (`async_queue_poc.api`) exposing queue operations as REST endpoints.
- Minimal browser UI (`async_queue_poc/ui`) for local debugging and visual flow checks.
- Tests covering domain, CLI, and API wrappers.

## Project structure

- `async_queue_poc/domain.py`: queue/domain logic.
- `async_queue_poc/cli.py`: CLI wrapper around queue logic.
- `async_queue_poc/api.py`: FastAPI app and in-memory API service.
- `async_queue_poc/ui/index.html`: UI layout.
- `async_queue_poc/ui/app.js`: browser behavior and API calls.
- `async_queue_poc/ui/styles.css`: simple three-column styling.
- `tests/`: automated tests.

## Install dependencies

```bash
pip install -r requirements.txt
```

## Run the server (API + UI)

```bash
python -m uvicorn async_queue_poc.api:app --reload
```

Open:

- UI: `http://localhost:8000/ui`
- OpenAPI docs: `http://localhost:8000/docs`

## REST endpoints

- `GET /queues`
- `POST /queues`
- `GET /queues/{name}`
- `POST /queues/{name}/pause`
- `POST /queues/{name}/resume`
- `POST /queues/{name}/items`
- `POST /queues/{name}/dispatch` (debug/manual)
- `POST /test/run`
- `GET /transport/log`

## Demo flow in UI

1. Create queues manually in the UI (for example: Queue A, Queue B, Queue C).
2. Add items to each queue and pause whichever queues should be held back.
3. Click **Run Test**.
4. Verify open queues send all pending items in insertion order and paused queues remain pending.
5. Inspect queue details, activity log, and dummy transport log for processing order and skipped queues.

## Run tests

```bash
pytest
```

## Optional CLI demo

```bash
python -m async_queue_poc.cli
```
