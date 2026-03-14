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


class GenerateQueuesRequest(BaseModel):
    queue_count: int = Field(ge=1, le=50)
    items_per_queue: int = Field(ge=0, le=100)
    paused_queue_indices: list[int] = Field(default_factory=list)
    queue_prefix: str = Field(default="Queue")


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
            self._record_sent_item(queue.name, dispatched_item)
        return {
            "dispatched_item": dispatched_item,
            "queue": self._serialize_queue(queue),
        }

    def run_test(self) -> dict[str, object]:
        results: list[dict[str, object]] = []
        queues_skipped = 0
        items_sent = 0

        for queue in self._queues.values():
            if queue.is_paused:
                queues_skipped += 1
                results.append(
                    {
                        "queue": queue.name,
                        "status": "SKIPPED",
                        "reason": "paused",
                        "items_sent": 0,
                        "remaining_items": queue.snapshot().size,
                    }
                )
                continue

            sent_items: list[str] = []
            while True:
                dispatched_item = queue.dispatch()
                if dispatched_item is None:
                    break
                sent_items.append(dispatched_item)
                self._record_sent_item(queue.name, dispatched_item)

            items_sent += len(sent_items)
            results.append(
                {
                    "queue": queue.name,
                    "status": "SENT",
                    "items_sent": len(sent_items),
                    "sent_items": sent_items,
                    "remaining_items": queue.snapshot().size,
                }
            )

        return {
            "queues_processed": len(self._queues),
            "queues_skipped": queues_skipped,
            "items_sent": items_sent,
            "results": results,
        }

    def generate_test_queues(
        self,
        queue_count: int,
        items_per_queue: int,
        paused_queue_indices: list[int],
        queue_prefix: str,
    ) -> list[dict[str, object]]:
        created_queues: list[dict[str, object]] = []
        for idx in range(queue_count):
            queue_name = f"{queue_prefix}-{idx + 1}"
            if queue_name in self._queues:
                continue
            queue = Queue[str](queue_name)
            for item_idx in range(items_per_queue):
                queue.add_item(f"{queue_name}-item-{item_idx + 1}")
            if idx in paused_queue_indices:
                queue.pause()
            self._queues[queue_name] = queue
            created_queues.append(self._serialize_queue(queue))
        return created_queues

    def queue_snapshot(self, name: str) -> dict[str, object]:
        queue = self.get_queue(name)
        snapshot = asdict(queue.snapshot())
        state = "PAUSED" if snapshot.pop("is_paused") else "OPEN"
        pending_items = snapshot.pop("pending_items")
        dispatched_items = snapshot.pop("dispatched_items")
        item_entries = [
            {"payload": item, "status": "PENDING"} for item in pending_items
        ] + [{"payload": item, "status": "SENT"} for item in dispatched_items]
        return {
            "name": snapshot["name"],
            "state": state,
            "size": snapshot["size"],
            "sent_count": len(dispatched_items),
            "items": item_entries,
        }

    def transport_log(self) -> list[dict[str, str]]:
        return list(self._transport_log)

    def reset(self) -> None:
        self._queues.clear()
        self._transport_log.clear()

    def _record_sent_item(self, queue_name: str, item: str) -> None:
        self._transport_log.append(
            {
                "queue": queue_name,
                "item": item,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            }
        )

    def _serialize_queue(self, queue: Queue[str]) -> dict[str, object]:
        snapshot = queue.snapshot()
        return {
            "name": snapshot.name,
            "state": "PAUSED" if snapshot.is_paused else "OPEN",
            "item_count": snapshot.size,
            "sent_item_count": len(snapshot.dispatched_items),
            "total_item_count": snapshot.size + len(snapshot.dispatched_items),
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


@app.post("/test/run")
def run_test() -> dict[str, object]:
    return service.run_test()


@app.post("/test/generate")
def generate_test_queues(payload: GenerateQueuesRequest) -> dict[str, object]:
    created_queues = service.generate_test_queues(
        queue_count=payload.queue_count,
        items_per_queue=payload.items_per_queue,
        paused_queue_indices=payload.paused_queue_indices,
        queue_prefix=payload.queue_prefix,
    )
    return {"created": len(created_queues), "queues": created_queues}


@app.get("/transport/log")
def transport_log() -> list[dict[str, str]]:
    return service.transport_log()


ui_path = Path(__file__).parent / "ui"
app.mount("/ui", StaticFiles(directory=ui_path, html=True), name="ui")
