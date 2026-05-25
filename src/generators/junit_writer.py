"""JUnit 5 test file writer using Jinja2 templates."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from config.settings import OUTPUT_DIR
from src.core.types import TestCase


class JUnitWriter:
    """Writes TestCase objects to .java files grouped by target class."""

    def __init__(self, output_dir: Path | None = None, template_dir: Path | None = None):
        self.output_dir = output_dir or (OUTPUT_DIR / "generated-tests")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        tpl_dir = template_dir or Path(__file__).parent.parent.parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(tpl_dir)),
            keep_trailing_newline=True,
        )
        self.template = self.env.get_template("junit5_template.java")

    def write_tests(self, test_cases: list[TestCase]) -> list[Path]:
        """Write test cases to .java files, grouped by target class. Returns list of file paths."""
        by_class: dict[str, list[TestCase]] = defaultdict(list)
        for tc in test_cases:
            by_class[tc.target_class].append(tc)

        written_files = []
        for class_name, cases in by_class.items():
            package = cases[0].package if cases[0].package else self._derive_package(class_name)
            imports = self._collect_imports(cases)

            content = self.template.render(
                package=package,
                class_name=class_name,
                imports=imports,
                tests=cases,
            )

            file_path = self.output_dir / f"{class_name}Test.java"
            file_path.write_text(content, encoding="utf-8")
            written_files.append(file_path)

        return written_files

    def _derive_package(self, class_name: str) -> str:
        return "com.example.service"

    def _collect_imports(self, cases: list[TestCase]) -> str:
        imports = set()
        for tc in cases:
            if "ParameterizedTest" in tc.java_code:
                imports.add("import org.junit.jupiter.params.ParameterizedTest;")
            if "@NullAndEmptySource" in tc.java_code:
                imports.add("import org.junit.jupiter.params.provider.NullAndEmptySource;")
            if "@ValueSource" in tc.java_code:
                imports.add("import org.junit.jupiter.params.provider.ValueSource;")
        return "\n".join(sorted(imports))
