"""HTTP API for interacting with VSensorService without UI."""

from __future__ import annotations

import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from service import VSensorService

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
INTERVAL = float(os.getenv("INTERVAL", "5.0"))
_stale_after = os.getenv("STALE_AFTER")
STALE_AFTER = float(_stale_after) if _stale_after is not None else None

app = FastAPI(title="VSensor Headless Service")
service = VSensorService(interval=INTERVAL, stale_after=STALE_AFTER)


class RegisterValue(BaseModel):
    value: int | float


@app.get("/registers/{name}")
def read_register(name: str) -> RegisterValue:
    """Return the current value of ``name``."""
    value = service.read_register(name)
    if value is None:
        raise HTTPException(status_code=404, detail="Register not found or unreadable")
    return RegisterValue(value=value)


@app.get("/registers")
def read_all() -> dict[str, int | float | None]:
    """Return values for all registers."""
    return service.read_all()


@app.post("/registers/{name}")
def write_register(name: str, payload: RegisterValue) -> RegisterValue:
    """Write a new value to ``name``."""
    ok = service.write_register(name, payload.value)
    if not ok:
        raise HTTPException(status_code=500, detail="Write failed")
    return RegisterValue(value=payload.value)


@app.get("/healthz")
def healthz() -> dict[str, int | float | bool | None]:
    """Return service health and statistics."""
    return {
        "connected": service.last_poll_ok(),
        "last_success_ts": service.last_success_ts,
        "poll_interval": service.poll_interval,
        "stale_after": service.stale_after,
        "polls_total": service.polls_total,
        "errors_total": service.errors_total,
        "uptime": service.uptime,
    }


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    """Return metrics in a simple text format."""
    data = healthz()
    lines = [f"{k} {v}" for k, v in data.items()]
    return PlainTextResponse("\n".join(lines))


@app.on_event("shutdown")
def shutdown() -> None:
    """Stop background polling when the service shuts down."""
    service.stop()


def main() -> None:
    """Run the API using ``uvicorn``."""
    import uvicorn

    try:
        uvicorn.run(app, host=HOST, port=PORT)
    finally:
        service.stop()
