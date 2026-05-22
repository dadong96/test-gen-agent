"""Base Agent class — all specialized agents inherit from this."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from src.core.llm_client import LLMClient
from src.utils.logger import setup_logger


@dataclass
class AgentResult:
    """Standardized output every agent must produce."""
    agent_name: str
    status: str  # success / error / skipped
    data: Any = None
    error: str = ""
    metadata: dict = field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base for all agents."""

    name: str = "base"
    system_prompt: str = ""

    def __init__(self, llm: LLMClient, logger: logging.Logger | None = None):
        self.llm = llm
        self.logger = logger or setup_logger(f"agent.{self.name}")

    @abstractmethod
    async def run(self, **kwargs) -> AgentResult:
        """Execute the agent's core logic. Must be implemented by subclasses."""
        ...

    def chat(self, user_message: str, system_prompt: str | None = None, **kwargs) -> str:
        """Convenience wrapper for LLM chat."""
        messages = [{"role": "user", "content": user_message}]
        sys_prompt = system_prompt or self.system_prompt
        self.logger.debug("[%s] Sending prompt (%d chars)", self.name, len(user_message))
        return self.llm.chat(messages, system_prompt=sys_prompt, **kwargs)

    def chat_json(self, user_message: str, system_prompt: str | None = None, **kwargs) -> dict | list:
        """Convenience wrapper for LLM JSON chat."""
        messages = [{"role": "user", "content": user_message}]
        sys_prompt = system_prompt or self.system_prompt
        self.logger.debug("[%s] Sending JSON prompt (%d chars)", self.name, len(user_message))
        return self.llm.chat_json(messages, system_prompt=sys_prompt, **kwargs)

    def _success(self, data: Any, metadata: dict | None = None) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            status="success",
            data=data,
            metadata=metadata or {},
        )

    def _error(self, error: str) -> AgentResult:
        self.logger.error("[%s] Error: %s", self.name, error)
        return AgentResult(agent_name=self.name, status="error", error=error)
