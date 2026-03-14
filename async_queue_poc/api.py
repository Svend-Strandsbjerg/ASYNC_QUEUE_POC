from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .domain import Queue

app = FastAPI(title="Async Queue POC")


class CreateQueueRequest(BaseModel):
    name: str = Field(min_length=1)


class AddItemRequest(BaseModel):
    item: str


class QueueService:
    """Thin in-memory service that wraps the queue domain objects for API/UI use."""

    def __init__(self) -> None:
        self._queues: dict[str, Queue[str]] = {}
        self._transport_log: list[dict[str, str]] = []

    def list_queues(self) -> list[dict[str, object]]:
        return [self._serialize_queue(queue) for queue in self._queues.values()]

    def create_queue(self, name: str) -> dict[str, object]:
        if name in self._queues:
            raise ValueError(f"Queue '{name}' already exists")
        self._queues[name] = Queue[str](name)
        return self._serialize_queue(self._queues[name])

    def get_queue(self, name: str) -> Queue[str]:
        queue = self._queues.get(name)
        if queue is None:
            raise KeyError(f"Queue '{name}' not found")
        return queue

    def pause_queue(self, name: str) -> dict[str, object]:
        queue = self.get_queue(name)
        queue.pause()
        return self._serialize_queue(queue)

    def resume_queue(self, name: str) -> dict[str, object]:
        queue = self.get_queue(name)
        queue.resume()
        return self._serialize_queue(queue)

    def add_item(self, name: str, item: str) -> dict[str, object]:
        queue = self.get_queue(name)
        queue.add_item(item)
        return self._serialize_queue(queue)

    def dispatch_item(self, name: str) -> dict[str, object]:
        queue = self.get_queue(name)
        dispatched_item = queue.dispatch()
        if dispatched_item is not None:
            self._transport_log.append(
                {
                    "queue": queue.name,
                    "item": dispatched_item,
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                }
            )
        return {
            "dispatched_item": dispatched_item,
            "queue": self._serialize_queue(queue),
        }

    def queue_snapshot(self, name: str) -> dict[str, object]:
        queue = self.get_queue(name)
        snapshot = asdict(queue.snapshot())
        snapshot["state"] = "PAUSED" if snapshot.pop("is_paused") else "OPEN"
        snapshot["items"] = snapshot.pop("pending_items")
        return snapshot

    def transport_log(self) -> list[dict[str, str]]:
        return list(self._transport_log)

    def reset(self) -> None:
        self._queues.clear()
        self._transport_log.clear()

    def _serialize_queue(self, queue: Queue[str]) -> dict[str, object]:
        snapshot = queue.snapshot()
        return {
            "name": snapshot.name,
            "state": "PAUSED" if snapshot.is_paused else "OPEN",
            "items": snapshot.pending_items,
            "item_count": snapshot.size,
        }


service = QueueService()


@app.get("/queues")
def list_queues() -> list[dict[str, object]]:
    return service.list_queues()


@app.post("/queues")
def create_queue(payload: CreateQueueRequest) -> dict[str, object]:
    try:
        return service.create_queue(payload.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/queues/{name}")
def queue_snapshot(name: str) -> dict[str, object]:
    try:
        return service.queue_snapshot(name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/queues/{name}/pause")
def pause_queue(name: str) -> dict[str, object]:
    try:
        return service.pause_queue(name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/queues/{name}/resume")
def resume_queue(name: str) -> dict[str, object]:
    try:
        return service.resume_queue(name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/queues/{name}/items")
def add_item(name: str, payload: AddItemRequest) -> dict[str, object]:
    try:
        return service.add_item(name, payload.item)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/queues/{name}/dispatch")
def dispatch_item(name: str) -> dict[str, object]:
    try:
        return service.dispatch_item(name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/transport/log")
def transport_log() -> list[dict[str, str]]:
    return service.transport_log()


ui_path = Path(__file__).parent / "ui"
app.mount("/ui", StaticFiles(directory=ui_path, html=True), name="ui")
