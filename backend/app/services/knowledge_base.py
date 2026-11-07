from functools import lru_cache

import numpy as np
from sqlalchemy import text

from app.core.database import engine


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384


@lru_cache(maxsize=1)
def get_embedding_model():
    """Load the ONNX embedding model once and reuse it."""
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=MODEL_NAME)


def embed_text(text_to_embed: str) -> list[float]:
    """Return a normalized 384-dimensional embedding."""
    model = get_embedding_model()

    vector = next(model.embed([text_to_embed]))
    vector = vector / np.linalg.norm(vector)

    return vector.tolist()


def search_kb(
    query_text: str,
    top_k: int = 5,
) -> list[dict]:

    if not query_text or not query_text.strip():
        return []

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    query_embedding = embed_text(query_text.strip())

    if len(query_embedding) != EMBEDDING_DIMENSIONS:
        raise ValueError("Expected a 384-dimensional embedding")

    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT *
                FROM public.search_kb(
                    CAST(:query_embedding AS extensions.vector),
                    :top_k
                )
            """),
            {
                "query_embedding": str(query_embedding),
                "top_k": top_k,
            },
        ).mappings().all()

    return [
        {
            "content": row["content"],
            "source": row["source"] or "",
            "score": float(row["score"]),
        }
        for row in rows
    ]