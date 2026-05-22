"""Tests for Parser Agent."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.agents.parser_agent import ParserAgent
from src.core.types import RequirementSpec


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.chat_json.return_value = {
        "business_rules": [
            {
                "id": "BR-001",
                "description": "Order amount must be positive",
                "source": "PRD section 3.2",
                "related_apis": ["POST /api/orders"],
            }
        ],
        "edge_cases": ["amount is zero", "amount is negative"],
        "constraints": ["idempotent order creation"],
    }
    return llm


@pytest.fixture
def sample_prd(tmp_path):
    content = """# Order Service PRD

## 3.2 Order Creation
- Users can create orders with a positive amount
- Amount must be greater than zero
"""
    prd = tmp_path / "prd.md"
    prd.write_text(content)
    return prd


@pytest.fixture
def sample_swagger(tmp_path):
    swagger = {
        "openapi": "3.0.0",
        "paths": {
            "/api/orders": {
                "post": {
                    "summary": "Create order",
                    "parameters": [
                        {"name": "amount", "in": "query", "required": True, "schema": {"type": "number"}}
                    ],
                    "responses": {"200": {"description": "Order created"}},
                }
            }
        },
    }
    path = tmp_path / "swagger.json"
    path.write_text(json.dumps(swagger))
    return path


@pytest.mark.asyncio
async def test_parser_extracts_business_rules(mock_llm, sample_prd, sample_swagger):
    agent = ParserAgent(mock_llm)
    result = await agent.run(prd_path=sample_prd, swagger_path=sample_swagger)
    assert result.status == "success"
    spec = result.data
    assert isinstance(spec, RequirementSpec)
    assert len(spec.business_rules) == 1
    assert spec.business_rules[0].id == "BR-001"


@pytest.mark.asyncio
async def test_parser_extracts_api_endpoints(mock_llm, sample_prd, sample_swagger):
    agent = ParserAgent(mock_llm)
    result = await agent.run(prd_path=sample_prd, swagger_path=sample_swagger)
    spec = result.data
    assert len(spec.api_endpoints) == 1
    assert spec.api_endpoints[0].method == "POST"
    assert spec.api_endpoints[0].path == "/api/orders"


@pytest.mark.asyncio
async def test_parser_extracts_edge_cases(mock_llm, sample_prd, sample_swagger):
    agent = ParserAgent(mock_llm)
    result = await agent.run(prd_path=sample_prd, swagger_path=sample_swagger)
    spec = result.data
    assert len(spec.edge_cases) > 0


@pytest.mark.asyncio
async def test_parser_no_swagger(mock_llm, sample_prd):
    agent = ParserAgent(mock_llm)
    result = await agent.run(prd_path=sample_prd, swagger_path=None)
    assert result.status == "success"
    spec = result.data
    assert len(spec.api_endpoints) == 0
