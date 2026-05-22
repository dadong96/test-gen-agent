"""Tests for JUnit 5 test file writer."""

from pathlib import Path

import pytest

from src.core.types import TestCase
from src.generators.junit_writer import JUnitWriter


@pytest.fixture
def writer(tmp_path):
    return JUnitWriter(output_dir=tmp_path)


@pytest.fixture
def sample_test_cases():
    return [
        TestCase(
            id="TC-001",
            target_class="OrderService",
            target_method="createOrder",
            scenario_type="normal",
            priority="P0",
            java_code='    @Test\n    @DisplayName("createOrder - normal case")\n    void testCreateOrderNormal() {\n        // given\n        // when\n        // then\n    }',
            covered_rules=["BR-001"],
        ),
        TestCase(
            id="TC-002",
            target_class="OrderService",
            target_method="createOrder",
            scenario_type="exception",
            priority="P1",
            java_code='    @Test\n    @DisplayName("createOrder - negative amount")\n    void testCreateOrderNegativeAmount() {\n        // given\n        // when\n        // then\n    }',
            covered_rules=["BR-001"],
        ),
    ]


def test_write_generates_java_file(writer, sample_test_cases):
    files = writer.write_tests(sample_test_cases)
    assert len(files) == 1
    assert files[0].name == "OrderServiceTest.java"
    assert files[0].exists()


def test_generated_file_contains_package(writer, sample_test_cases):
    files = writer.write_tests(sample_test_cases)
    content = files[0].read_text(encoding="utf-8")
    assert "package" in content


def test_generated_file_contains_imports(writer, sample_test_cases):
    files = writer.write_tests(sample_test_cases)
    content = files[0].read_text(encoding="utf-8")
    assert "import org.junit.jupiter.api.Test" in content
    assert "import org.junit.jupiter.api.DisplayName" in content


def test_generated_file_contains_test_methods(writer, sample_test_cases):
    files = writer.write_tests(sample_test_cases)
    content = files[0].read_text(encoding="utf-8")
    assert "testCreateOrderNormal" in content
    assert "testCreateOrderNegativeAmount" in content


def test_groups_by_class(writer):
    cases = [
        TestCase(id="TC-001", target_class="OrderService", target_method="createOrder",
                 scenario_type="normal", priority="P0", java_code="    @Test void t1() {}"),
        TestCase(id="TC-002", target_class="UserService", target_method="getUser",
                 scenario_type="normal", priority="P0", java_code="    @Test void t2() {}"),
    ]
    files = writer.write_tests(cases)
    names = {f.name for f in files}
    assert "OrderServiceTest.java" in names
    assert "UserServiceTest.java" in names
