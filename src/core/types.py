"""Shared data types used across the pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field

# Re-export types from other modules for convenience
from src.core.ast_parser import JavaClassInfo, MethodInfo  # noqa: F401
from src.agents.base import AgentResult  # noqa: F401
from src.core.build_executor import BuildResult  # noqa: F401


@dataclass
class BusinessRule:
    id: str
    description: str
    source: str
    related_apis: list[str] = field(default_factory=list)


@dataclass
class Param:
    name: str
    type: str
    required: bool = True
    description: str = ""


@dataclass
class ApiEndpoint:
    method: str
    path: str
    params: list[Param] = field(default_factory=list)
    response_schema: dict = field(default_factory=dict)
    validations: list[str] = field(default_factory=list)


@dataclass
class RequirementSpec:
    business_rules: list[BusinessRule] = field(default_factory=list)
    api_endpoints: list[ApiEndpoint] = field(default_factory=list)
    edge_cases: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)


@dataclass
class TestCase:
    id: str
    target_class: str
    target_method: str
    scenario_type: str  # "normal" | "exception" | "boundary"
    priority: str  # "P0" | "P1" | "P2"
    java_code: str
    covered_rules: list[str] = field(default_factory=list)
    package: str = ""  # Java package of the target class


@dataclass
class BranchInfo:
    line: int
    branch_index: int
    description: str = ""


@dataclass
class CoverageReport:
    target_class: str
    method: str
    line_coverage: float
    branch_coverage: float
    uncovered_lines: list[int] = field(default_factory=list)
    uncovered_branches: list[BranchInfo] = field(default_factory=list)


@dataclass
class LoopState:
    round: int
    coverage_threshold: float
    uncovered_gaps: list[CoverageReport] = field(default_factory=list)


@dataclass
class PipelineResult:
    target: str
    stage_results: dict = field(default_factory=dict)
    generated_tests: list[TestCase] = field(default_factory=list)
    coverage_reports: list[CoverageReport] = field(default_factory=list)
    token_summary: dict = field(default_factory=dict)
    duration_seconds: float = 0.0
    status: str = "success"
    error: str = ""
