from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class QueueState(str, Enum):
    OPEN = "OPEN"
    DISPATCHING = "DISPATCHING"
    PAUSED = "PAUSED"


class QueueItemState(str, Enum):
    PENDING = "PENDING"
    DISPATCHED = "DISPATCHED"
    FAILED = "FAILED"

    @property
    def is_terminal(self) -> bool:
        return self in {QueueItemState.DISPATCHED, QueueItemState.FAILED}


@dataclass
class QueueItem:
    payload: dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid4()))
    state: QueueItemState = QueueItemState.PENDING
    dispatch_attempts: int = 0


@dataclass
class QueueEvent:
    sequence: int
    event_type: str
    details: dict[str, Any]


class FakeTransport:
    """Transport double that records all sent items in order."""

    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []

    def send(self, queue_id: str, item: QueueItem) -> bool:
        self.sent.append(
            {
                "queue_id": queue_id,
                "item_id": item.id,
                "payload": deepcopy(item.payload),
            }
        )
        return True


class AsyncQueue:
    def __init__(self, scope: dict[str, Any], queue_id: str | None = None) -> None:
        self.id = queue_id or str(uuid4())
        self.scope = deepcopy(scope)
        self.state = QueueState.OPEN
        self._state_before_pause: QueueState | None = None
        self.items: list[QueueItem] = []
        self.activity_log: list[QueueEvent] = []
        self._sequence = 0
        self._log("QUEUE_CREATED", {"scope": deepcopy(self.scope)})

    def _log(self, event_type: str, details: dict[str, Any]) -> None:
        self._sequence += 1
        self.activity_log.append(QueueEvent(self._sequence, event_type, deepcopy(details)))

    def pause(self) -> None:
        if self.state == QueueState.PAUSED:
            self._log("QUEUE_PAUSE_SKIPPED", {"reason": "already_paused"})
            return
        self._state_before_pause = self.state
        self.state = QueueState.PAUSED
        self._log("QUEUE_PAUSED", {"state_before_pause": self._state_before_pause.value})

    def resume(self) -> None:
        if self.state != QueueState.PAUSED:
            self._log("QUEUE_RESUME_SKIPPED", {"reason": "not_paused"})
            return
        restored_state = self._state_before_pause or QueueState.OPEN
        self.state = restored_state
        self._state_before_pause = None
        self._log("QUEUE_RESUMED", {"restored_state": restored_state.value})

    def add_item(self, payload: dict[str, Any]) -> QueueItem:
        item = QueueItem(payload=deepcopy(payload))
        self.items.append(item)
        self._log("ITEM_ADDED", {"item_id": item.id, "state": item.state.value})
        return item

    def dispatch_all(self, transport: FakeTransport) -> int:
        if self.state == QueueState.PAUSED:
            self._log("DISPATCH_SKIPPED", {"reason": "queue_paused"})
            return 0

        dispatchable_items = [item for item in self.items if item.state == QueueItemState.PENDING]
        if not dispatchable_items:
            self._log("DISPATCH_SKIPPED", {"reason": "no_dispatchable_items"})
            return 0

        previous_state = self.state
        self.state = QueueState.DISPATCHING
        self._log("DISPATCH_STARTED", {"items": len(dispatchable_items)})

        dispatched = 0
        for item in dispatchable_items:
            item.dispatch_attempts += 1
            sent = transport.send(self.id, item)
            item.state = QueueItemState.DISPATCHED if sent else QueueItemState.FAILED
            self._log(
                "ITEM_DISPATCHED",
                {
                    "item_id": item.id,
                    "attempt": item.dispatch_attempts,
                    "result_state": item.state.value,
                },
            )
            dispatched += 1

        self.state = previous_state
        self._log("DISPATCH_COMPLETED", {"dispatched_items": dispatched, "state_after": self.state.value})
        return dispatched

    def snapshot(self) -> dict[str, Any]:
        return {
            "queue_id": self.id,
            "scope": deepcopy(self.scope),
            "queue_state": self.state.value,
            "item_count": len(self.items),
            "items": [
                {
                    "item_id": item.id,
                    "state": item.state.value,
                    "dispatch_attempts": item.dispatch_attempts,
                    "payload": deepcopy(item.payload),
                }
                for item in self.items
            ],
            "activity_log": [
                {
                    "sequence": event.sequence,
                    "event_type": event.event_type,
                    "details": deepcopy(event.details),
                }
                for event in self.activity_log
            ],
        }


class InMemoryQueueRepository:
    def __init__(self) -> None:
        self._queues_by_scope: dict[tuple[tuple[str, Any], ...], AsyncQueue] = {}

    @staticmethod
    def _scope_key(scope: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
        return tuple(sorted(deepcopy(scope).items()))

    def get_or_create_queue(self, scope: dict[str, Any]) -> AsyncQueue:
        key = self._scope_key(scope)
        if key not in self._queues_by_scope:
            self._queues_by_scope[key] = AsyncQueue(scope=scope)
        return self._queues_by_scope[key]
