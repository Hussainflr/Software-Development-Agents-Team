"""Compatibility entrypoint.

Run with:
    uvicorn app.main:app --reload
"""

from backend.app.main import app

__all__ = ["app"]

