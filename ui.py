import streamlit as st
import os
import shutil
from urllib.parse import urlparse

from github_collector import load_data
from database import create_tables, save_data
from embedder import run_embedder
from graph import app
import chromadb
from agents.collector import search
import ollama



st.set_page_config(page_title="ADR Generator", layout="wide")
st.title("ADR Generator")
st.caption("Automatically generate Architectural Decision Records from any GitHub repository")

try:
    ollama.embeddings(model="nomic-embed-text", prompt="test")
except Exception:
    st.error("Ollama is not running. Please start Ollama and refresh.")
    st.stop()


with st.sidebar:
    st.header("Reporsitory")
    repo_url = st.text_input(
        "Github URL",placeholder="https://github.com/owner/repo"
    )
    
    token = st.text_input(
        "GitHub Token",
        type="password",
        placeholder="ghp_...",
        help="Generate at github.com → Settings → Developer Settings → Personal Access Tokens"
    )
    
    if st.button("Collect Data", type="primary",use_container_width=True):
        if not repo_url:
            st.error("Please enter a valid GitHub URL")
        elif not token:
            st.error("Please enter a github token")
        else:
            try:
                parts = urlparse(repo_url).path.strip("/").split("/")
                full_repo = f"{parts[0]}/{parts[1]}"
                
                with st.spinner(f"Fetching data from {full_repo}..."):
                    data = load_data(repo_url, token)
                    create_tables()
                    save_data(
                        full_repo,
                        data["pull_requests"],
                        data["commits"],
                        data["comments"],
                        data["issues"]
                    )
                st.success(f"Collected: {len(data['commits'])} commits, {len(data['pull_requests'])} PRs")
                
                # step 2 — embed into chromadb
                with st.spinner("Embedding into ChromaDB..."):
                    if st.session_state.get("embedded_repo") != full_repo:
                        # wait for chromadb to release files
                        import time
                        import gc
                        gc.collect()
                        time.sleep(1)
                        
                        if os.path.exists("chroma_store"):
                            try:
                                shutil.rmtree("chroma_store")
                            except Exception:
                                st.warning("Could not clear old ChromaDB — using existing data")   # now safe to delete
                                            
                        run_embedder(full_repo)
                
                        st.session_state.repo_ready = True
                        st.session_state.full_repo  = full_repo
                        st.success("✅ Ready — enter a topic below")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # show current repo if already collected
    if st.session_state.get("repo_ready"):
        st.divider()
        st.success(f"Active repo: `{st.session_state.full_repo}`")
        

if not st.session_state.get("repo_ready"):
    st.info("Enter a Github url and token in the sidebar to get started")
else:
    tab1,tab2 = st.tabs(["Generate ADR","Ask Questions"])
    
    with tab1:
        st.header("Generate ADR")
        
        col1,col2 = st.columns([3,1])
        
        with col1:
            topic = st.text_input(
                "Topic to Explore",
                placeholder="e.g. authentication, performance etc."
            )
            
        with col2: 
            n_results = st.slider("PRs to retrieve",min_value =5,max_value=25,value=15)
            
        if st.button("Generate ADRs", type="primary",use_container_width=True):
            if not topic:
                st.error("Enter a topic")
            else:
                if os.path.exists("adr_output"):
                    shutil.rmtree("adr_output")
                
                progress = st.empty()
                
                try:
                    progress.info("Collector Agent Running")
                    
                    result = app.invoke({
                    "repo": st.session_state.full_repo,
                    "topic": topic,
                    "n_results" : n_results,
                    "relevant_prs": [],
                    "relevant_commits": [],
                    "clusters": [],
                    "draft_adrs": [],
                    "final_adrs": [],
                    "current_cluster_index": 0,
                    "errors": []
                })
                    
                    st.session_state.adrs = result['final_adrs']
                    st.session_state.topic = topic
                    progress.success(f"✅ Generated {len(result['final_adrs'])} ADRs")
                
                except Exception as e:
                    progress.error(f"Error: {str(e)}")
                        
        if st.session_state.get("adrs"):
            st.divider()
            st.subheader(f"ADRs for: *{st.session_state.get('topic', '')}*")
            
            for filepath in st.session_state.adrs:
                if os.path.exists(filepath):
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    name = os.path.basename(filepath)
                    
                    with st.expander(f"📄 {name}", expanded=True):
                        st.markdown(content)
                        
                        # download button for each ADR
                        st.download_button(
                            label="⬇️ Download",
                            data=content,
                            file_name=name,
                            mime="text/markdown"
                        )
                            
    # tab2 for chats
    with tab2:
        st.header("Ask about this repository")
        st.caption("Ask anything — what decisions were made, who worked on what, when things changed")
        
        # chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # chat input
        question = st.chat_input("Ask anything about this repository...")
        
        if question:
            # add user message to history
            st.session_state.chat_history.append({
                "role": "user",
                "content": question
            })
            
            with st.chat_message("user"):
                st.markdown(question)
            
            with st.chat_message("assistant"):
                with st.spinner("Searching repository..."):
                    try:
                        client      = chromadb.PersistentClient(path="chroma_store")
                        prs_col     = client.get_or_create_collection("pull_requests")
                        commits_col = client.get_or_create_collection("commits")
                        
                        relevant_prs     = search(question, prs_col,     n_results=5)
                        relevant_commits = search(question, commits_col,  n_results=5)
                        
                        context = "Relevant Pull Requests:\n"
                        for pr in relevant_prs:
                            context += f"- {pr['title']} by {pr['author']} ({pr.get('created_at', '')[:10]})\n"
                            context += f"  {pr['body'][:300]}\n\n"
                        
                        context += "Relevant Commits:\n"
                        for c in relevant_commits:
                            context += f"- {c['text']} by {c['author']} ({c.get('date', '')[:10]})\n"
                        
                        response = ollama.chat(
                            model="mistral",
                            messages=[{
                                "role": "user",
                                "content": f"""You are an expert software architect analyzing a GitHub repository.
                                Answer this question: "{question}"
                                Based on this repository data:{context}
                                Be specific, concise, and reference actual PRs and commits where relevant."""
                            }]
                        )
                        
                        answer = response["message"]["content"]
                        st.markdown(answer)
                        
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": answer
                        })
                        
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
