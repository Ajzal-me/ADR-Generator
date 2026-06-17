import chromadb
import ollama
from state import ADRState

def search(query, collection, n_results):
    query_embeddings = ollama.embeddings(
        model="nomic-embed-text",
        prompt=query
    )["embedding"]
    
    results = collection.query(
        query_embeddings = [query_embeddings],
        n_results = n_results
    )
    
    return results["metadatas"][0]

def collector(state:ADRState )-> ADRState:
    topic = state["topic"]
    repo  = state["repo"]
    n_results = state["n_results"]
    
    client = chromadb.PersistentClient(path="chroma_store")
    prs_col = client.get_or_create_collection("pull_requests")
    commits_col = client.get_or_create_collection("commits")
    
    relevant_prs = search(topic,prs_col,n_results)
    relevant_commits = search(topic,commits_col,n_results)
    
    print(f"Collector found {len(relevant_prs)} PRs and {len(relevant_commits)} commits for topic: '{topic}'")
    
    return {
    "relevant_prs": relevant_prs,
    "relevant_commits": relevant_commits
    }
    
    