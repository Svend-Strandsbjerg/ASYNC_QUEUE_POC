from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from async_integration_foundation.queue_framework import FakeTransport, InMemoryQueueRepository


def print_snapshot(title: str, snapshot: dict) -> None:
    print(f"\n=== {title} ===")
    print(json.dumps(snapshot, indent=2, sort_keys=True))


def run_demo() -> None:
    repository = InMemoryQueueRepository()
    transport = FakeTransport()

    scope = {
        "session_id": "sess-001",
        "user_id": "alice",
        "context_type": "ORDER",
        "context_id": "ORD-9001",
    }

    queue = repository.get_or_create_queue(scope)
    print_snapshot("Step A - Initial snapshot", queue.snapshot())

    queue.pause()
    for index in range(1, 5):
        queue.add_item({"line": index, "description": f"Item {index}"})

    queue.dispatch_all(transport)
    print_snapshot("Step B - Queue paused with accumulated items", queue.snapshot())
    print(f"Sent while paused: {len(transport.sent)}")

    queue.resume()
    queue.dispatch_all(transport)
    print_snapshot("Step C - Queue resumed and dispatched", queue.snapshot())
    print(f"Sent after resume: {len(transport.sent)}")

    queue.dispatch_all(transport)
    print_snapshot("Step D - Second dispatch attempt (no redispatch)", queue.snapshot())
    print(f"Sent after second dispatch: {len(transport.sent)}")
    print("\nTransport sent log:")
    print(json.dumps(transport.sent, indent=2, sort_keys=True))


if __name__ == "__main__":
    run_demo()
