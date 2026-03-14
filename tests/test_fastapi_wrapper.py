import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

import async_queue_poc.api as api


@pytest.fixture(autouse=True)
def clear_state() -> None:
    api.service.reset()


def test_run_test_skips_paused_queues_and_sends_open_queue_items() -> None:
    client = TestClient(api.app)

    client.post("/queues", json={"name": "A"})
    client.post("/queues", json={"name": "B"})
    client.post("/queues/A/pause")

    client.post("/queues/A/items", json={"item": "a1"})
    client.post("/queues/A/items", json={"item": "a2"})
    client.post("/queues/B/items", json={"item": "b1"})

    run_response = client.post("/test/run")

    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["queues_processed"] == 2
    assert payload["queues_skipped"] == 1
    assert payload["items_sent"] == 1

    result_by_queue = {result["queue"]: result for result in payload["results"]}
    assert result_by_queue["A"]["status"] == "SKIPPED"
    assert result_by_queue["A"]["reason"] == "paused"
    assert result_by_queue["B"]["status"] == "SENT"
    assert result_by_queue["B"]["items_sent"] == 1

    a_snapshot = client.get("/queues/A").json()
    b_snapshot = client.get("/queues/B").json()

    assert [item["status"] for item in a_snapshot["items"]] == ["PENDING", "PENDING"]
    assert [item["status"] for item in b_snapshot["items"]] == ["SENT"]


def test_multiple_queues_processed_in_single_run_and_sent_log_updated() -> None:
    client = TestClient(api.app)

    client.post("/test/generate", json={"queue_count": 4, "items_per_queue": 1, "paused_queue_indices": [0, 3]})

    run_response = client.post("/test/run")

    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["queues_processed"] == 4
    assert payload["queues_skipped"] == 2
    assert payload["items_sent"] == 2

    transport = client.get("/transport/log")
    assert transport.status_code == 200
    entries = transport.json()
    assert len(entries) == 2
    assert {entry["queue"] for entry in entries} == {"Queue-2", "Queue-3"}


def test_dispatch_endpoint_kept_as_debug_action() -> None:
    client = TestClient(api.app)

    client.post("/queues", json={"name": "demo"})
    client.post("/queues/demo/items", json={"item": "item1"})

    first_dispatch = client.post("/queues/demo/dispatch")
    second_dispatch = client.post("/queues/demo/dispatch")

    assert first_dispatch.status_code == 200
    assert second_dispatch.status_code == 200
    assert first_dispatch.json()["dispatched_item"] == "item1"
    assert second_dispatch.json()["dispatched_item"] is None


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


def test_not_found_returns_404() -> None:
    client = TestClient(api.app)

    response = client.post("/queues/missing/items", json={"item": "x"})

    assert response.status_code == 404
