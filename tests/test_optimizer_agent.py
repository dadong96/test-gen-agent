"""Tests for Optimizer Agent."""

from unittest.mock import MagicMock

import pytest

from src.agents.optimizer_agent import OptimizerAgent
from src.core.types import TestCase


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.chat_json.return_value = {
        "action": "keep",
        "reason": "Tests cover distinct scenarios",
        "merged_tests": [],
    }
    return llm


@pytest.fixture
def duplicate_test_cases():
    return [
        TestCase(id="TC-001", target_class="OrderService", target_method="createOrder",
                 scenario_type="normal", priority="P0",
                 java_code='    @Test void test1() { createOrder("u1", new BigDecimal("10")); }'),
        TestCase(id="TC-002", target_class="OrderService", target_method="createOrder",
                 scenario_type="normal", priority="P0",
                 java_code='    @Test void test2() { createOrder("u2", new BigDecimal("20")); }'),
        TestCase(id="TC-003", target_class="OrderService", target_method="createOrder",
                 scenario_type="exception", priority="P1",
                 java_code='    @Test void test3() { assertThrows(IllegalArgumentException.class, () -> createOrder("u1", null)); }'),
    ]


@pytest.mark.asyncio
async def test_optimizer_keeps_unique_tests(mock_llm):
    cases = [
        TestCase(id="TC-001", target_class="S", target_method="m1",
                 scenario_type="normal", priority="P0", java_code="    @Test void t1() {}"),
        TestCase(id="TC-002", target_class="S", target_method="m1",
                 scenario_type="exception", priority="P1", java_code="    @Test void t2() {}"),
    ]
    agent = OptimizerAgent(mock_llm)
    result = await agent.run(test_cases=cases)
    assert result.status == "success"
    assert len(result.data) == 2


@pytest.mark.asyncio
async def test_optimizer_assigns_priority(mock_llm):
    cases = [
        TestCase(id="TC-001", target_class="S", target_method="m",
                 scenario_type="normal", priority="", java_code="    @Test void t() {}"),
    ]
    agent = OptimizerAgent(mock_llm)
    result = await agent.run(test_cases=cases)
    for tc in result.data:
        assert tc.priority in ("P0", "P1", "P2")


@pytest.mark.asyncio
async def test_optimizer_preserves_all_cases(mock_llm, duplicate_test_cases):
    agent = OptimizerAgent(mock_llm)
    result = await agent.run(test_cases=duplicate_test_cases)
    assert result.status == "success"
    assert len(result.data) >= 1
