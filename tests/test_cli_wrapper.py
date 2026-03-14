from async_queue_poc.cli import QueueController


def test_cli_controller_supports_full_manual_flow():
    controller = QueueController()

    created = controller.create_queue("orders")
    assert created["queue"]["name"] == "orders"

    controller.add_item("orders", "order-1")
    controller.add_item("orders", "order-2")

    controller.pause_queue("orders")
    paused_dispatch = controller.dispatch("orders")
    assert paused_dispatch["dispatched_item"] is None

    controller.resume_queue("orders")
    first_dispatch = controller.dispatch("orders")
    assert first_dispatch["dispatched_item"] == "order-1"

    snapshot = controller.show_snapshot("orders")
    assert snapshot["queue"]["pending_items"] == ["order-2"]
