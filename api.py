"""Common protocol for V-Sensor client implementations."""

from __future__ import annotations

from typing import Dict, Iterable, Optional, Protocol


class VSensorAPI(Protocol):
    """Protocol describing the V-Sensor client/service API."""

    def read_register(self, name: str) -> Optional[int | float]:
        """Read a single register value."""
        ...

    def write_register(self, name: str, value: int | float) -> bool:
        """Write a register value."""
        ...

    def read_all(self, registers: Iterable[str] | None = None) -> Dict[str, Optional[int | float]]:
        """Read multiple registers at once."""
        ...
