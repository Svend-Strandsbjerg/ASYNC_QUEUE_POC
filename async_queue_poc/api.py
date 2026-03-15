from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .domain import Queue, QueueItem

app = FastAPI(title="Async Queue POC")


class CreateQueueRequest(BaseModel):
    name: str = Field(min_length=1)


class AddItemRequest(BaseModel):
    item: str


class QueueService:
    """Thin in-memory service that wraps the queue domain objects for API/UI use."""

    def __init__(self) -> None:
        self._queues_by_id: dict[str, Queue] = {}
        self._queue_ids_by_name: dict[str, str] = {}
        self._transport_log: list[dict[str, str]] = []

    def list_queues(self) -> list[dict[str, object]]:
        return [self._serialize_queue(queue) for queue in self._queues_by_id.values()]

    def create_queue(self, name: str) -> dict[str, object]:
        if name in self._queue_ids_by_name:
            raise ValueError(f"Queue '{name}' already exists")

        queue = Queue(name)
        self._queues_by_id[queue.id] = queue
        self._queue_ids_by_name[name] = queue.id
        return self._serialize_queue(queue)

    def _resolve_queue_id(self, queue_ref: str) -> str:
        if queue_ref in self._queues_by_id:
            return queue_ref
        queue_id = self._queue_ids_by_name.get(queue_ref)
        if queue_id is not None:
            return queue_id
        raise KeyError(f"Queue '{queue_ref}' not found")

    def get_queue(self, queue_ref: str) -> Queue:
        queue_id = self._resolve_queue_id(queue_ref)
        return self._queues_by_id[queue_id]

    def pause_queue(self, queue_ref: str) -> dict[str, object]:
        queue = self.get_queue(queue_ref)
        queue.pause()
        return self._serialize_queue(queue)

    def resume_queue(self, queue_ref: str) -> dict[str, object]:
        queue = self.get_queue(queue_ref)
        queue.resume()
        return self._serialize_queue(queue)

    def add_item(self, queue_ref: str, payload: str) -> dict[str, object]:
        queue = self.get_queue(queue_ref)
        item = queue.add_item(payload)
        return {
            "queue": self._serialize_queue(queue),
            "item": self._serialize_item(queue.id, item, status="PENDING"),
        }

    def dispatch_item(self, queue_ref: str) -> dict[str, object]:
        queue = self.get_queue(queue_ref)
        dispatched_item = queue.dispatch()
        if dispatched_item is not None:
            self._record_sent_item(queue, dispatched_item)

        return {
            "dispatched_item": self._serialize_item(queue.id, dispatched_item, status="SENT")
            if dispatched_item is not None
            else None,
            "queue": self._serialize_queue(queue),
        }

    def run_test(self) -> dict[str, object]:
        results: list[dict[str, object]] = []
        processed_queues = 0
        processed_items = 0
        skipped_queues = 0
        skipped_items = 0
        sending_queues = 0
        sent_items = 0

        for queue in self._queues_by_id.values():
            queue_snapshot = queue.snapshot()
            if queue.is_paused:
                skipped_queues += 1
                skipped_items += queue_snapshot.size
                results.append(
                    {
                        "queue_id": queue.id,
                        "queue_name": queue.name,
                        "status": "SKIPPED",
                        "reason": "paused",
                        "items_sent": [],
                        "items_sent_count": 0,
                        "pending_items": [self._serialize_item(queue.id, item, "PENDING") for item in queue_snapshot.pending_items],
                        "remaining_items": queue_snapshot.size,
                    }
                )
                continue

            processed_queues += 1
            sent_items_for_queue: list[dict[str, str]] = []
            while True:
                dispatched_item = queue.dispatch()
                if dispatched_item is None:
                    break
                serialized_item = self._serialize_item(queue.id, dispatched_item, status="SENT")
                sent_items_for_queue.append(serialized_item)
                self._record_sent_item(queue, dispatched_item)

            sent_count = len(sent_items_for_queue)
            processed_items += sent_count
            sent_items += sent_count
            if sent_count > 0:
                sending_queues += 1

            results.append(
                {
                    "queue_id": queue.id,
                    "queue_name": queue.name,
                    "status": "SENT",
                    "items_sent": sent_items_for_queue,
                    "items_sent_count": sent_count,
                    "remaining_items": queue.pending_count(),
                }
            )

        return {
            "processed": {"queues": processed_queues, "items": processed_items},
            "skipped": {"queues": skipped_queues, "items": skipped_items},
            "sent": {"queues": sending_queues, "items": sent_items},
            # Backward-compatible aliases
            "queues_processed": processed_queues,
            "queues_skipped": skipped_queues,
            "items_sent": sent_items,
            "results": results,
        }

    def queue_snapshot(self, queue_ref: str) -> dict[str, object]:
        queue = self.get_queue(queue_ref)
        snapshot = asdict(queue.snapshot())
        state = "PAUSED" if snapshot.pop("is_paused") else "OPEN"
        pending_items = snapshot.pop("pending_items")
        dispatched_items = snapshot.pop("dispatched_items")
        item_entries = [
            self._serialize_item(queue.id, QueueItem(**item), "PENDING") for item in pending_items
        ] + [self._serialize_item(queue.id, QueueItem(**item), "SENT") for item in dispatched_items]
        return {
            "queue_id": snapshot["queue_id"],
            "queue_name": snapshot["name"],
            "state": state,
            "size": snapshot["size"],
            "sent_count": len(dispatched_items),
            "items": item_entries,
        }

    def transport_log(self) -> list[dict[str, str]]:
        return list(self._transport_log)

    def reset(self) -> None:
        self._queues_by_id.clear()
        self._queue_ids_by_name.clear()
        self._transport_log.clear()

    def _record_sent_item(self, queue: Queue, item: QueueItem) -> None:
        released_at = item.sent_at or item.created_at
        self._transport_log.append(
            {
                "queue_id": queue.id,
                "queue_name": queue.name,
                "item_id": item.item_id,
                "payload": item.payload,
                "released_at": released_at,
                "timestamp": released_at,
            }
        )

    def _serialize_item(self, queue_id: str, item: QueueItem, status: str) -> dict[str, str]:
        return {
            "item_id": item.item_id,
            "queue_id": queue_id,
            "payload": item.payload,
            "status": status,
            "created_at": item.created_at,
            "sent_at": item.sent_at,
        }

    def _serialize_queue(self, queue: Queue) -> dict[str, object]:
        snapshot = queue.snapshot()
        return {
            "queue_id": snapshot.queue_id,
            "queue_name": snapshot.name,
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


@app.get("/queues/{queue_ref}")
def queue_snapshot(queue_ref: str) -> dict[str, object]:
    try:
        return service.queue_snapshot(queue_ref)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/queues/{queue_ref}/pause")
def pause_queue(queue_ref: str) -> dict[str, object]:
    try:
        return service.pause_queue(queue_ref)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/queues/{queue_ref}/resume")
def resume_queue(queue_ref: str) -> dict[str, object]:
    try:
        return service.resume_queue(queue_ref)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/queues/{queue_ref}/items")
def add_item(queue_ref: str, payload: AddItemRequest) -> dict[str, object]:
    try:
        return service.add_item(queue_ref, payload.item)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/queues/{queue_ref}/dispatch")
def dispatch_item(queue_ref: str) -> dict[str, object]:
    try:
        return service.dispatch_item(queue_ref)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/test/run")
def run_test() -> dict[str, object]:
    return service.run_test()


@app.get("/transport/log")
def transport_log() -> list[dict[str, str]]:
    return service.transport_log()


ui_path = Path(__file__).parent / "ui"
app.mount("/ui", StaticFiles(directory=ui_path, html=True), name="ui")
