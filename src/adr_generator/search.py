from typing import Any, cast

import chromadb
import ollama

from .repo import parse_repo_url
from .settings import get_settings


def search(query: str, collection: Any, n_results: int = 3) -> list[dict[str, Any]]:
    query_embedding = ollama.embeddings(model=get_settings().embed_model, prompt=query)["embedding"]

    results = collection.query(query_embeddings=query_embedding, n_results=n_results)

    return cast(list[dict[str, Any]], results["metadatas"][0])


if __name__ == "__main__":
    settings = get_settings()
    repo = parse_repo_url(settings.repo_url).full

    client = chromadb.PersistentClient(path=str(settings.chroma_path))
    prs_col = client.get_or_create_collection("pull_requests")

    queries = [
        "performance optimization",
        "security vulnerability fix",
        "breaking changes to the API",
        "authentication and authorization",
    ]

    for query in queries:
        print(f"\n{'=' * 50}")
        print(f"Query: '{query}'")
        print("=" * 50)
        results = search(query, prs_col)
        for i, r in enumerate(results):
            print(f"\nResult {i + 1}: {r['title']}")
            print(f"Author: {r['author']} | State: {r['state']}")
            print(f"Body preview: {r['body'][:150]}...")
