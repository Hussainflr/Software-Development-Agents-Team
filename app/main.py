"""Compatibility entrypoint.

Run with:
    uvicorn app.main:app --reload
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.main import app

__all__ = ["app"]

