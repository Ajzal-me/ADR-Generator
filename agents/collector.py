import chromadb
import ollama
from state import ADRState
from config import REPO_URL
from urllib.parse import urlparse

def get_repo():
    owner,repo = urlparse(REPO_URL).path.strip("/").split("/")
    return f"{owner}/{repo}"

def search(query, collection, n_results=15):
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
    
    client = chromadb.PersistentClient(path="chroma_store")
    prs_col = client.get_or_create_collection("pull_requests")
    commits_col = client.get_or_create_collection("commits")
    
    relevant_prs = search(topic,prs_col)
    relevant_commits = search(topic,commits_col)
    
    print(f"Collector found {len(relevant_prs)} PRs and {len(relevant_commits)} commits for topic: '{topic}'")
    
    return {
    "relevant_prs": relevant_prs,
    "relevant_commits": relevant_commits
    }
    
    