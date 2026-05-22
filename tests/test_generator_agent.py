"""Tests for Generator Agent."""

from unittest.mock import MagicMock

import pytest

from src.agents.generator_agent import GeneratorAgent
from src.core.types import (
    ApiEndpoint,
    BusinessRule,
    CoverageReport,
    JavaClassInfo,
    LoopState,
    MethodInfo,
    Param,
    RequirementSpec,
    TestCase,
)


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.chat_json.return_value = [
        {
            "id": "TC-001",
            "target_method": "createOrder",
            "scenario_type": "normal",
            "priority": "P0",
            "java_code": '    @Test\n    @DisplayName("createOrder - normal")\n    void testCreateOrderNormal() {\n        // given\n        // when\n        // then\n    }',
        },
        {
            "id": "TC-002",
            "target_method": "createOrder",
            "scenario_type": "exception",
            "priority": "P1",
            "java_code": '    @Test\n    @DisplayName("createOrder - null amount")\n    void testCreateOrderNullAmount() {\n        // given\n        // when\n        // then\n    }',
        },
    ]
    return llm


@pytest.fixture
def sample_spec():
    return RequirementSpec(
        business_rules=[
            BusinessRule(id="BR-001", description="Amount must be positive", source="PRD", related_apis=["POST /api/orders"]),
        ],
        api_endpoints=[
            ApiEndpoint(method="POST", path="/api/orders", params=[Param(name="amount", type="number", required=True)]),
        ],
        edge_cases=["amount is zero", "amount is negative"],
    )


@pytest.fixture
def sample_ast():
    return JavaClassInfo(
        class_name="OrderService",
        package="com.example.service",
        imports=["java.math.BigDecimal"],
        methods=[
            MethodInfo(
                name="createOrder",
                return_type="Order",
                parameters=[("userId", "String"), ("amount", "BigDecimal")],
                is_public=True,
                body_source="if (amount == null) throw ...",
            ),
        ],
    )


@pytest.mark.asyncio
async def test_generator_produces_test_cases(mock_llm, sample_spec, sample_ast):
    agent = GeneratorAgent(mock_llm)
    result = await agent.run(spec=sample_spec, ast_info=sample_ast)
    assert result.status == "success"
    cases = result.data
    assert len(cases) == 2
    assert all(isinstance(tc, TestCase) for tc in cases)


@pytest.mark.asyncio
async def test_generator_sets_target_class(mock_llm, sample_spec, sample_ast):
    agent = GeneratorAgent(mock_llm)
    result = await agent.run(spec=sample_spec, ast_info=sample_ast)
    for tc in result.data:
        assert tc.target_class == "OrderService"


@pytest.mark.asyncio
async def test_generator_with_coverage_gaps(mock_llm, sample_spec, sample_ast):
    gaps = [
        CoverageReport(target_class="OrderService", method="createOrder",
                       line_coverage=0.5, branch_coverage=0.3,
                       uncovered_lines=[10, 11], uncovered_branches=[]),
    ]
    loop_state = LoopState(round=2, coverage_threshold=0.80, uncovered_gaps=gaps)

    agent = GeneratorAgent(mock_llm)
    result = await agent.run(spec=sample_spec, ast_info=sample_ast, loop_state=loop_state)
    assert result.status == "success"
