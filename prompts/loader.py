from functools import lru_cache
from pathlib import Path


PROMPT_DIR = Path(__file__).resolve().parent


@lru_cache
def load_prompt(name: str) -> str:
    """Load a prompt template from disk so prompt text stays out of agent code."""

    path = PROMPT_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {name}")
    return path.read_text(encoding="utf-8").strip()
