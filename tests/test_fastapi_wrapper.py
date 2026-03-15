import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

import async_queue_poc.api as api


@pytest.fixture(autouse=True)
def clear_state() -> None:
    api.service.reset()


def test_run_test_sends_open_queue_items_and_skips_paused_items() -> None:
    client = TestClient(api.app)

    queue_a = client.post("/queues", json={"name": "Queue A"}).json()["queue_id"]
    queue_b = client.post("/queues", json={"name": "Queue B"}).json()["queue_id"]
    queue_c = client.post("/queues", json={"name": "Queue C"}).json()["queue_id"]

    client.post(f"/queues/{queue_b}/pause")

    client.post(f"/queues/{queue_a}/items", json={"item": "A1"})
    client.post(f"/queues/{queue_a}/items", json={"item": "A2"})
    client.post(f"/queues/{queue_b}/items", json={"item": "B1"})
    client.post(f"/queues/{queue_b}/items", json={"item": "B2"})
    client.post(f"/queues/{queue_c}/items", json={"item": "C1"})

    run_response = client.post("/test/run")

    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["processed"] == {"queues": 2, "items": 3}
    assert payload["skipped"] == {"queues": 1, "items": 2}
    assert payload["sent"] == {"queues": 2, "items": 3}

    result_by_queue = {result["queue_id"]: result for result in payload["results"]}
    assert result_by_queue[queue_a]["status"] == "SENT"
    assert [item["payload"] for item in result_by_queue[queue_a]["items_sent"]] == ["A1", "A2"]
    assert result_by_queue[queue_b] == {
        "queue_id": queue_b,
        "queue_name": "Queue B",
        "status": "SKIPPED",
        "reason": "paused",
        "items_sent": [],
        "items_sent_count": 0,
        "pending_items": result_by_queue[queue_b]["pending_items"],
        "remaining_items": 2,
    }
    assert [item["payload"] for item in result_by_queue[queue_b]["pending_items"]] == ["B1", "B2"]
    assert result_by_queue[queue_c]["status"] == "SENT"
    assert [item["payload"] for item in result_by_queue[queue_c]["items_sent"]] == ["C1"]

    a_snapshot = client.get(f"/queues/{queue_a}").json()
    b_snapshot = client.get(f"/queues/{queue_b}").json()
    c_snapshot = client.get(f"/queues/{queue_c}").json()

    assert [item["status"] for item in a_snapshot["items"]] == ["SENT", "SENT"]
    assert [item["payload"] for item in b_snapshot["items"]] == ["B1", "B2"]
    assert [item["status"] for item in b_snapshot["items"]] == ["PENDING", "PENDING"]
    assert [item["status"] for item in c_snapshot["items"]] == ["SENT"]


def test_sent_log_reflects_global_processing_order_with_real_ids() -> None:
    client = TestClient(api.app)

    queue_a = client.post("/queues", json={"name": "Queue A"}).json()["queue_id"]
    queue_b = client.post("/queues", json={"name": "Queue B"}).json()["queue_id"]
    queue_c = client.post("/queues", json={"name": "Queue C"}).json()["queue_id"]

    client.post(f"/queues/{queue_b}/pause")

    a1 = client.post(f"/queues/{queue_a}/items", json={"item": "A1"}).json()["item"]["item_id"]
    a2 = client.post(f"/queues/{queue_a}/items", json={"item": "A2"}).json()["item"]["item_id"]
    client.post(f"/queues/{queue_b}/items", json={"item": "B1"})
    client.post(f"/queues/{queue_b}/items", json={"item": "B2"})
    c1 = client.post(f"/queues/{queue_c}/items", json={"item": "C1"}).json()["item"]["item_id"]

    client.post("/test/run")

    transport = client.get("/transport/log")
    assert transport.status_code == 200
    entries = transport.json()
    assert [(entry["queue_id"], entry["item_id"]) for entry in entries] == [
        (queue_a, a1),
        (queue_a, a2),
        (queue_c, c1),
    ]
    assert all("released_at" in entry for entry in entries)
    assert all(entry["released_at"] == entry["timestamp"] for entry in entries)


def test_generate_test_endpoint_removed_from_main_flow() -> None:
    client = TestClient(api.app)

    response = client.post("/test/generate", json={"queue_count": 2, "items_per_queue": 2})

    assert response.status_code == 404


def test_list_queues_and_static_ui_mount() -> None:
    client = TestClient(api.app)

    queue_alpha = client.post("/queues", json={"name": "alpha"}).json()
    queue_beta = client.post("/queues", json={"name": "beta"}).json()
    list_response = client.get("/queues")

    assert list_response.status_code == 200
    queue_names = {queue["queue_name"] for queue in list_response.json()}
    queue_ids = {queue["queue_id"] for queue in list_response.json()}
    assert queue_names == {"alpha", "beta"}
    assert queue_ids == {queue_alpha["queue_id"], queue_beta["queue_id"]}

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


def test_ui_script_renders_newest_log_entries_first_with_structured_sent_item_cards() -> None:
    client = TestClient(api.app)

    response = client.get("/ui/app.js")

    assert response.status_code == 200
    script = response.text
    assert "container.insertBefore(element, container.firstChild);" in script
    assert 'class="log-entry-header">Item ID: ${entry.item_id}</div>' in script
    assert "<div>Queue ID: ${entry.queue_id}</div>" in script
    assert "<div>Released: ${formatReleasedAt(releasedAt)}</div>" in script
    assert "Run Test completed: processed=${payload.processed.queues}" in script
    assert "(${payload.processed.items} items)" in script
