"""Local semantic memory facade used by the dashboard and reasoning layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.memory.embeddings import LocalTextEmbedder, cosine_similarity
from app.memory.semantic_repository import SemanticMemoryRepository, StoredMemory


@dataclass(frozen=True, slots=True)
class MemoryHit:
    memory: StoredMemory
    score: float


class SemanticMemory:
    """Store and retrieve related local notes without network access."""

    def __init__(self, repository: SemanticMemoryRepository, embedder: LocalTextEmbedder | None = None) -> None:
        self.repository = repository
        self.embedder = embedder or LocalTextEmbedder()

    @property
    def provider_name(self) -> str:
        return self.embedder.provider_name

    def remember(self, text: str, memory_type: str = "note", metadata: dict[str, Any] | None = None) -> StoredMemory:
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("Memory text cannot be empty")
        return self.repository.add(memory_type, cleaned, metadata or {}, self.embedder.embed(cleaned))

    def search(self, query: str, limit: int = 5, minimum_score: float = 0.05) -> list[MemoryHit]:
        query_vector = self.embedder.embed(query)
        hits = [
            MemoryHit(memory, cosine_similarity(query_vector, memory.embedding))
            for memory in self.repository.recent()
        ]
        hits = [hit for hit in hits if hit.score >= minimum_score]
        hits.sort(key=lambda hit: (hit.score, hit.memory.created_at), reverse=True)
        return hits[: max(0, limit)]

    def remember_context(self, summary: str, project_context: str | None = None) -> StoredMemory:
        metadata = {"project_context": project_context} if project_context else {}
        return self.remember(summary, memory_type="context", metadata=metadata)
