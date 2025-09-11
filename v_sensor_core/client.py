"""Compatibility wrapper exporting the high level :class:`VSensorClient`.

The real implementation lives in the project root module :mod:`client`.  This
wrapper simply re-exports the class so existing imports continue to work::

    from v_sensor_core.client import VSensorClient

"""

from __future__ import annotations

from client import VSensorClient

__all__ = ["VSensorClient"]
