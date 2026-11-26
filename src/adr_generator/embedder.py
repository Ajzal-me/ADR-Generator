from typing import Any, cast

import chromadb
import ollama

from .database import get_connection
from .settings import get_settings


def load_commits(repo: str) -> list[tuple[Any, ...]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM commits WHERE repo = ?", (repo,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def load_pull_requests(repo: str) -> list[tuple[Any, ...]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pull_requests WHERE repo = ?", (repo,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def load_comments(repo: str) -> list[tuple[Any, ...]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM comments WHERE repo = ?", (repo,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def load_issues(repo: str) -> list[tuple[Any, ...]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM issues WHERE repo = ?", (repo,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def embed_text(text: str, max_chars: int = 2000) -> list[float]:
    text = text[:max_chars]
    response = ollama.embeddings(model=get_settings().embed_model, prompt=text)
    return cast(list[float], response["embedding"])


def embed_commits(collection: Any, repo: str) -> None:
    commits = load_commits(repo)
    for commit in commits:
        sha, author, message, date, repo_name = commit
        embedding = embed_text(message)
        collection.add(
            ids=[sha],
            embeddings=[embedding],
            metadatas=[
                {
                    "text": message,
                    "author": author,
                    "date": date,
                    "sha": sha,
                    "repo": repo_name,
                }
            ],
        )
    print(f"Embedded {len(commits)} commits")


def embed_pull_requests(collection: Any, repo: str) -> None:
    prs = load_pull_requests(repo)
    for pr in prs:
        id, title, body, state, author, created_at, merged_at, repo_name = pr
        body = body or ""
        text_to_embed = f"{title}. {body}".strip()
        embedding = embed_text(text_to_embed)
        collection.add(
            ids=[f"pr_{id}"],
            embeddings=[embedding],
            metadatas=[
                {
                    "title": title,
                    "body": body,
                    "state": state,
                    "author": author,
                    "created_at": created_at,
                    "merged_at": merged_at or "",
                    "repo": repo_name,
                }
            ],
        )
    print(f"Embedded {len(prs)} pull requests")


def embed_comments(collection: Any, repo: str) -> None:
    comments = load_comments(repo)
    for comment in comments:
        id, pr_number, author, body, created_at, repo_name = comment
        body = body or ""
        if not body.strip():  # skip empty comments
            continue
        embedding = embed_text(body)
        collection.add(
            ids=[f"comment_{id}"],
            embeddings=[embedding],
            metadatas=[
                {
                    "body": body,
                    "author": author,
                    "pr_number": str(pr_number) if pr_number else "",
                    "created_at": created_at,
                    "repo": repo_name,
                }
            ],
        )
    print(f"Embedded {len(comments)} comments")


def embed_issues(collection: Any, repo: str) -> None:
    issues = load_issues(repo)
    for issue in issues:
        id, title, body, state, author, created_at, repo_name = issue
        body = body or ""
        text_to_embed = f"{title}. {body}".strip()
        embedding = embed_text(text_to_embed)
        collection.add(
            ids=[f"issue_{id}"],
            embeddings=[embedding],
            metadatas=[
                {
                    "title": title,
                    "body": body,
                    "state": state,
                    "author": author,
                    "created_at": created_at,
                    "repo": repo_name,
                }
            ],
        )
    print(f"Embedded {len(issues)} issues")


def run_embedder(repo: str) -> None:
    settings = get_settings()
    client = chromadb.PersistentClient(path=str(settings.chroma_path))
    commits_col = client.get_or_create_collection("commits")
    prs_col = client.get_or_create_collection("pull_requests")
    issues_col = client.get_or_create_collection("issues")
    comments_col = client.get_or_create_collection("comments")
    embed_commits(commits_col, repo)
    embed_pull_requests(prs_col, repo)
    embed_comments(comments_col, repo)
    embed_issues(issues_col, repo)
