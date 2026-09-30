"""Small, dependency-free local text embeddings for the MVP.

The prototype uses signed feature hashing instead of a cloud API or a large
model. It is deterministic, fast, private, and good enough to retrieve
related work notes on a laptop. A real ONNX embedding model can be plugged in
later through the same ``embed`` contract.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass


TOKEN_PATTERN = re.compile(r"[a-z0-9_]+", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class EmbeddingConfig:
    dimensions: int = 256


class LocalTextEmbedder:
    """Deterministic signed feature-hash embedding with word and character features."""

    provider_name = "local-feature-hash-v1"

    def __init__(self, config: EmbeddingConfig | None = None) -> None:
        self.config = config or EmbeddingConfig()
        if self.config.dimensions < 32:
            raise ValueError("Embedding dimensions must be at least 32")

    def embed(self, text: str) -> tuple[float, ...]:
        vector = [0.0] * self.config.dimensions
        normalized = " ".join(TOKEN_PATTERN.findall(text.lower()))
        tokens = normalized.split()
        features = list(tokens)
        features.extend(f"{tokens[index]}_{tokens[index + 1]}" for index in range(len(tokens) - 1))
        for token in tokens:
            padded = f"^{token}$"
            features.extend(padded[index : index + 3] for index in range(len(padded) - 2))
        for feature in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "little") % self.config.dimensions
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[bucket] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            vector = [value / norm for value in vector]
        return tuple(vector)


def cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    """Return cosine similarity for two normalized or unnormalized vectors."""

    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0
