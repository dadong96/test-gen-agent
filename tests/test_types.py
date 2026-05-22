"""Tests for shared data types."""

from src.core.types import (
    ApiEndpoint,
    BranchInfo,
    BusinessRule,
    CoverageReport,
    LoopState,
    Param,
    RequirementSpec,
    TestCase,
)


def test_business_rule_creation():
    rule = BusinessRule(
        id="BR-001",
        description="Order amount must be positive",
        source="PRD section 3.2",
        related_apis=["POST /api/orders"],
    )
    assert rule.id == "BR-001"
    assert rule.description == "Order amount must be positive"
    assert "POST /api/orders" in rule.related_apis


def test_api_endpoint_creation():
    endpoint = ApiEndpoint(
        method="POST",
        path="/api/orders",
        params=[Param(name="amount", type="BigDecimal", required=True, description="Order amount")],
        response_schema={"id": "integer", "status": "string"},
        validations=["amount > 0", "status in (PENDING, CONFIRMED)"],
    )
    assert endpoint.method == "POST"
    assert len(endpoint.params) == 1
    assert endpoint.params[0].name == "amount"


def test_requirement_spec_defaults():
    spec = RequirementSpec()
    assert spec.business_rules == []
    assert spec.api_endpoints == []
    assert spec.edge_cases == []
    assert spec.constraints == []


def test_test_case_creation():
    tc = TestCase(
        id="TC-001",
        target_class="OrderService",
        target_method="createOrder",
        scenario_type="normal",
        priority="P0",
        java_code="@Test void testCreateOrder() {}",
        covered_rules=["BR-001"],
    )
    assert tc.scenario_type == "normal"
    assert tc.priority == "P0"


def test_coverage_report():
    report = CoverageReport(
        target_class="OrderService",
        method="createOrder",
        line_coverage=0.75,
        branch_coverage=0.50,
        uncovered_lines=[10, 11, 20],
        uncovered_branches=[
            BranchInfo(line=10, branch_index=0, description="null check on amount"),
        ],
    )
    assert report.branch_coverage == 0.50
    assert len(report.uncovered_branches) == 1


def test_loop_state():
    state = LoopState(round=1, coverage_threshold=0.70, uncovered_gaps=[])
    assert state.round == 1
    assert state.coverage_threshold == 0.70
