from pathlib import Path


class UnsafeArtifactPath(ValueError):
    """Raised when an agent tries to write outside the generated run folder."""


def safe_artifact_path(base_dir: Path, relative_path: str) -> Path:
    target = (base_dir / relative_path).resolve()
    root = base_dir.resolve()
    if root != target and root not in target.parents:
        raise UnsafeArtifactPath(f"Artifact path escapes run directory: {relative_path}")
    return target


def write_artifacts(base_dir: Path, artifacts: dict[str, str]) -> list[Path]:
    """Persist generated artifacts to disk under a single run directory."""

    written: list[Path] = []
    base_dir.mkdir(parents=True, exist_ok=True)
    for relative_path, content in artifacts.items():
        target = safe_artifact_path(base_dir, relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        if target.suffix == ".sh":
            target.chmod(0o755)
        written.append(target)
    return written
