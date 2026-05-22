"""Tests for the Orchestrator pipeline coordinator."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.orchestrator import Orchestrator
from src.core.types import (
    AgentResult,
    BuildResult,
    CoverageReport,
    JavaClassInfo,
    MethodInfo,
    PipelineResult,
    RequirementSpec,
    TestCase,
)


@pytest.fixture
def mock_llm():
    return MagicMock()


def _make_parser_result():
    return AgentResult(
        agent_name="parser", status="success",
        data=RequirementSpec(),
    )


def _make_generator_result():
    return AgentResult(
        agent_name="generator", status="success",
        data=[TestCase(id="TC-001", target_class="S", target_method="m",
                       scenario_type="normal", priority="P0", java_code="    @Test void t() {}")],
    )


def _make_optimizer_result():
    return AgentResult(
        agent_name="optimizer", status="success",
        data=[TestCase(id="TC-001", target_class="S", target_method="m",
                       scenario_type="normal", priority="P0", java_code="    @Test void t() {}")],
    )


def _make_runner_result(coverage=0.85, needs_retry=False):
    return AgentResult(
        agent_name="runner", status="success",
        data={
            "build_success": True,
            "needs_fix": False,
            "error_details": "",
            "coverage_reports": [
                CoverageReport(target_class="S", method="*",
                               line_coverage=coverage, branch_coverage=coverage),
            ],
            "needs_retry": needs_retry,
        },
    )


@pytest.mark.asyncio
async def test_orchestrator_runs_pipeline(mock_llm, tmp_path):
    orchestrator = Orchestrator(mock_llm)

    orchestrator.parser.run = AsyncMock(return_value=_make_parser_result())
    orchestrator.generator.run = AsyncMock(return_value=_make_generator_result())
    orchestrator.optimizer.run = AsyncMock(return_value=_make_optimizer_result())
    orchestrator.runner.run = AsyncMock(return_value=_make_runner_result())

    with patch("src.core.orchestrator.find_java_files", return_value=[tmp_path / "S.java"]):
        with patch("src.core.orchestrator.parse_java_file") as mock_ast:
            mock_ast.return_value = JavaClassInfo(
                class_name="S", methods=[MethodInfo(name="m", is_public=True)]
            )
            result = await orchestrator.run(
                project_path=tmp_path,
                prd_path=tmp_path / "prd.md",
                swagger_path=None,
            )

    assert result.status == "success"
    assert len(result.generated_tests) > 0


@pytest.mark.asyncio
async def test_orchestrator_coverage_retry(mock_llm, tmp_path):
    orchestrator = Orchestrator(mock_llm, max_coverage_rounds=2)

    run_count = 0

    async def mock_runner_run(**kwargs):
        nonlocal run_count
        run_count += 1
        if run_count == 1:
            return _make_runner_result(coverage=0.50, needs_retry=True)
        return _make_runner_result(coverage=0.80, needs_retry=False)

    orchestrator.parser.run = AsyncMock(return_value=_make_parser_result())
    orchestrator.generator.run = AsyncMock(return_value=_make_generator_result())
    orchestrator.optimizer.run = AsyncMock(return_value=_make_optimizer_result())
    orchestrator.runner.run = AsyncMock(side_effect=mock_runner_run)

    with patch("src.core.orchestrator.find_java_files", return_value=[tmp_path / "S.java"]):
        with patch("src.core.orchestrator.parse_java_file") as mock_ast:
            mock_ast.return_value = JavaClassInfo(
                class_name="S", methods=[MethodInfo(name="m", is_public=True)]
            )
            result = await orchestrator.run(
                project_path=tmp_path,
                prd_path=tmp_path / "prd.md",
                swagger_path=None,
                coverage_threshold=0.70,
            )

    assert result.status == "success"
    assert run_count == 2
