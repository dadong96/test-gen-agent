"""Tests for Maven/Gradle build executor."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.build_executor import BuildExecutor, BuildResult


def test_detect_maven(tmp_path):
    (tmp_path / "pom.xml").write_text("<project/>")
    executor = BuildExecutor(tmp_path)
    assert executor.build_tool == "maven"


def test_detect_gradle(tmp_path):
    (tmp_path / "build.gradle").write_text("plugins {}")
    executor = BuildExecutor(tmp_path)
    assert executor.build_tool == "gradle"


def test_no_build_tool(tmp_path):
    executor = BuildExecutor(tmp_path)
    assert executor.build_tool is None


def test_build_result_success():
    result = BuildResult(success=True, stdout="BUILD SUCCESS", stderr="", duration=10.0)
    assert result.success is True


def test_build_result_failure():
    result = BuildResult(success=False, stdout="", stderr="COMPILATION ERROR", duration=5.0)
    assert result.success is False
    assert "COMPILATION ERROR" in result.stderr


@patch("src.core.build_executor.subprocess.run")
def test_maven_test_command(mock_run, tmp_path):
    (tmp_path / "pom.xml").write_text("<project/>")
    mock_run.return_value = MagicMock(returncode=0, stdout="BUILD SUCCESS", stderr="")

    executor = BuildExecutor(tmp_path)
    result = executor.run_tests()

    assert result.success is True
    args = mock_run.call_args[0][0]
    assert "mvn" in args[0] or "mvn" in " ".join(args)


@patch("src.core.build_executor.subprocess.run")
def test_gradle_test_command(mock_run, tmp_path):
    (tmp_path / "build.gradle").write_text("plugins {}")
    mock_run.return_value = MagicMock(returncode=0, stdout="BUILD SUCCESSFUL", stderr="")

    executor = BuildExecutor(tmp_path)
    result = executor.run_tests()

    assert result.success is True
