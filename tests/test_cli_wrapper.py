from async_queue_poc.cli import QueueController


def test_cli_controller_supports_full_manual_flow():
    controller = QueueController()

    created = controller.create_queue("orders")
    queue_snapshot = created["queue"]
    assert queue_snapshot["name"] == "orders"
    assert queue_snapshot["queue_id"]

    controller.add_item("orders", "order-1")
    controller.add_item("orders", "order-2")

    controller.pause_queue("orders")
    paused_dispatch = controller.dispatch("orders")
    assert paused_dispatch["dispatched_item"] is None

    controller.resume_queue("orders")
    first_dispatch = controller.dispatch("orders")
    assert first_dispatch["dispatched_item"]["payload"] == "order-1"
    assert first_dispatch["dispatched_item"]["item_id"]

    snapshot = controller.show_snapshot("orders")
    pending_payloads = [item["payload"] for item in snapshot["queue"]["pending_items"]]
    assert pending_payloads == ["order-2"]
