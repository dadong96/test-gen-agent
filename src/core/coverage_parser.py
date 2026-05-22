"""JaCoCo coverage report parser (CSV format)."""

from __future__ import annotations

import csv
from pathlib import Path

from src.core.types import CoverageReport


def parse_jacoco_csv(csv_path: Path) -> list[CoverageReport]:
    """Parse a JaCoCo CSV report and return coverage info per class."""
    reports = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            class_name = row.get("CLASS", "").strip()
            if not class_name:
                continue

            instruction_missed = int(row.get("INSTRUCTION_MISSED", 0))
            instruction_covered = int(row.get("INSTRUCTION_COVERED", 0))
            branch_missed = int(row.get("BRANCH_MISSED", 0))
            branch_covered = int(row.get("BRANCH_COVERED", 0))
            line_missed = int(row.get("LINE_MISSED", 0))
            line_covered = int(row.get("LINE_COVERED", 0))

            total_lines = line_missed + line_covered
            total_branches = branch_missed + branch_covered

            line_coverage = line_covered / total_lines if total_lines > 0 else 1.0
            branch_coverage = branch_covered / total_branches if total_branches > 0 else 1.0

            reports.append(CoverageReport(
                target_class=class_name,
                method="*",
                line_coverage=line_coverage,
                branch_coverage=branch_coverage,
                uncovered_lines=[],
                uncovered_branches=[],
            ))

    return reports
