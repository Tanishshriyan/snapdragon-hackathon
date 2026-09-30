"""Optional local SLM reasoning with a deterministic MVP fallback."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ReasoningResult:
    text: str
    provider: str
    used_model: bool


class DemoReasoner:
    """Useful local reasoning when no model file is configured."""

    provider_name = "local-demo-reasoner"

    def explain(self, context: Any, memories: list[str] | None = None) -> ReasoningResult:
        application = getattr(context, "active_application", None) or "your current workspace"
        task = getattr(context, "summary", None) or "No active task has been identified yet."
        related = ""
        if memories:
            related = f" Related memory: {memories[0]}"
        return ReasoningResult(f"You are working in {application}. {task}{related}", self.provider_name, False)

    def plan(self, text: str) -> list[str]:
        return [line.strip(" -*•\t") for line in text.splitlines() if line.strip(" -*•\t")]


class LlamaCppReasoner(DemoReasoner):
    """Thin adapter for a local GGUF model through optional llama-cpp-python."""

    provider_name = "llama-cpp-local"

    def __init__(self, model_path: str | Path, context_window: int = 2048) -> None:
        try:
            from llama_cpp import Llama  # type: ignore[import-not-found]
        except ImportError as error:
            raise RuntimeError("Install llama-cpp-python to use a local GGUF model") from error
        self.model_path = Path(model_path).expanduser().resolve()
        if not self.model_path.exists():
            raise FileNotFoundError(self.model_path)
        self._model = Llama(model_path=self.model_path.as_posix(), n_ctx=context_window, verbose=False)

    def explain(self, context: Any, memories: list[str] | None = None) -> ReasoningResult:
        prompt = (
            "You are a concise private work assistant. Summarize the current work context "
            "and suggest one next step. Do not invent facts.\n\n"
            f"Context: {getattr(context, 'summary', '')}\n"
            f"Application: {getattr(context, 'active_application', '')}\n"
            f"Related memory: {' | '.join(memories or [])}\n"
            "Answer in two short sentences."
        )
        response = self._model(prompt, max_tokens=120, temperature=0.15, stop=["</s>"])
        text = str(response["choices"][0]["text"]).strip()
        return ReasoningResult(text or "No local model response was produced.", self.provider_name, True)


def build_reasoner(model_path: str | Path | None = None) -> DemoReasoner:
    if model_path:
        try:
            return LlamaCppReasoner(model_path)
        except (FileNotFoundError, RuntimeError):
            pass
    return DemoReasoner()
