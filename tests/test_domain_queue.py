from async_queue_poc.domain import Queue


def test_dispatch_returns_none_when_paused_and_keeps_items():
    queue = Queue[str]("demo")
    queue.add_item("a")
    queue.pause()

    result = queue.dispatch()

    assert result is None
    snapshot = queue.snapshot()
    assert snapshot.size == 1
    assert snapshot.pending_items == ["a"]


def test_dispatch_pops_first_item_when_running():
    queue = Queue[str]("demo")
    queue.add_item("first")
    queue.add_item("second")

    dispatched = queue.dispatch()

    assert dispatched == "first"
    assert queue.snapshot().pending_items == ["second"]
