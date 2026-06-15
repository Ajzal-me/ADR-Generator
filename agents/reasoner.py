import chromadb
import ollama
from state import ADRState
from agents.collector import search  # reuse search function you already wrote

def reasoner(state: ADRState) -> ADRState:
    clusters = state["clusters"]
    index    = state["current_cluster_index"]
    cluster  = clusters[index]
    theme    = cluster["theme"]
    prs      = cluster["prs"]
    
    # get commits relevant to THIS cluster's theme
    client = chromadb.PersistentClient(path="chroma_store")
    commits_col = client.get_or_create_collection("commits")
    relevant_commits = search(theme, commits_col, n_results=5)
    
    # now build context — no duplication
    pr_text = ""
    for pr in prs:
        pr_text+=f"Title:{pr['title']}\n"
        pr_text+=f"Body:{pr['body'][:500]}\n\n"
        
    commit_text = ""
    for commit in relevant_commits:
        commit_text+=f"Author: {commit['author']}\n"
        commit_text+=f"Text: {commit['text']}\n\n"
        
    response = ollama.chat(
        model="mistral",
        messages=[{
            "role": "user",
            "content": f"""You are an expert software architect analyzing a codebase. 
            Based on these pull requests about "{theme}":{pr_text} 
            And these related commits:{commit_text}

            Write an Architectural Decision Record (ADR) with exactly these three sections:
            ## Decision
            What was decided?

            ## Reasoning  
            Why was this decision made? What problem did it solve?

            ## Consequences
            What are the consequences — positive and negative?

            Be specific and concise. Base everything only on the PR and commit information provided."""
        }]
    )
        
    
    adr_text = f"# ADR: {theme}\n\n"
    adr_text += response["message"]["content"]  # get content from response
    
    # get existing draft_adrs or empty list if first time
    existing_adrs = state.get("draft_adrs", [])
    
    return {
        "draft_adrs": existing_adrs + [adr_text],          # add new ADR
        "current_cluster_index": index + 1           # increment by?
    }