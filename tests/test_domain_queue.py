from async_queue_poc.domain import Queue


def test_dispatch_returns_none_when_paused_and_keeps_items() -> None:
    queue = Queue[str]("demo")
    queue.add_item("a")
    queue.pause()

    result = queue.dispatch()

    assert result is None
    snapshot = queue.snapshot()
    assert snapshot.size == 1
    assert snapshot.pending_items == ["a"]
    assert snapshot.dispatched_items == []


def test_dispatch_pops_first_item_when_running() -> None:
    queue = Queue[str]("demo")
    queue.add_item("first")
    queue.add_item("second")

    dispatched = queue.dispatch()

    assert dispatched == "first"
    snapshot = queue.snapshot()
    assert snapshot.pending_items == ["second"]
    assert snapshot.dispatched_items == ["first"]
