from __future__ import annotations

import argparse
import shlex
from dataclasses import asdict
from typing import Any

from .domain import Queue


class QueueController:
    def __init__(self):
        self._queues: dict[str, Queue] = {}

    def _get_queue(self, name: str) -> Queue | None:
        return self._queues.get(name)

    def create_queue(self, name: str) -> dict[str, Any]:
        if name in self._queues:
            return {"error": f"Queue '{name}' already exists."}
        self._queues[name] = Queue(name)
        return {"queue": asdict(self._queues[name].snapshot())}

    def pause_queue(self, name: str) -> dict[str, Any]:
        queue = self._get_queue(name)
        if not queue:
            return {"error": f"Queue '{name}' not found."}
        queue.pause()
        return {"queue": asdict(queue.snapshot())}

    def resume_queue(self, name: str) -> dict[str, Any]:
        queue = self._get_queue(name)
        if not queue:
            return {"error": f"Queue '{name}' not found."}
        queue.resume()
        return {"queue": asdict(queue.snapshot())}

    def add_item(self, name: str, item: str) -> dict[str, Any]:
        queue = self._get_queue(name)
        if not queue:
            return {"error": f"Queue '{name}' not found."}
        queue.add_item(item)
        return {"queue": asdict(queue.snapshot())}

    def dispatch(self, name: str) -> dict[str, Any]:
        queue = self._get_queue(name)
        if not queue:
            return {"error": f"Queue '{name}' not found."}
        item = queue.dispatch()
        return {"dispatched_item": asdict(item) if item is not None else None, "queue": asdict(queue.snapshot())}

    def show_snapshot(self, name: str) -> dict[str, Any]:
        queue = self._get_queue(name)
        if not queue:
            return {"error": f"Queue '{name}' not found."}
        return {"queue": asdict(queue.snapshot())}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="queue-cli", description="Interactive queue POC CLI")
    subparsers = parser.add_subparsers(dest="command")

    for command in ["create-queue", "pause-queue", "resume-queue", "dispatch", "show-snapshot"]:
        cmd = subparsers.add_parser(command)
        cmd.add_argument("name")

    add_item = subparsers.add_parser("add-item")
    add_item.add_argument("name")
    add_item.add_argument("item")

    return parser


def _execute_command(controller: QueueController, argv: list[str]) -> dict[str, Any]:
    parser = _build_parser()
    parsed = parser.parse_args(argv)

    handlers = {
        "create-queue": lambda: controller.create_queue(parsed.name),
        "pause-queue": lambda: controller.pause_queue(parsed.name),
        "resume-queue": lambda: controller.resume_queue(parsed.name),
        "dispatch": lambda: controller.dispatch(parsed.name),
        "show-snapshot": lambda: controller.show_snapshot(parsed.name),
        "add-item": lambda: controller.add_item(parsed.name, parsed.item),
    }

    handler = handlers.get(parsed.command)
    if handler is None:
        return {"error": "Unknown command."}
    return handler()


def main() -> None:
    print("Queue CLI demo. Enter commands (or 'exit').")
    controller = QueueController()
    while True:
        raw = input("queue> ").strip()
        if raw in {"exit", "quit"}:
            print("Goodbye")
            return
        if not raw:
            continue
        result = _execute_command(controller, shlex.split(raw))
        print(result)


if __name__ == "__main__":
    main()
