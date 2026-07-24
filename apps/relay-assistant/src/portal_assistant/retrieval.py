from __future__ import annotations

from typing import Any


def reciprocal_rank_fusion(
    ranked_lists: list[list[dict[str, Any]]],
    *,
    limit: int = 6,
    k: int = 60,
) -> list[dict[str, Any]]:
    """Merge multiple ranked result lists with RRF (rank fusion)."""
    scores: dict[tuple[str, str, str], float] = {}
    payloads: dict[tuple[str, str, str], dict[str, Any]] = {}

    for results in ranked_lists:
        for rank, row in enumerate(results, start=1):
            key = (row["source"], row["title"], row["content"])
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            payloads[key] = row

    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    merged: list[dict[str, Any]] = []
    for key, rrf_score in ordered[:limit]:
        row = dict(payloads[key])
        row["rrf_score"] = rrf_score
        merged.append(row)
    return merged
