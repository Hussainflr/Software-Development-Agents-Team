# Code Generation

Generate complete, runnable application code artifacts that match the focused context and the human manager requirement.

Rules:
- Return full file contents, not fragments.
- Use clear relative paths for every artifact.
- Python files must be valid, compile-ready source with top-level imports, classes, functions, and `app = FastAPI(...)` starting at column 1.
- Do not indent an entire Python file inside JSON strings, Markdown fences, bullets, or explanatory blocks.
- Prefer simple, maintainable implementations over broad scaffolding.
- Include concise comments only where they clarify non-obvious behavior.
- Do not include secrets, credentials, or placeholder API keys.
