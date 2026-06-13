import ollama
import chromadb
from urllib.parse import urlparse
from config import REPO_URL

def search(query, collection, n_results=3):
    query_embedding = ollama.embeddings(
        model="nomic-embed-text",
        prompt=query
    )["embedding"]
    
    results = collection.query(
        query_embeddings = query_embedding,
        n_results = n_results
    )
    
    return results["metadatas"][0]


if __name__ == "__main__":
    parts = urlparse(REPO_URL).path.strip("/").split("/")
    repo = f"{parts[0]}/{parts[1]}"
    
    client = chromadb.PersistentClient(path="chroma_store")
    prs_col = client.get_or_create_collection("pull_requests")
    
    queries = [
        "performance optimization",
        "security vulnerability fix",
        "breaking changes to the API",
        "authentication and authorization"
    ]
    
    for query in queries:
        print(f"\n{'='*50}")
        print(f"Query: '{query}'")
        print('='*50)
        results = search(query, prs_col)
        for i, r in enumerate(results):
            print(f"\nResult {i+1}: {r['title']}")
            print(f"Author: {r['author']} | State: {r['state']}")
            print(f"Body preview: {r['body'][:150]}...")