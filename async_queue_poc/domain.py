from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class QueueItem:
    item_id: str
    payload: str
    created_at: str
    sent_at: str | None = None


@dataclass(frozen=True)
class QueueSnapshot:
    queue_id: str
    name: str
    is_paused: bool
    size: int
    pending_items: list[QueueItem]
    dispatched_items: list[QueueItem]


class Queue:
    """Simple in-memory queue domain object used by the POC."""

    def __init__(self, name: str):
        self._id = str(uuid4())
        self._name = name
        self._is_paused = False
        self._items: deque[QueueItem] = deque()
        self._dispatched_items: list[QueueItem] = []

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    def pause(self) -> None:
        self._is_paused = True

    def resume(self) -> None:
        self._is_paused = False

    def add_item(self, payload: str) -> QueueItem:
        item = QueueItem(
            item_id=str(uuid4()),
            payload=payload,
            created_at=datetime.now(tz=timezone.utc).isoformat(),
        )
        self._items.append(item)
        return item

    def dispatch(self) -> QueueItem | None:
        if self._is_paused or not self._items:
            return None
        item = self._items.popleft()
        dispatched_item = QueueItem(
            item_id=item.item_id,
            payload=item.payload,
            created_at=item.created_at,
            sent_at=datetime.now(tz=timezone.utc).isoformat(),
        )
        self._dispatched_items.append(dispatched_item)
        return dispatched_item

    def snapshot(self) -> QueueSnapshot:
        return QueueSnapshot(
            queue_id=self._id,
            name=self._name,
            is_paused=self._is_paused,
            size=len(self._items),
            pending_items=list(self._items),
            dispatched_items=list(self._dispatched_items),
        )

    def pending_count(self) -> int:
        return len(self._items)
