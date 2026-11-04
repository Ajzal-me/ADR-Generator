from typing import Any, cast

import chromadb
import ollama
from langsmith import traceable

from ..state import ADRState


def search(query: str, collection: Any, n_results: int) -> list[dict[str, Any]]:
    query_embeddings = ollama.embeddings(model="nomic-embed-text", prompt=query)["embedding"]

    results = collection.query(query_embeddings=[query_embeddings], n_results=n_results)

    return cast(list[dict[str, Any]], results["metadatas"][0])


@traceable(name="collector_agent", run_type="chain")
def collector(state: ADRState) -> ADRState:
    topic = state["topic"]
    n_results = state["n_results"]

    client = chromadb.PersistentClient(path="chroma_store")
    prs_col = client.get_or_create_collection("pull_requests")
    commits_col = client.get_or_create_collection("commits")

    relevant_prs = search(topic, prs_col, n_results)
    relevant_commits = search(topic, commits_col, n_results)

    print(f"Collector found {len(relevant_prs)} PRs and {len(relevant_commits)} commits for topic: '{topic}'")

    return {"relevant_prs": relevant_prs, "relevant_commits": relevant_commits}
