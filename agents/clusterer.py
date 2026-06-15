import ollama
import numpy as np
from sklearn.cluster import KMeans
from state import ADRState
import json

def get_cluster_name(prs_in_cluster):
    # build a prompt for mistral to name this cluster
    pr_titles = [pr["title"] for pr in prs_in_cluster]
    titles_text = "\n".join(pr_titles)
    
    response = ollama.chat(
        model="mistral",
        messages=[{
            "role": "user",
            "content": 
                f"""
                    Here are some pull request titles that belong to the same group:{titles_text}
                    Give this group a short theme name (3-5 words maximum).Respond with ONLY the theme name, nothing else.
                """
        }]
    )
    
    return response["message"]["content"].strip()


def clusterer(state:ADRState)->ADRState:
    relevant_prs = state['relevant_prs']
    relevant_commits = state['relevant_commits']
    
    if len(relevant_prs) < 2:
        return {"clusters": [{"theme": "general", "prs": relevant_prs}]}
    
    
    vectors = []
    for pr in relevant_prs:
        embeddings = ollama.embeddings(
            model="nomic-embed-text", 
            prompt= pr['title']
        )["embedding"]
        vectors.append(embeddings)
        
    k = min(max(2, len(relevant_prs) // 4), len(relevant_prs))
    
    vectors_array = np.array(vectors)
    
    kmeans = KMeans(n_clusters=k,random_state=42, n_init="auto")
    kmeans.fit(vectors_array)
    labels = kmeans.labels_
    
    grouped = {}
    for i , pr in enumerate(relevant_prs):
        label = int(labels[i])
        if label not in grouped:
            grouped[label] = []
        grouped[label].append(pr)
        
    clusters = []
    for label,prs in grouped.items():
        print(f"  Naming cluster {label} with {len(prs)} PRs...")
        
        theme = get_cluster_name(prs)
        clusters.append({
            "theme": theme,
            "prs": prs,
            "commits":relevant_commits    
        })
        
        print(f"  Cluster: '{theme}' — {len(prs)} PRs")
        
    return {
        "clusters": clusters
    }   
