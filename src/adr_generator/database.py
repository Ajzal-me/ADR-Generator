import logging
import sqlite3
from contextlib import closing
from typing import Any

from .settings import get_settings

logger = logging.getLogger(__name__)


def get_connection() -> sqlite3.Connection:
    path = get_settings().db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(path)


def create_tables() -> None:
    # NOTE: keep the column order — embedder.py unpacks rows by position.
    with closing(get_connection()) as conn, conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS commits (
            sha TEXT,
            author TEXT,
            message TEXT,
            date TEXT,
            repo TEXT,
            PRIMARY KEY (repo, sha)
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS pull_requests (
            number INTEGER,
            title TEXT,
            body TEXT,
            state TEXT,
            author TEXT,
            created_at TEXT,
            merged_at TEXT,
            repo TEXT,
            PRIMARY KEY (repo, number)
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER,
            pr_number INTEGER,
            author TEXT,
            body TEXT,
            created_at TEXT,
            repo TEXT,
            PRIMARY KEY (repo, id)
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS issues (
            number INTEGER,
            title TEXT,
            body TEXT,
            state TEXT,
            author TEXT,
            created_at TEXT,
            repo TEXT,
            PRIMARY KEY (repo, number)
        )
        """)
    logger.info("Tables ready")


def _login(user: dict[str, Any] | None) -> str:
    """GitHub sends user=null for deleted accounts."""
    return (user or {}).get("login") or "ghost"


def save_data(
    repo: str,
    prs: list[dict[str, Any]],
    commits: list[dict[str, Any]],
    comments: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> None:
    with closing(get_connection()) as conn, conn:  # `conn` as a context manager = one transaction
        conn.executemany(
            """
            INSERT OR REPLACE INTO pull_requests
                (number, title, body, state, author, created_at, merged_at, repo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    pr["number"],
                    pr["title"],
                    pr.get("body") or "",
                    pr["state"],
                    _login(pr.get("user")),
                    pr["created_at"],
                    pr.get("merged_at"),
                    repo,
                )
                for pr in prs
            ],
        )
        conn.executemany(
            """
            INSERT OR REPLACE INTO commits (sha, author, message, date, repo)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    c["sha"],
                    (c["commit"].get("author") or {}).get("name") or "unknown",
                    c["commit"]["message"],
                    (c["commit"].get("author") or {}).get("date") or "",
                    repo,
                )
                for c in commits
            ],
        )
        conn.executemany(
            """
            INSERT OR REPLACE INTO comments (id, pr_number, author, body, created_at, repo)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    c["id"],
                    c.get("pr_number"),
                    _login(c.get("user")),
                    c.get("body") or "",
                    c["created_at"],
                    repo,
                )
                for c in comments
            ],
        )
        conn.executemany(
            """
            INSERT OR REPLACE INTO issues (number, title, body, state, author, created_at, repo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    i["number"],
                    i["title"],
                    i.get("body") or "",
                    i["state"],
                    _login(i.get("user")),
                    i["created_at"],
                    repo,
                )
                for i in issues
            ],
        )
    logger.info(
        "Saved %s: %d PRs, %d commits, %d comments, %d issues",
        repo, len(prs), len(commits), len(comments), len(issues),
    )