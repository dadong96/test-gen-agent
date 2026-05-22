"""Generator Agent — generates JUnit 5 test cases from requirements + AST."""

from __future__ import annotations

from src.agents.base import AgentResult, BaseAgent
from src.core.types import (
    JavaClassInfo,
    LoopState,
    RequirementSpec,
    TestCase,
)


class GeneratorAgent(BaseAgent):
    name = "generator"
    system_prompt = """You are a Java test engineer. Generate JUnit 5 test cases for the given class and methods.

For each method, generate tests covering:
1. Normal flow — valid inputs, expected outputs
2. Exception flow — invalid inputs, expected exceptions
3. Boundary values — null, empty, zero, max values

Respond with ONLY valid JSON — a list of test case objects:
[
  {
    "id": "TC-001",
    "target_method": "methodName",
    "scenario_type": "normal|exception|boundary",
    "priority": "P0|P1|P2",
    "java_code": "    @Test\\n    @DisplayName(\\"...\\")\\n    void testName() {\\n        // given\\n        // when\\n        // then\\n    }"
  }
]

Rules:
- Use @Test, @DisplayName, @ParameterizedTest annotations
- P0 = core normal flows, P1 = exception flows, P2 = boundary values
- java_code must be properly indented (4 spaces) and contain the full method body
- Use realistic test data based on the business rules provided"""

    async def run(
        self,
        spec: RequirementSpec,
        ast_info: JavaClassInfo,
        loop_state: LoopState | None = None,
    ) -> AgentResult:
        try:
            prompt = self._build_prompt(spec, ast_info, loop_state)
            raw_cases = self.chat_json(prompt)

            test_cases = []
            for item in raw_cases:
                tc = TestCase(
                    id=item.get("id", f"TC-{len(test_cases)+1:03d}"),
                    target_class=ast_info.class_name,
                    target_method=item.get("target_method", ""),
                    scenario_type=item.get("scenario_type", "normal"),
                    priority=item.get("priority", "P0"),
                    java_code=item.get("java_code", ""),
                    covered_rules=[],
                )
                test_cases.append(tc)

            self.logger.info(
                "[generator] Generated %d test cases for %s",
                len(test_cases),
                ast_info.class_name,
            )

            return self._success(test_cases)

        except Exception as e:
            return self._error(str(e))

    def _build_prompt(
        self,
        spec: RequirementSpec,
        ast_info: JavaClassInfo,
        loop_state: LoopState | None,
    ) -> str:
        parts = []

        parts.append(f"## Target Class: {ast_info.class_name}")
        parts.append(f"Package: {ast_info.package}")
        parts.append(f"Imports: {', '.join(ast_info.imports)}")
        parts.append("")

        parts.append("## Public Methods")
        for m in ast_info.methods:
            if not m.is_public:
                continue
            params_str = ", ".join(f"{t} {n}" for n, t in m.parameters)
            parts.append(f"- {m.return_type} {m.name}({params_str})")
            if m.body_source:
                body_preview = m.body_source[:500]
                parts.append(f"  Body: {body_preview}")
        parts.append("")

        if spec.business_rules:
            parts.append("## Business Rules")
            for rule in spec.business_rules:
                parts.append(f"- [{rule.id}] {rule.description}")
            parts.append("")

        if spec.edge_cases:
            parts.append("## Edge Cases to Cover")
            for ec in spec.edge_cases:
                parts.append(f"- {ec}")
            parts.append("")

        if loop_state and loop_state.uncovered_gaps:
            parts.append(f"## Coverage Gaps (Round {loop_state.round})")
            parts.append(f"Target coverage: {loop_state.coverage_threshold:.0%}")
            for gap in loop_state.uncovered_gaps:
                parts.append(f"- {gap.target_class}.{gap.method}: "
                             f"line={gap.line_coverage:.0%}, branch={gap.branch_coverage:.0%}")
                if gap.uncovered_lines:
                    parts.append(f"  Uncovered lines: {gap.uncovered_lines}")
            parts.append("")
            parts.append("Generate additional tests to cover these gaps.")

        return "\n".join(parts)
