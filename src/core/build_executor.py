"""Maven/Gradle build executor via subprocess."""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from src.utils.file_utils import detect_build_tool
from src.utils.logger import setup_logger

logger = setup_logger("build_executor")


@dataclass
class BuildResult:
    success: bool
    stdout: str
    stderr: str
    duration: float


class BuildExecutor:
    """Runs Maven or Gradle tests and returns structured results."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.build_tool = detect_build_tool(project_path)

    def run_tests(self, test_filter: str | None = None) -> BuildResult:
        """Execute tests and return the result."""
        if self.build_tool is None:
            return BuildResult(
                success=False,
                stdout="",
                stderr="No pom.xml or build.gradle found in project path.",
                duration=0.0,
            )

        if self.build_tool == "maven":
            return self._run_maven(test_filter)
        else:
            return self._run_gradle(test_filter)

    def _run_maven(self, test_filter: str | None = None) -> BuildResult:
        cmd = ["mvn", "test", "-q", "-f", str(self.project_path / "pom.xml")]
        if test_filter:
            cmd.extend(["-Dtest=" + test_filter])
        return self._execute(cmd)

    def _run_gradle(self, test_filter: str | None = None) -> BuildResult:
        cmd = ["gradle", "test", "-q", "-p", str(self.project_path)]
        if test_filter:
            cmd.extend(["--tests", test_filter])
        return self._execute(cmd)

    def _execute(self, cmd: list[str]) -> BuildResult:
        logger.info("Executing: %s", " ".join(cmd))
        start = time.monotonic()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=self.project_path,
            )
            duration = time.monotonic() - start
            return BuildResult(
                success=proc.returncode == 0,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration=duration,
            )
        except subprocess.TimeoutExpired:
            return BuildResult(
                success=False,
                stdout="",
                stderr="Build timed out after 300 seconds",
                duration=300.0,
            )
        except FileNotFoundError as e:
            return BuildResult(
                success=False,
                stdout="",
                stderr=f"Build tool not found: {e}",
                duration=0.0,
            )
