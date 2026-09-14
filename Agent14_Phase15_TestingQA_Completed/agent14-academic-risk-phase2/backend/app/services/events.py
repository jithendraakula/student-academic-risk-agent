"""Lightweight SSE broker for single-instance deployments."""
from __future__ import annotations

import asyncio
import json
from collections import defaultdict

_subscribers: dict[str, set[asyncio.Queue[str]]] = defaultdict(set)


def publish_case_event(payload: dict) -> None:
    message = f"event: case-work\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n"
    for role, queues in list(_subscribers.items()):
        for queue in list(queues):
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                    queue.put_nowait(message)
                except Exception:
                    pass


def subscribe(role: str) -> tuple[asyncio.Queue[str], callable]:
    queue: asyncio.Queue[str] = asyncio.Queue(maxsize=10)
    _subscribers[role].add(queue)
    def close() -> None:
        _subscribers.get(role, set()).discard(queue)
    return queue, close
