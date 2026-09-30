"""Provider boundary for future local models and Snapdragon acceleration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    """Interface consumed by future AI-enabled services."""

    @abstractmethod
    def analyze_context(self, context: Any) -> str:
        """Return a context interpretation."""

    @abstractmethod
    def summarize_session(self, context: Any) -> str:
        """Return a session summary."""

    @abstractmethod
    def interpret_plan(self, text: str) -> list[str]:
        """Return structured plan items from user text."""

    @abstractmethod
    def predict_next_action(self, context: Any) -> str | None:
        """Return a predicted action when supported."""


class LocalInferenceProvider(AIProvider):
    """Explicit baseline provider used until a local model runtime is added."""

    provider_name = "baseline-rule-based"

    def analyze_context(self, context: Any) -> str:
        return getattr(context, "summary", "No context available.")

    def summarize_session(self, context: Any) -> str:
        return getattr(context, "summary", "No session summary available.")

    def interpret_plan(self, text: str) -> list[str]:
        return [line.strip(" -•\t") for line in text.splitlines() if line.strip(" -•\t")]

    def predict_next_action(self, context: Any) -> str | None:
        return None

