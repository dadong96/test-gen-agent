"""Tests for Runner Agent."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.agents.runner_agent import RunnerAgent
from src.core.types import BuildResult, CoverageReport, TestCase


@pytest.fixture
def mock_llm():
    return MagicMock()


@pytest.fixture
def sample_tests():
    return [
        TestCase(id="TC-001", target_class="OrderService", target_method="createOrder",
                 scenario_type="normal", priority="P0", java_code="    @Test void t1() {}"),
    ]


@pytest.fixture
def mock_build_success():
    with patch("src.agents.runner_agent.BuildExecutor") as MockExec:
        instance = MockExec.return_value
        instance.build_tool = "maven"
        instance.run_tests.return_value = BuildResult(
            success=True, stdout="BUILD SUCCESS", stderr="", duration=10.0
        )
        yield instance


@pytest.fixture
def mock_build_failure():
    with patch("src.agents.runner_agent.BuildExecutor") as MockExec:
        instance = MockExec.return_value
        instance.build_tool = "maven"
        instance.run_tests.return_value = BuildResult(
            success=False, stdout="", stderr="COMPILATION ERROR: cannot find symbol", duration=5.0
        )
        yield instance


@pytest.mark.asyncio
async def test_runner_success(mock_llm, mock_build_success, tmp_path, sample_tests):
    agent = RunnerAgent(mock_llm)
    result = await agent.run(
        test_cases=sample_tests,
        project_path=tmp_path,
        coverage_threshold=0.70,
    )
    assert result.status == "success"
    assert result.data["build_success"] is True


@pytest.mark.asyncio
async def test_runner_build_failure(mock_llm, mock_build_failure, tmp_path, sample_tests):
    agent = RunnerAgent(mock_llm)
    result = await agent.run(
        test_cases=sample_tests,
        project_path=tmp_path,
        coverage_threshold=0.70,
    )
    assert result.status == "success"
    assert result.data["build_success"] is False
    assert result.data.get("needs_fix") is True


@pytest.mark.asyncio
async def test_runner_coverage_below_threshold(mock_llm, tmp_path, sample_tests):
    with patch("src.agents.runner_agent.BuildExecutor") as MockExec:
        MockExec.return_value.build_tool = "maven"
        MockExec.return_value.run_tests.return_value = BuildResult(
            success=True, stdout="BUILD SUCCESS", stderr="", duration=10.0
        )
        with patch("src.agents.runner_agent.parse_jacoco_csv") as mock_parse:
            mock_parse.return_value = [
                CoverageReport(
                    target_class="OrderService", method="*",
                    line_coverage=0.65, branch_coverage=0.50,
                    uncovered_lines=[10, 11], uncovered_branches=[],
                ),
            ]
            agent = RunnerAgent(mock_llm)
            result = await agent.run(
                test_cases=sample_tests,
                project_path=tmp_path,
                coverage_threshold=0.70,
            )
    assert result.data["needs_retry"] is True
    assert len(result.data["coverage_reports"]) > 0
