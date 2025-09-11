"""Smoke tests for command line interfaces."""

from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_client_cli_runs() -> None:
    subprocess.run([sys.executable, str(ROOT / "client.py"), "--help"], check=True)


def test_codec_cli_runs() -> None:
    subprocess.run([sys.executable, str(ROOT / "codec.py"), "--help"], check=True)
