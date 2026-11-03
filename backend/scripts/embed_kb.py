
from sentence_transformers import SentenceTransformer
from sqlalchemy import text

from app.core.database import engine

MODEL_NAME = "all-MiniLM-L6-v2"

def main():
    model = SentenceTransformer(MODEL_NAME)

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

            embedding = model.encode(
                combined_text,
                normalize_embeddings=True,
            ).tolist()

            if len(embedding) != 384:
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
