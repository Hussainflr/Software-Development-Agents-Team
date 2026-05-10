import pytest

from tools.artifact_sanitizer import ArtifactValidationError, normalize_artifact


def test_python_artifact_removes_accidental_indented_module_body():
    source = """from datetime import datetime
        from uuid import uuid4

        from fastapi import FastAPI

        app = FastAPI()


        @app.get("/health")
        def health():
            return {"status": "ok", "time": datetime.utcnow().isoformat()}
"""

    normalized = normalize_artifact("generated_backend/main.py", source)

    assert "from uuid import uuid4\n" in normalized
    assert "\nfrom fastapi import FastAPI\n" in normalized
    assert "\ndef health():\n    return" in normalized
    compile(normalized, "generated_backend/main.py", "exec")


def test_python_artifact_strips_markdown_fence():
    source = """```python
        print("ok")
```"""

    assert normalize_artifact("script.py", source) == 'print("ok")\n'


def test_invalid_python_artifact_raises_validation_error():
    with pytest.raises(ArtifactValidationError):
        normalize_artifact("generated_backend/main.py", "def broken(:\n    pass")
