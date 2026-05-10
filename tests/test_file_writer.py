import pytest

from tools.file_writer import UnsafeArtifactPath, safe_artifact_path, write_artifacts


def test_write_artifacts_under_run_dir(tmp_path):
    written = write_artifacts(tmp_path, {"src/app.py": "print('ok')"})

    assert written[0].read_text(encoding="utf-8") == "print('ok')\n"


def test_safe_artifact_path_blocks_traversal(tmp_path):
    with pytest.raises(UnsafeArtifactPath):
        safe_artifact_path(tmp_path, "../outside.py")
