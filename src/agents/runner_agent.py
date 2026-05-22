"""Runner Agent — executes tests, parses coverage, and triggers retry loops."""

from __future__ import annotations

from pathlib import Path

from src.agents.base import AgentResult, BaseAgent
from src.core.build_executor import BuildExecutor
from src.core.coverage_parser import parse_jacoco_csv
from src.core.types import CoverageReport, TestCase


class RunnerAgent(BaseAgent):
    name = "runner"

    async def run(
        self,
        test_cases: list[TestCase],
        project_path: Path,
        coverage_threshold: float = 0.70,
    ) -> AgentResult:
        try:
            executor = BuildExecutor(project_path)

            if executor.build_tool is None:
                return self._error(
                    "No pom.xml or build.gradle found. Cannot execute tests."
                )

            self.logger.info("[runner] Executing %s tests...", executor.build_tool)
            build_result = executor.run_tests()

            if not build_result.success:
                self.logger.warning("[runner] Build failed: %s", build_result.stderr[:200])
                return self._success({
                    "build_success": False,
                    "needs_fix": True,
                    "error_details": build_result.stderr,
                    "coverage_reports": [],
                    "needs_retry": False,
                })

            coverage_reports = self._find_and_parse_coverage(project_path)

            needs_retry = False
            if coverage_reports:
                avg_branch = sum(r.branch_coverage for r in coverage_reports) / len(coverage_reports)
                if avg_branch < coverage_threshold:
                    needs_retry = True
                    self.logger.info(
                        "[runner] Branch coverage %.0f%% < threshold %.0f%%, retry recommended",
                        avg_branch * 100,
                        coverage_threshold * 100,
                    )

            return self._success({
                "build_success": True,
                "needs_fix": False,
                "error_details": "",
                "coverage_reports": coverage_reports,
                "needs_retry": needs_retry,
            })

        except Exception as e:
            return self._error(str(e))

    def _find_and_parse_coverage(self, project_path: Path) -> list[CoverageReport]:
        candidates = [
            project_path / "target" / "site" / "jacoco" / "jacoco.csv",
            project_path / "build" / "reports" / "jacoco" / "test" / "jacoco.csv",
        ]
        for csv_path in candidates:
            if csv_path.exists():
                return parse_jacoco_csv(csv_path)

        self.logger.warning("[runner] JaCoCo CSV report not found in expected locations")
        return []
