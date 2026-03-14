from async_integration_foundation.queue_framework import (
    FakeTransport,
    InMemoryQueueRepository,
    QueueItemState,
    QueueState,
)


def build_scope() -> dict[str, str]:
    return {
        "session_id": "sess-001",
        "user_id": "alice",
        "context_type": "ORDER",
        "context_id": "ORD-9001",
    }


def test_items_accumulate_while_paused_and_not_sent() -> None:
    repository = InMemoryQueueRepository()
    transport = FakeTransport()
    queue = repository.get_or_create_queue(build_scope())

    queue.pause()
    for idx in range(5):
        queue.add_item({"value": idx})

    dispatched = queue.dispatch_all(transport)

    assert queue.state == QueueState.PAUSED
    assert len(queue.items) == 5
    assert dispatched == 0
    assert transport.sent == []


def test_resume_restores_previous_state_not_forced_open() -> None:
    repository = InMemoryQueueRepository()
    queue = repository.get_or_create_queue(build_scope())
    queue.state = QueueState.DISPATCHING

    queue.pause()
    queue.resume()

    assert queue.state == QueueState.DISPATCHING


def test_dispatch_sends_only_dispatchable_items() -> None:
    repository = InMemoryQueueRepository()
    transport = FakeTransport()
    queue = repository.get_or_create_queue(build_scope())

    first = queue.add_item({"value": "a"})
    second = queue.add_item({"value": "b"})
    second.state = QueueItemState.FAILED

    dispatched = queue.dispatch_all(transport)

    assert dispatched == 1
    assert first.state == QueueItemState.DISPATCHED
    assert second.state == QueueItemState.FAILED
    assert len(transport.sent) == 1
    assert transport.sent[0]["item_id"] == first.id


def test_terminal_items_are_not_redispatched() -> None:
    repository = InMemoryQueueRepository()
    transport = FakeTransport()
    queue = repository.get_or_create_queue(build_scope())

    queue.add_item({"value": "only-once"})

    first_dispatch = queue.dispatch_all(transport)
    second_dispatch = queue.dispatch_all(transport)

    assert first_dispatch == 1
    assert second_dispatch == 0
    assert len(transport.sent) == 1


def test_scope_metadata_is_isolated_from_caller_mutation() -> None:
    repository = InMemoryQueueRepository()
    scope = build_scope()

    queue = repository.get_or_create_queue(scope)
    scope["user_id"] = "bob"

    assert queue.scope["user_id"] == "alice"


def test_snapshot_contains_debuggable_state_and_activity() -> None:
    repository = InMemoryQueueRepository()
    transport = FakeTransport()
    queue = repository.get_or_create_queue(build_scope())
    queue.pause()
    queue.add_item({"value": "x"})
    queue.resume()
    queue.dispatch_all(transport)

    snapshot = queue.snapshot()

    assert snapshot["queue_id"] == queue.id
    assert snapshot["scope"]["context_id"] == "ORD-9001"
    assert snapshot["queue_state"] == queue.state.value
    assert snapshot["item_count"] == 1
    assert snapshot["items"][0]["state"] == QueueItemState.DISPATCHED.value
    assert any(event["event_type"] == "QUEUE_PAUSED" for event in snapshot["activity_log"])
    assert any(event["event_type"] == "DISPATCH_COMPLETED" for event in snapshot["activity_log"])
