"""Parser Agent — extracts structured requirements from PRD + Swagger docs."""

from __future__ import annotations

import json
from pathlib import Path

from src.agents.base import AgentResult, BaseAgent
from src.core.types import ApiEndpoint, BusinessRule, Param, RequirementSpec
from src.utils.file_utils import read_text


class ParserAgent(BaseAgent):
    name = "parser"
    system_prompt = """You are a requirements analyst. Extract structured information from product documents.

Given a PRD document and/or Swagger/OpenAPI spec, extract:
1. Business rules (with IDs, descriptions, source sections, related APIs)
2. Edge cases and boundary conditions
3. Non-functional constraints (idempotency, concurrency, etc.)

Respond with ONLY valid JSON in this format:
{
  "business_rules": [
    {"id": "BR-001", "description": "...", "source": "...", "related_apis": ["..."]}
  ],
  "edge_cases": ["..."],
  "constraints": ["..."]
}"""

    async def run(
        self,
        prd_path: Path,
        swagger_path: Path | None = None,
    ) -> AgentResult:
        try:
            prd_content = read_text(prd_path)

            endpoints = []
            swagger_content = ""
            if swagger_path and swagger_path.exists():
                swagger_content = read_text(swagger_path)
                endpoints = self._parse_swagger(swagger_content)

            prompt = self._build_prompt(prd_content, swagger_content)
            llm_result = self.chat_json(prompt)

            business_rules = [
                BusinessRule(
                    id=br["id"],
                    description=br["description"],
                    source=br.get("source", ""),
                    related_apis=br.get("related_apis", []),
                )
                for br in llm_result.get("business_rules", [])
            ]

            spec = RequirementSpec(
                business_rules=business_rules,
                api_endpoints=endpoints,
                edge_cases=llm_result.get("edge_cases", []),
                constraints=llm_result.get("constraints", []),
            )

            self.logger.info(
                "[parser] Extracted %d rules, %d endpoints, %d edge cases",
                len(spec.business_rules),
                len(spec.api_endpoints),
                len(spec.edge_cases),
            )

            return self._success(spec)

        except Exception as e:
            return self._error(str(e))

    def _parse_swagger(self, swagger_content: str) -> list[ApiEndpoint]:
        try:
            spec = json.loads(swagger_content)
        except json.JSONDecodeError:
            self.logger.warning("[parser] Failed to parse Swagger JSON")
            return []

        endpoints = []
        paths = spec.get("paths", {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method not in ("get", "post", "put", "patch", "delete"):
                    continue
                params = []
                for p in details.get("parameters", []):
                    params.append(Param(
                        name=p.get("name", ""),
                        type=p.get("schema", {}).get("type", "string"),
                        required=p.get("required", False),
                        description=p.get("description", ""),
                    ))
                endpoints.append(ApiEndpoint(
                    method=method.upper(),
                    path=path,
                    params=params,
                    response_schema=details.get("responses", {}),
                    validations=[],
                ))

        return endpoints

    def _build_prompt(self, prd_content: str, swagger_content: str) -> str:
        parts = [f"## PRD Document\n\n{prd_content}"]
        if swagger_content:
            parts.append(f"\n\n## Swagger/OpenAPI Spec\n\n{swagger_content}")
        parts.append("\n\nExtract business rules, edge cases, and constraints from the above documents.")
        return "\n".join(parts)
