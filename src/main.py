"""Programmatic entry point for the test generation pipeline."""

from __future__ import annotations

import asyncio
from pathlib import Path

from src.core.llm_client import LLMClient
from src.core.orchestrator import Orchestrator
from src.core.types import PipelineResult


async def run_test_generation(
    project_path: str,
    prd_path: str,
    swagger_path: str | None = None,
    coverage_threshold: float = 0.70,
    max_rounds: int = 3,
    no_run: bool = False,
    dry_run: bool = False,
) -> PipelineResult:
    """Run the test generation pipeline programmatically."""
    llm = LLMClient()
    orchestrator = Orchestrator(llm, max_coverage_rounds=max_rounds)

    return await orchestrator.run(
        project_path=Path(project_path),
        prd_path=Path(prd_path),
        swagger_path=Path(swagger_path) if swagger_path else None,
        coverage_threshold=coverage_threshold,
        no_run=no_run,
        dry_run=dry_run,
    )
