
from app.services.knowledge_base import search_kb


def main():
    query = "What does a low haemoglobin result mean?"

    results = search_kb(query, top_k=5)

    print(f"Query: {query}")
    print(f"Results found: {len(results)}")

    for index, result in enumerate(results, start=1):
        print(f"\nResult {index}")
        print(f"Score: {result['score']:.4f}")
        print(f"Source: {result['source']}")
        print(f"Content: {result['content'][:500]}")


if __name__ == "__main__":
    main()
