from portal_assistant.embeddings import embed_text
from portal_assistant.retrieval import reciprocal_rank_fusion


def test_embed_text_is_deterministic():
    a = embed_text("golden path gitops", dimensions=32)
    b = embed_text("golden path gitops", dimensions=32)
    assert a == b
    assert len(a) == 32


def test_reciprocal_rank_fusion_prefers_overlap():
    fts = [
        {"source": "a", "title": "A", "content": "one", "rank": 0.9},
        {"source": "b", "title": "B", "content": "two", "rank": 0.5},
    ]
    vec = [
        {"source": "b", "title": "B", "content": "two", "vec_score": 0.8},
        {"source": "c", "title": "C", "content": "three", "vec_score": 0.7},
    ]
    merged = reciprocal_rank_fusion([fts, vec], limit=2)
    assert merged[0]["title"] == "B"
    assert len(merged) == 2
