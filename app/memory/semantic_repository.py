"""SQLite persistence for local semantic memory."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, sessionmaker

from app.database.models import MemoryEntry


@dataclass(frozen=True, slots=True)
class StoredMemory:
    id: int
    memory_type: str
    text: str
    metadata: dict[str, Any]
    embedding: tuple[float, ...]
    created_at: datetime


class SemanticMemoryRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def add(self, memory_type: str, text: str, metadata: dict[str, Any], embedding: tuple[float, ...]) -> StoredMemory:
        with self.session_factory() as session:
            entry = MemoryEntry(
                memory_type=memory_type,
                text=text.strip(),
                metadata_json=json.dumps(metadata, default=str),
                embedding_json=json.dumps(embedding),
            )
            session.add(entry)
            session.commit()
            session.refresh(entry)
            return self._from_model(entry)

    def recent(self, limit: int = 200) -> list[StoredMemory]:
        with self.session_factory() as session:
            statement = select(MemoryEntry).order_by(desc(MemoryEntry.created_at), desc(MemoryEntry.id)).limit(limit)
            return [self._from_model(item) for item in session.scalars(statement).all()]

    def delete(self, memory_id: int) -> bool:
        with self.session_factory() as session:
            entry = session.get(MemoryEntry, memory_id)
            if entry is None:
                return False
            session.delete(entry)
            session.commit()
            return True

    @staticmethod
    def _from_model(entry: MemoryEntry) -> StoredMemory:
        try:
            metadata = json.loads(entry.metadata_json or "{}")
        except json.JSONDecodeError:
            metadata = {}
        try:
            embedding = tuple(float(value) for value in json.loads(entry.embedding_json or "[]"))
        except (json.JSONDecodeError, TypeError, ValueError):
            embedding = ()
        return StoredMemory(entry.id, entry.memory_type, entry.text, metadata, embedding, entry.created_at)
