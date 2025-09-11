"""Tests for the VSensorService."""

from __future__ import annotations

import pathlib
import sys
import time
from typing import Any, Dict

# Ensure project root on path
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from service import Quality, VSensorService


class FakeClient:
    """Simple stand-in for :class:`VSensorClient` used in tests."""

    def __init__(self, values: Dict[str, Any], errors: set[str] | None = None) -> None:
        self.values = values
        self.errors = errors or set()
        self.writes: list[tuple[str, Any]] = []

    def connect(self) -> bool:  # pragma: no cover - trivial
        return True

    def close(self) -> None:  # pragma: no cover - trivial
        pass

    def read_register(self, name: str) -> Any:
        if name in self.errors:
            return None
        return self.values.get(name)

    def write_register(self, name: str, value: Any) -> bool:
        self.values[name] = value
        self.writes.append((name, value))
        return True


def test_poll_and_read() -> None:
    client = FakeClient({"heartbeat": 5})
    service = VSensorService(
        client=client, registers=["heartbeat"], interval=0.05, stale_after=0.2
    )
    time.sleep(0.1)
    assert service.read_register("heartbeat") == 5
    assert service.status("heartbeat") is Quality.OK
    service.stop()


def test_stale_detection() -> None:
    client = FakeClient({"heartbeat": 1})
    service = VSensorService(
        client=client, registers=["heartbeat"], interval=0.05, stale_after=0.1
    )
    time.sleep(0.1)
    service.stop()
    time.sleep(0.15)
    assert service.status("heartbeat") is Quality.STALE


def test_error_quality() -> None:
    client = FakeClient({}, errors={"heartbeat"})
    service = VSensorService(
        client=client, registers=["heartbeat"], interval=0.05, stale_after=0.2
    )
    time.sleep(0.1)
    assert service.read_register("heartbeat") is None
    assert service.status("heartbeat") is Quality.ERROR
    service.stop()


def test_write_updates_cache() -> None:
    client = FakeClient({"heartbeat": 1})
    service = VSensorService(
        client=client, registers=["heartbeat"], interval=0.05, stale_after=0.2
    )
    time.sleep(0.1)
    assert service.write_register("heartbeat", 2)
    time.sleep(0.1)
    assert service.read_register("heartbeat") == 2
    service.stop()


def test_read_all() -> None:
    client = FakeClient({"heartbeat": 5, "mode": 3})
    service = VSensorService(
        client=client, registers=["heartbeat", "mode"], interval=0.05, stale_after=0.2
    )
    time.sleep(0.1)
    data = service.read_all()
    assert set(data) == {"heartbeat", "mode"}
    assert data["heartbeat"] == 5
    assert service.status("heartbeat") is Quality.OK
    service.stop()
