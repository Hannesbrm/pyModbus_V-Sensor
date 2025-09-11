"""HTTP API for interacting with VSensorService without UI."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from service import VSensorService

app = FastAPI(title="VSensor Headless Service")
service = VSensorService(interval=5.0)


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


@app.on_event("shutdown")
def shutdown() -> None:
    """Stop background polling when the service shuts down."""
    service.stop()
