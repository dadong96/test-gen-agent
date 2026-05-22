"""File I/O helpers."""

from __future__ import annotations

from pathlib import Path

from config.settings import EXCLUDE_DIRS, JAVA_EXTENSIONS


def read_text(path: Path) -> str:
    """Read a text file and return its contents."""
    return path.read_text(encoding="utf-8")


def find_java_files(project_path: Path, max_files: int = 50) -> list[Path]:
    """Find all .java source files under a project, excluding build dirs."""
    java_files = []
    for p in project_path.rglob("*.java"):
        # Skip excluded directories
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        # Skip test files — we generate those
        if "src/test" in str(p):
            continue
        java_files.append(p)
        if len(java_files) >= max_files:
            break
    return sorted(java_files)


def detect_build_tool(project_path: Path) -> str | None:
    """Detect whether the project uses Maven or Gradle."""
    if (project_path / "pom.xml").exists():
        return "maven"
    if (project_path / "build.gradle").exists() or (project_path / "build.gradle.kts").exists():
        return "gradle"
    return None


def write_text(path: Path, content: str) -> None:
    """Write text to a file, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
