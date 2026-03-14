import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from async_integration_foundation.local_ui_app import create_app


def scope_payload() -> dict[str, str]:
    return {
        "session_id": "sess-001",
        "user_id": "alice",
        "context_type": "ORDER",
        "context_id": "ORD-9001",
    }


def test_get_or_create_queue_endpoint_returns_same_queue_for_same_scope() -> None:
    client = TestClient(create_app())

    first = client.post("/api/queues/get-or-create", json=scope_payload())
    second = client.post("/api/queues/get-or-create", json=scope_payload())

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["queue"]["queue_id"] == second.json()["queue"]["queue_id"]


def test_pause_and_resume_endpoints_update_queue_state() -> None:
    client = TestClient(create_app())
    queue_id = client.post("/api/queues/get-or-create", json=scope_payload()).json()["queue"]["queue_id"]

    paused = client.post(f"/api/queues/{queue_id}/pause")
    resumed = client.post(f"/api/queues/{queue_id}/resume")

    assert paused.status_code == 200
    assert resumed.status_code == 200
    assert paused.json()["snapshot"]["queue_state"] == "PAUSED"
    assert resumed.json()["snapshot"]["queue_state"] == "OPEN"


def test_add_item_endpoint_adds_pending_item() -> None:
    client = TestClient(create_app())
    queue_id = client.post("/api/queues/get-or-create", json=scope_payload()).json()["queue"]["queue_id"]

    response = client.post(f"/api/queues/{queue_id}/items", json={"payload": {"value": "x"}})

    assert response.status_code == 200
    payload = response.json()
    assert payload["item"]["state"] == "PENDING"
    assert payload["snapshot"]["item_count"] == 1


def test_dispatch_endpoint_dispatches_and_does_not_redispatch_terminal_items() -> None:
    client = TestClient(create_app())
    queue_id = client.post("/api/queues/get-or-create", json=scope_payload()).json()["queue"]["queue_id"]
    for idx in range(3):
        client.post(f"/api/queues/{queue_id}/items", json={"payload": {"value": idx}})

    first_dispatch = client.post(f"/api/queues/{queue_id}/dispatch")
    second_dispatch = client.post(f"/api/queues/{queue_id}/dispatch")

    assert first_dispatch.status_code == 200
    assert second_dispatch.status_code == 200
    assert first_dispatch.json()["dispatched"] == 3
    assert second_dispatch.json()["dispatched"] == 0


def test_sent_log_endpoint_lists_items_and_supports_queue_filter() -> None:
    client = TestClient(create_app())
    queue_a = client.post("/api/queues/get-or-create", json=scope_payload()).json()["queue"]["queue_id"]
    scope_b = scope_payload() | {"context_id": "ORD-9002"}
    queue_b = client.post("/api/queues/get-or-create", json=scope_b).json()["queue"]["queue_id"]

    client.post(f"/api/queues/{queue_a}/items", json={"payload": {"value": "a1"}})
    client.post(f"/api/queues/{queue_b}/items", json={"payload": {"value": "b1"}})
    client.post(f"/api/queues/{queue_a}/dispatch")
    client.post(f"/api/queues/{queue_b}/dispatch")

    all_entries = client.get("/api/sent-log")
    filtered_entries = client.get(f"/api/sent-log?queue_id={queue_a}")

    assert all_entries.status_code == 200
    assert filtered_entries.status_code == 200
    assert all_entries.json()["count"] == 2
    assert filtered_entries.json()["count"] == 1
    assert filtered_entries.json()["entries"][0]["queue_id"] == queue_a
