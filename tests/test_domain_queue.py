from uuid import UUID

from async_queue_poc.domain import Queue


def test_dispatch_returns_none_when_paused_and_keeps_items() -> None:
    queue = Queue("demo")
    item = queue.add_item("a")
    queue.pause()

    result = queue.dispatch()

    assert result is None
    snapshot = queue.snapshot()
    assert snapshot.size == 1
    assert [entry.payload for entry in snapshot.pending_items] == ["a"]
    assert snapshot.pending_items[0].item_id == item.item_id
    assert snapshot.dispatched_items == []


def test_dispatch_pops_first_item_when_running() -> None:
    queue = Queue("demo")
    first_item = queue.add_item("first")
    queue.add_item("second")

    dispatched = queue.dispatch()

    assert dispatched is not None
    assert dispatched.payload == "first"
    assert dispatched.item_id == first_item.item_id
    assert dispatched.sent_at is not None
    snapshot = queue.snapshot()
    assert [entry.payload for entry in snapshot.pending_items] == ["second"]
    assert [entry.payload for entry in snapshot.dispatched_items] == ["first"]


def test_queue_and_item_ids_are_foundation_generated() -> None:
    queue = Queue("demo")
    first = queue.add_item("first")
    second = queue.add_item("second")

    assert UUID(queue.id)
    assert UUID(first.item_id)
    assert UUID(second.item_id)
    assert first.item_id != second.item_id
