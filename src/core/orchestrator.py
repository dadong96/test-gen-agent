"""Orchestrator — coordinates the 4-agent pipeline with coverage retry loop."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

from config.settings import (
    COVERAGE_THRESHOLD_DEFAULT,
    COVERAGE_THRESHOLD_INCREMENT,
    MAX_COVERAGE_ROUNDS,
)
from src.agents.generator_agent import GeneratorAgent
from src.agents.optimizer_agent import OptimizerAgent
from src.agents.parser_agent import ParserAgent
from src.agents.runner_agent import RunnerAgent
from src.core.ast_parser import parse_java_file
from src.core.llm_client import LLMClient
from src.core.types import (
    CoverageReport,
    LoopState,
    PipelineResult,
    RequirementSpec,
    TestCase,
)
from src.generators.junit_writer import JUnitWriter
from src.utils.file_utils import find_java_files
from src.utils.logger import setup_logger


class Orchestrator:
    """Coordinates the multi-agent test generation pipeline."""

    def __init__(
        self,
        llm: LLMClient,
        max_coverage_rounds: int | None = None,
    ):
        self.llm = llm
        self.max_coverage_rounds = max_coverage_rounds or MAX_COVERAGE_ROUNDS
        self.logger = setup_logger("orchestrator")

        self.parser = ParserAgent(llm)
        self.generator = GeneratorAgent(llm)
        self.optimizer = OptimizerAgent(llm)
        self.runner = RunnerAgent(llm)
        self.writer = JUnitWriter()

    async def run(
        self,
        project_path: Path,
        prd_path: Path,
        swagger_path: Path | None = None,
        coverage_threshold: float = COVERAGE_THRESHOLD_DEFAULT,
        no_run: bool = False,
        dry_run: bool = False,
    ) -> PipelineResult:
        """Execute the full test generation pipeline."""
        self.logger.info("=" * 60)
        self.logger.info("TEST GENERATION PIPELINE — project: %s", project_path)
        self.logger.info("=" * 60)

        result = PipelineResult(target=str(project_path))
        start = time.monotonic()

        try:
            # ── Stage 1: Parse documents ───────────────────────────────
            self.logger.info("[pipeline] Stage 1/4 — Parser")
            parse_result = await self.parser.run(
                prd_path=prd_path,
                swagger_path=swagger_path,
            )
            result.stage_results["parser"] = parse_result

            if parse_result.status != "success":
                result.status = "error"
                result.error = f"Parser failed: {parse_result.error}"
                return result

            spec = parse_result.data

            if dry_run:
                self.logger.info("[pipeline] Dry run — stopping after parse")
                result.status = "dry_run"
                result.duration_seconds = time.monotonic() - start
                return result

            # ── Stage 2: Find and parse Java files ─────────────────────
            self.logger.info("[pipeline] Stage 2 — Finding Java source files")
            java_files = find_java_files(project_path)
            self.logger.info("[pipeline] Found %d Java files", len(java_files))

            if not java_files:
                result.status = "no_sources"
                result.error = "No Java source files found"
                return result

            # ── Stage 3-4: Generate → Optimize → Run loop ─────────────
            all_test_cases: list[TestCase] = []
            all_coverage: list[CoverageReport] = []
            current_threshold = coverage_threshold

            for round_num in range(1, self.max_coverage_rounds + 1):
                self.logger.info(
                    "[pipeline] === Round %d (threshold=%.0f%%) ===",
                    round_num,
                    current_threshold * 100,
                )

                round_tests: list[TestCase] = []
                for java_file in java_files:
                    try:
                        ast_info = parse_java_file(java_file)
                    except Exception as e:
                        self.logger.warning("[pipeline] AST parse failed for %s: %s", java_file, e)
                        continue

                    if not ast_info.methods:
                        continue

                    loop_state = None
                    if round_num > 1 and all_coverage:
                        loop_state = LoopState(
                            round=round_num,
                            coverage_threshold=current_threshold,
                            uncovered_gaps=all_coverage,
                        )

                    gen_result = await self.generator.run(
                        spec=spec,
                        ast_info=ast_info,
                        loop_state=loop_state,
                    )
                    if gen_result.status == "success":
                        round_tests.extend(gen_result.data)

                if not round_tests:
                    self.logger.warning("[pipeline] No tests generated in round %d", round_num)
                    break

                opt_result = await self.optimizer.run(test_cases=round_tests)
                if opt_result.status == "success":
                    round_tests = opt_result.data

                all_test_cases.extend(round_tests)

                self.writer.write_tests(round_tests)

                if no_run:
                    self.logger.info("[pipeline] --no-run: skipping test execution")
                    break

                run_result = await self.runner.run(
                    test_cases=round_tests,
                    project_path=project_path,
                    coverage_threshold=current_threshold,
                )

                if run_result.status != "success":
                    self.logger.error("[pipeline] Runner failed: %s", run_result.error)
                    break

                run_data = run_result.data
                if not run_data["build_success"]:
                    self.logger.warning("[pipeline] Build failed: %s", run_data["error_details"][:200])
                    break

                all_coverage = run_data["coverage_reports"]

                if not run_data["needs_retry"]:
                    self.logger.info("[pipeline] Coverage threshold met — done")
                    break

                current_threshold += COVERAGE_THRESHOLD_INCREMENT
                self.logger.info("[pipeline] Retrying with threshold=%.0f%%", current_threshold * 100)

            result.generated_tests = all_test_cases
            result.coverage_reports = all_coverage
            result.status = "success" if all_test_cases else "no_tests"
            if not all_test_cases:
                result.error = "No tests were successfully generated"

        except Exception as e:
            self.logger.exception("[pipeline] Pipeline failed")
            result.status = "error"
            result.error = str(e)

        result.duration_seconds = time.monotonic() - start
        result.token_summary = self.llm.token_summary()

        self.logger.info("=" * 60)
        self.logger.info("PIPELINE COMPLETE in %.1fs", result.duration_seconds)
        self.logger.info("Generated %d test cases", len(result.generated_tests))
        self.logger.info("Token usage: %s", result.token_summary)
        self.logger.info("=" * 60)

        return result
