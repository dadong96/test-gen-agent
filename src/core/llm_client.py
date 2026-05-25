"""Unified LLM client supporting Anthropic Claude and OpenAI-compatible APIs."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from config.settings import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    MAX_TOKENS_PER_ANALYSIS,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
)

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # exponential backoff: 2s, 4s, 8s
RETRYABLE_STATUS_CODES = {429, 500, 502, 503}


def _make_anthropic_client():
    from anthropic import Anthropic
    return Anthropic(api_key=ANTHROPIC_API_KEY)


def _make_openai_client():
    from openai import OpenAI
    return OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)


class LLMClient:
    """Thin wrapper around the LLM provider with retry and token tracking."""

    def __init__(self):
        self._provider = "anthropic" if ANTHROPIC_API_KEY else ("openai" if OPENAI_API_KEY else None)
        self._client: Any = None
        self._model = ""
        self.total_tokens_input = 0
        self.total_tokens_output = 0
        self.call_count = 0
        self._init_client()

    def _init_client(self):
        if self._provider == "anthropic":
            self._client = _make_anthropic_client()
            self._model = ANTHROPIC_MODEL
        elif self._provider == "openai":
            self._client = _make_openai_client()
            self._model = OPENAI_MODEL
        else:
            raise RuntimeError(
                "No API key configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env."
            )

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def model(self) -> str:
        return self._model

    def _call_api(self, messages, system_prompt, max_tokens, temperature, kwargs):
        """Single API call attempt. Returns (text, input_tokens, output_tokens)."""
        if self._provider == "anthropic":
            response = self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages,
                **kwargs,
            )
            text = response.content[0].text
            input_tokens = getattr(response.usage, "input_tokens", 0)
            output_tokens = getattr(response.usage, "output_tokens", 0)
        else:
            sys_msg = [{"role": "system", "content": system_prompt}] if system_prompt else []
            response = self._client.chat.completions.create(
                model=self._model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=sys_msg + messages,
                **kwargs,
            )
            text = response.choices[0].message.content or ""
            usage = response.usage
            input_tokens = getattr(usage, "prompt_tokens", 0)
            output_tokens = getattr(usage, "completion_tokens", 0)
        return text, input_tokens, output_tokens

    def chat(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.2,
        **kwargs,
    ) -> str:
        """Send a chat request and return the assistant's text response."""
        max_tokens = max_tokens or MAX_TOKENS_PER_ANALYSIS

        last_exc = None
        for attempt in range(MAX_RETRIES):
            try:
                text, input_tokens, output_tokens = self._call_api(
                    messages, system_prompt, max_tokens, temperature, kwargs,
                )
                self.total_tokens_input += input_tokens
                self.total_tokens_output += output_tokens
                self.call_count += 1
                return text
            except Exception as exc:
                last_exc = exc
                status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
                if status not in RETRYABLE_STATUS_CODES and attempt == 0:
                    raise
                wait = RETRY_BACKOFF_BASE ** attempt
                logger.warning("LLM call failed (attempt %d/%d, status=%s): %s — retrying in %ds",
                               attempt + 1, MAX_RETRIES, status, exc, wait)
                time.sleep(wait)

        raise RuntimeError(f"LLM call failed after {MAX_RETRIES} retries") from last_exc

    def chat_json(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> dict | list:
        """Send a chat request and parse the response as JSON."""
        if max_tokens is None:
            max_tokens = max(MAX_TOKENS_PER_ANALYSIS, 8192)
        messages_with_hint = messages + [
            {
                "role": "user",
                "content": "Respond with ONLY valid JSON, no markdown code fences or extra text.",
            }
        ]
        raw = self.chat(messages_with_hint, system_prompt=system_prompt, max_tokens=max_tokens, **kwargs)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse LLM response as JSON: %s\nRaw response (first 500 chars): %s", exc, raw[:500])
            raise ValueError(f"LLM returned invalid JSON: {exc}") from exc

    def token_summary(self) -> dict:
        return {
            "provider": self._provider,
            "model": self._model,
            "total_calls": self.call_count,
            "input_tokens": self.total_tokens_input,
            "output_tokens": self.total_tokens_output,
            "total_tokens": self.total_tokens_input + self.total_tokens_output,
        }
