"""Tests for JaCoCo coverage report parser."""

from pathlib import Path

import pytest

from src.core.coverage_parser import parse_jacoco_csv
from src.core.types import CoverageReport

SAMPLE_CSV = """GROUP,PACKAGE,CLASS,INSTRUCTION_MISSED,INSTRUCTION_COVERED,BRANCH_MISSED,BRANCH_COVERED,LINE_MISSED,LINE_COVERED,COMPLEXITY_MISSED,COMPLEXITY_COVERED,METHOD_MISSED,METHOD_COVERED
,com.example.service,OrderService,20,80,4,6,10,30,5,15,2,8
,com.example.service,UserService,5,45,1,9,2,18,1,9,0,5
"""


def test_parse_csv_returns_reports(tmp_path):
    csv_file = tmp_path / "jacoco.csv"
    csv_file.write_text(SAMPLE_CSV)
    reports = parse_jacoco_csv(csv_file)
    assert len(reports) == 2


def test_parse_csv_class_name(tmp_path):
    csv_file = tmp_path / "jacoco.csv"
    csv_file.write_text(SAMPLE_CSV)
    reports = parse_jacoco_csv(csv_file)
    classes = {r.target_class: r for r in reports}
    assert "OrderService" in classes
    assert "UserService" in classes


def test_parse_csv_coverage_values(tmp_path):
    csv_file = tmp_path / "jacoco.csv"
    csv_file.write_text(SAMPLE_CSV)
    reports = parse_jacoco_csv(csv_file)
    order = next(r for r in reports if r.target_class == "OrderService")
    assert order.line_coverage == pytest.approx(0.75)
    assert order.branch_coverage == pytest.approx(0.6)


def test_parse_csv_user_service(tmp_path):
    csv_file = tmp_path / "jacoco.csv"
    csv_file.write_text(SAMPLE_CSV)
    reports = parse_jacoco_csv(csv_file)
    user = next(r for r in reports if r.target_class == "UserService")
    assert user.line_coverage == pytest.approx(0.9)
    assert user.branch_coverage == pytest.approx(0.9)


def test_parse_empty_csv(tmp_path):
    csv_file = tmp_path / "jacoco.csv"
    csv_file.write_text("GROUP,PACKAGE,CLASS,INSTRUCTION_MISSED,INSTRUCTION_COVERED,BRANCH_MISSED,BRANCH_COVERED,LINE_MISSED,LINE_COVERED,COMPLEXITY_MISSED,COMPLEXITY_COVERED,METHOD_MISSED,METHOD_COVERED\n")
    reports = parse_jacoco_csv(csv_file)
    assert reports == []
