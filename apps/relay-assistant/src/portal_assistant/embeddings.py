from __future__ import annotations

import hashlib
import math


def embed_text(text: str, *, dimensions: int = 384) -> list[float]:
    """Deterministic local embedder — no API keys; suitable for dev/CI.

    Production can swap this provider for a hosted or on-cluster model without
    changing the store/search contract.
    """
    vec = [0.0] * dimensions
    tokens = text.lower().split()
    if not tokens:
        return vec
    for token in tokens:
        digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
        idx = int.from_bytes(digest[:4], "big") % dimensions
        vec[idx] += 1.0
    norm = math.sqrt(sum(x * x for x in vec))
    if norm <= 0:
        return vec
    return [x / norm for x in vec]


def to_vector_literal(vec: list[float]) -> str:
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"
