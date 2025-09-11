"""Background service for polling V-Sensor registers."""

from __future__ import annotations

import logging
import threading
import time
from enum import Enum
from typing import Any, Dict, Iterable, Optional

from client import VSensorClient
from registers import BY_NAME

LOGGER = logging.getLogger(__name__)


class Quality(Enum):
    """Quality indicator for cached register values."""

    OK = "OK"
    STALE = "STALE"
    ERROR = "ERROR"


class VSensorService:
    """Poll registers from a :class:`VSensorClient` in the background."""

    def __init__(
        self,
        *,
        registers: Optional[Iterable[str]] = None,
        interval: float = 5.0,
        stale_after: float | None = None,
        client: Optional[VSensorClient] = None,
        **client_kwargs: Any,
    ) -> None:
        """Create the service and start the polling thread.

        Parameters
        ----------
        registers:
            Iterable of register names to poll. If ``None`` all registers in
            :data:`registers.BY_NAME` are used.
        interval:
            Polling interval in seconds.
        stale_after:
            Age in seconds after which a value is considered stale. Defaults to
            ``2 * interval`` when ``None``.
        client:
            Optional :class:`VSensorClient` instance. When omitted a new client is
            created using ``client_kwargs`` and :meth:`VSensorClient.connect` is
            called.
        client_kwargs:
            Additional keyword arguments forwarded to :class:`VSensorClient` when
            ``client`` is ``None``.
        """

        if registers is None:
            self._registers = list(BY_NAME.keys())
        else:
            for name in registers:
                if name not in BY_NAME:
                    raise KeyError(f"Unknown register: {name}")
            self._registers = list(registers)

        self._interval = interval
        self._stale_after = stale_after if stale_after is not None else interval * 2

        self._client = client or VSensorClient(**client_kwargs)
        if client is None:
            try:
                self._client.connect()
            except Exception as exc:  # pragma: no cover - defensive
                LOGGER.error("Failed to connect: %s", exc)

        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------
    def _poll_loop(self) -> None:
        while self._running:
            for name in self._registers:
                try:
                    value = self._client.read_register(name)
                except Exception as exc:  # pragma: no cover - defensive
                    LOGGER.error("Polling %s failed: %s", name, exc)
                    value = None
                quality = Quality.OK if value is not None else Quality.ERROR
                with self._lock:
                    self._cache[name] = {
                        "value": value,
                        "timestamp": time.time(),
                        "quality": quality,
                    }
            time.sleep(self._interval)

    # ------------------------------------------------------------------
    def stop(self) -> None:
        """Stop the background thread and close the client."""
        self._running = False
        self._thread.join(timeout=self._interval)
        try:
            self._client.close()
        except Exception:  # pragma: no cover - defensive
            pass

    close = stop  # alias

    # ------------------------------------------------------------------
    def _apply_stale(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        if time.time() - entry["timestamp"] > self._stale_after:
            entry = dict(entry)
            entry["quality"] = Quality.STALE
        return entry

    def read_register(self, name: str) -> Optional[int | float]:
        """Return the cached value for ``name``."""
        with self._lock:
            entry = self._cache.get(name)
        if entry is None:
            return None
        entry = self._apply_stale(entry)
        if entry["quality"] is Quality.ERROR:
            return None
        return entry["value"]

    def read_all(self) -> Dict[str, Optional[int | float]]:
        """Return cached values for all registers."""
        with self._lock:
            items = {k: dict(v) for k, v in self._cache.items()}
        result: Dict[str, Optional[int | float]] = {}
        for name, entry in items.items():
            entry = self._apply_stale(entry)
            result[name] = None if entry["quality"] is Quality.ERROR else entry["value"]
        return result

    def write_register(self, name: str, value: int | float) -> bool:
        """Write a register and update the cache on success."""
        try:
            ok = self._client.write_register(name, value)
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.error("Write %s failed: %s", name, exc)
            ok = False
        if ok:
            with self._lock:
                self._cache[name] = {
                    "value": value,
                    "timestamp": time.time(),
                    "quality": Quality.OK,
                }
        return ok

    # ------------------------------------------------------------------
    def status(self, name: str) -> Optional[Quality]:
        """Return the :class:`Quality` for ``name``."""
        with self._lock:
            entry = self._cache.get(name)
        if entry is None:
            return None
        entry = self._apply_stale(entry)
        return entry["quality"]
