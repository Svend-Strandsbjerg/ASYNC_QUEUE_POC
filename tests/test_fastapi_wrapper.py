import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

import async_queue_poc.api as api


@pytest.fixture(autouse=True)
def clear_state() -> None:
    api.service.reset()


def test_run_test_sends_open_queue_items_and_skips_paused_items() -> None:
    client = TestClient(api.app)

    client.post("/queues", json={"name": "Queue A"})
    client.post("/queues", json={"name": "Queue B"})
    client.post("/queues", json={"name": "Queue C"})

    client.post("/queues/Queue B/pause")

    client.post("/queues/Queue A/items", json={"item": "A1"})
    client.post("/queues/Queue A/items", json={"item": "A2"})
    client.post("/queues/Queue B/items", json={"item": "B1"})
    client.post("/queues/Queue B/items", json={"item": "B2"})
    client.post("/queues/Queue C/items", json={"item": "C1"})

    run_response = client.post("/test/run")

    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["queues_processed"] == 3
    assert payload["queues_skipped"] == 1
    assert payload["items_sent"] == 3

    result_by_queue = {result["queue"]: result for result in payload["results"]}
    assert result_by_queue["Queue A"] == {
        "queue": "Queue A",
        "status": "SENT",
        "items_sent": ["A1", "A2"],
        "remaining_items": 0,
    }
    assert result_by_queue["Queue B"] == {
        "queue": "Queue B",
        "status": "SKIPPED",
        "reason": "paused",
        "remaining_items": 2,
    }
    assert result_by_queue["Queue C"] == {
        "queue": "Queue C",
        "status": "SENT",
        "items_sent": ["C1"],
        "remaining_items": 0,
    }

    a_snapshot = client.get("/queues/Queue A").json()
    b_snapshot = client.get("/queues/Queue B").json()
    c_snapshot = client.get("/queues/Queue C").json()

    assert [item["status"] for item in a_snapshot["items"]] == ["SENT", "SENT"]
    assert [item["payload"] for item in b_snapshot["items"]] == ["B1", "B2"]
    assert [item["status"] for item in b_snapshot["items"]] == ["PENDING", "PENDING"]
    assert [item["status"] for item in c_snapshot["items"]] == ["SENT"]


def test_sent_log_reflects_global_processing_order() -> None:
    client = TestClient(api.app)

    client.post("/queues", json={"name": "Queue A"})
    client.post("/queues", json={"name": "Queue B"})
    client.post("/queues", json={"name": "Queue C"})

    client.post("/queues/Queue B/pause")

    for item in ["A1", "A2"]:
        client.post("/queues/Queue A/items", json={"item": item})
    for item in ["B1", "B2"]:
        client.post("/queues/Queue B/items", json={"item": item})
    client.post("/queues/Queue C/items", json={"item": "C1"})

    client.post("/test/run")

    transport = client.get("/transport/log")
    assert transport.status_code == 200
    entries = transport.json()
    assert [(entry["queue"], entry["item"]) for entry in entries] == [
        ("Queue A", "A1"),
        ("Queue A", "A2"),
        ("Queue C", "C1"),
    ]
    assert all("released_at" in entry for entry in entries)
    assert all(entry["released_at"] == entry["timestamp"] for entry in entries)


def test_generate_test_endpoint_removed_from_main_flow() -> None:
    client = TestClient(api.app)

    response = client.post("/test/generate", json={"queue_count": 2, "items_per_queue": 2})

    assert response.status_code == 404


def test_list_queues_and_static_ui_mount() -> None:
    client = TestClient(api.app)

    client.post("/queues", json={"name": "alpha"})
    client.post("/queues", json={"name": "beta"})
    list_response = client.get("/queues")

    assert list_response.status_code == 200
    names = {queue["name"] for queue in list_response.json()}
    assert names == {"alpha", "beta"}

    ui_response = client.get("/ui")
    assert ui_response.status_code == 200
    assert "Run Test" in ui_response.text
    assert "LOG 1" in ui_response.text
    assert "Activity Log" in ui_response.text
    assert "LOG 2" in ui_response.text
    assert "Sent Items Log" in ui_response.text
    assert "log-scroll-area" in ui_response.text
    assert "activity-log-list" in ui_response.text
    assert "transport-log-list" in ui_response.text
    assert "Generate test queues" not in ui_response.text


def test_not_found_returns_404() -> None:
    client = TestClient(api.app)

    response = client.post("/queues/missing/items", json={"item": "x"})

    assert response.status_code == 404
