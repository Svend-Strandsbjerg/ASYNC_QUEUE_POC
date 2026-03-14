import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

import async_queue_poc.api as api


@pytest.fixture(autouse=True)
def clear_state() -> None:
    api.service.reset()


def test_full_queue_flow_and_transport_log() -> None:
    client = TestClient(api.app)

    created = client.post("/queues", json={"name": "demo"})
    assert created.status_code == 200
    assert created.json()["state"] == "OPEN"

    paused = client.post("/queues/demo/pause")
    assert paused.status_code == 200
    assert paused.json()["state"] == "PAUSED"

    add_first = client.post("/queues/demo/items", json={"item": "item1"})
    add_second = client.post("/queues/demo/items", json={"item": "item2"})
    assert add_first.status_code == 200
    assert add_second.status_code == 200

    snapshot = client.get("/queues/demo")
    assert snapshot.status_code == 200
    assert snapshot.json()["items"] == ["item1", "item2"]

    paused_dispatch = client.post("/queues/demo/dispatch")
    assert paused_dispatch.status_code == 200
    assert paused_dispatch.json()["dispatched_item"] is None

    resumed = client.post("/queues/demo/resume")
    assert resumed.status_code == 200
    assert resumed.json()["state"] == "OPEN"

    first_dispatch = client.post("/queues/demo/dispatch")
    second_dispatch = client.post("/queues/demo/dispatch")
    third_dispatch = client.post("/queues/demo/dispatch")

    assert first_dispatch.json()["dispatched_item"] == "item1"
    assert second_dispatch.json()["dispatched_item"] == "item2"
    assert third_dispatch.json()["dispatched_item"] is None

    transport = client.get("/transport/log")
    assert transport.status_code == 200
    entries = transport.json()
    assert len(entries) == 2
    assert entries[0]["queue"] == "demo"
    assert entries[0]["item"] == "item1"


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
    assert "Async Queue POC" in ui_response.text


def test_not_found_returns_404() -> None:
    client = TestClient(api.app)

    response = client.post("/queues/missing/items", json={"item": "x"})

    assert response.status_code == 404
