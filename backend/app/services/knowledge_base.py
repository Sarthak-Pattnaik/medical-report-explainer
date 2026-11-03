
from functools import lru_cache

from sqlalchemy import text

from app.core.database import engine


MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model():
    """Load the embedding model once and reuse it."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def search_kb(
    query_text: str,
    top_k: int = 5,
) -> list[dict]:

    if not query_text or not query_text.strip():
        return []

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    model = get_embedding_model()

    query_embedding = model.encode(
        query_text.strip(),
        normalize_embeddings=True,
    ).tolist()

    if len(query_embedding) != 384:
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
