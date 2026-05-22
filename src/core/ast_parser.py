"""Java AST parser using tree-sitter-java."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import tree_sitter_java as tsjava
from tree_sitter import Language, Parser

JAVA_LANGUAGE = Language(tsjava.language())


@dataclass
class MethodInfo:
    name: str
    return_type: str = ""
    parameters: list[tuple[str, str]] = field(default_factory=list)
    is_public: bool = False
    is_static: bool = False
    annotations: list[str] = field(default_factory=list)
    body_source: str = ""


@dataclass
class JavaClassInfo:
    class_name: str = ""
    package: str = ""
    imports: list[str] = field(default_factory=list)
    methods: list[MethodInfo] = field(default_factory=list)
    fields: list[tuple[str, str]] = field(default_factory=list)  # (type, name)


def _get_text(node, source: bytes) -> str:
    return source[node.start_byte:node.end_byte].decode("utf-8")


def _find_children(node, type_name: str):
    """Find all direct children of a given type."""
    return [c for c in node.children if c.type == type_name]


def _parse_method(node, source: bytes) -> MethodInfo:
    """Extract method info from a method_declaration node."""
    name = ""
    return_type = ""
    params = []
    is_public = False
    is_static = False
    annotations = []

    for child in node.children:
        if child.type == "modifiers":
            text = _get_text(child, source)
            is_public = "public" in text
            is_static = "static" in text
        elif child.type == "annotation":
            annotations.append(_get_text(child, source))
        elif child.type == "identifier":
            name = _get_text(child, source)
        elif child.type in ("type_identifier", "void_type", "integral_type",
                            "floating_point_type", "boolean_type", "array_type",
                            "generic_type"):
            return_type = _get_text(child, source)
        elif child.type == "formal_parameters":
            for param in child.children:
                if param.type == "formal_parameter":
                    param_type = ""
                    param_name = ""
                    for pc in param.children:
                        if pc.type in ("type_identifier", "integral_type",
                                       "floating_point_type", "boolean_type",
                                       "generic_type", "array_type"):
                            param_type = _get_text(pc, source)
                        elif pc.type == "identifier":
                            param_name = _get_text(pc, source)
                    if param_name:
                        params.append((param_name, param_type))

    body_source = ""
    block = node.child_by_field_name("body")
    if block:
        body_source = _get_text(block, source)

    return MethodInfo(
        name=name,
        return_type=return_type,
        parameters=params,
        is_public=is_public,
        is_static=is_static,
        annotations=annotations,
        body_source=body_source,
    )


def parse_java_source(source: str) -> JavaClassInfo:
    """Parse Java source code and extract class info."""
    parser = Parser(JAVA_LANGUAGE)
    tree = parser.parse(source.encode("utf-8"))
    root = tree.root_node

    class_name = ""
    package = ""
    imports = []
    methods = []
    fields = []

    # Package
    for child in root.children:
        if child.type == "package_declaration":
            for c in child.children:
                if c.type == "scoped_identifier":
                    package = _get_text(c, source.encode("utf-8"))

    # Imports
    for child in root.children:
        if child.type == "import_declaration":
            for c in child.children:
                if c.type == "scoped_identifier":
                    imports.append(_get_text(c, source.encode("utf-8")))

    # Class declaration
    src_bytes = source.encode("utf-8")
    for child in root.children:
        if child.type in ("class_declaration", "record_declaration"):
            for c in child.children:
                if c.type == "identifier":
                    class_name = _get_text(c, src_bytes)
                elif c.type == "class_body":
                    for member in c.children:
                        if member.type == "method_declaration":
                            methods.append(_parse_method(member, src_bytes))
                        elif member.type == "field_declaration":
                            field_type = ""
                            field_name = ""
                            for fc in member.children:
                                if fc.type in ("type_identifier", "integral_type",
                                               "floating_point_type", "generic_type"):
                                    field_type = _get_text(fc, src_bytes)
                                elif fc.type == "variable_declarator":
                                    for vc in fc.children:
                                        if vc.type == "identifier":
                                            field_name = _get_text(vc, src_bytes)
                            if field_name:
                                fields.append((field_type, field_name))

    return JavaClassInfo(
        class_name=class_name,
        package=package,
        imports=imports,
        methods=methods,
        fields=fields,
    )


def parse_java_file(path: Path) -> JavaClassInfo:
    """Parse a Java file and return class info."""
    source = path.read_text(encoding="utf-8")
    return parse_java_source(source)
