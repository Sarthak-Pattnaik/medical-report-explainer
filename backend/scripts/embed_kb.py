from sqlalchemy import text

from app.core.database import engine
from app.services.knowledge_base import (
    EMBEDDING_DIMENSIONS,
    embed_text,
)


def main():
    with engine.begin() as connection:
        entries = connection.execute(
            text("""
                SELECT id, topic, category, content, source
                FROM public.kb_entries
                WHERE embedding IS NULL
            """)
        ).mappings().all()

        print(f"Entries needing embeddings: {len(entries)}")

        for entry in entries:
            content_parts = [
                entry["topic"],
                entry["category"],
                entry["content"],
                entry["source"],
            ]

            combined_text = "\n".join(
                str(part)
                for part in content_parts
                if part
            )

            embedding = embed_text(combined_text)

            if len(embedding) != EMBEDDING_DIMENSIONS:
                raise ValueError("Expected a 384-dimensional embedding")

            connection.execute(
                text("""
                    UPDATE public.kb_entries
                    SET embedding = CAST(:embedding AS extensions.vector)
                    WHERE id = :id
                """),
                {
                    "id": entry["id"],
                    "embedding": str(embedding),
                },
            )

            print(f"Embedded: {entry['id']}")

    print("Embedding generation completed.")


if __name__ == "__main__":
    main()