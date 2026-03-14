from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class QueueSnapshot(Generic[T]):
    name: str
    is_paused: bool
    size: int
    pending_items: list[T]
    dispatched_items: list[T]


class Queue(Generic[T]):
    """Simple in-memory queue domain object used by the POC."""

    def __init__(self, name: str):
        self._name = name
        self._is_paused = False
        self._items: Deque[T] = deque()
        self._dispatched_items: list[T] = []

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

    def add_item(self, item: T) -> None:
        self._items.append(item)

    def dispatch(self) -> T | None:
        if self._is_paused or not self._items:
            return None
        item = self._items.popleft()
        self._dispatched_items.append(item)
        return item

    def snapshot(self) -> QueueSnapshot[T]:
        return QueueSnapshot(
            name=self._name,
            is_paused=self._is_paused,
            size=len(self._items),
            pending_items=list(self._items),
            dispatched_items=list(self._dispatched_items),
        )
