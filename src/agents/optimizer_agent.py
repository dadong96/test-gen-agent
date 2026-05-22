"""Optimizer Agent — deduplicates, merges, and prioritizes test cases."""

from __future__ import annotations

from src.agents.base import AgentResult, BaseAgent
from src.core.types import TestCase


class OptimizerAgent(BaseAgent):
    name = "optimizer"
    system_prompt = """You are a test optimization expert. Given a list of JUnit 5 test cases, analyze them for:

1. **Duplicates**: Tests that cover the same scenario with the same logic
2. **Mergable tests**: Similar tests that can be combined into @ParameterizedTest
3. **Priority assignment**: P0 (core flows), P1 (exceptions), P2 (boundaries)

Respond with ONLY valid JSON:
{
  "action": "keep|merge|deduplicate",
  "reason": "explanation",
  "merged_tests": [
    {
      "ids_to_merge": ["TC-001", "TC-002"],
      "merged_id": "TC-001",
      "merged_java_code": "...",
      "merged_priority": "P0"
    }
  ],
  "priority_overrides": {
    "TC-001": "P0",
    "TC-003": "P1"
  }
}"""

    async def run(self, test_cases: list[TestCase]) -> AgentResult:
        try:
            if not test_cases:
                return self._success([])

            if len(test_cases) <= 3:
                optimized = self._apply_default_priorities(test_cases)
                return self._success(optimized)

            prompt = self._build_prompt(test_cases)
            llm_result = self.chat_json(prompt)

            optimized = self._apply_optimization(test_cases, llm_result)

            self.logger.info(
                "[optimizer] Input: %d tests, output: %d tests",
                len(test_cases),
                len(optimized),
            )

            return self._success(optimized)

        except Exception as e:
            return self._error(str(e))

    def _apply_default_priorities(self, cases: list[TestCase]) -> list[TestCase]:
        priority_map = {"normal": "P0", "exception": "P1", "boundary": "P2"}
        for tc in cases:
            if not tc.priority:
                tc.priority = priority_map.get(tc.scenario_type, "P1")
        return cases

    def _apply_optimization(
        self,
        cases: list[TestCase],
        llm_result: dict,
    ) -> list[TestCase]:
        overrides = llm_result.get("priority_overrides", {})
        for tc in cases:
            if tc.id in overrides:
                tc.priority = overrides[tc.id]

        merges = llm_result.get("merged_tests", [])
        merged_ids = set()
        for merge in merges:
            ids_to_merge = merge.get("ids_to_merge", [])
            merged_id = merge.get("merged_id", ids_to_merge[0] if ids_to_merge else "")
            merged_ids.update(ids_to_merge)

            for tc in cases:
                if tc.id == merged_id:
                    tc.java_code = merge.get("merged_java_code", tc.java_code)
                    tc.priority = merge.get("merged_priority", tc.priority)
                    break

        if merged_ids:
            cases = [tc for tc in cases if tc.id not in merged_ids or tc.id in {
                m.get("merged_id") for m in merges
            }]

        priority_map = {"normal": "P0", "exception": "P1", "boundary": "P2"}
        for tc in cases:
            if not tc.priority:
                tc.priority = priority_map.get(tc.scenario_type, "P1")

        return cases
