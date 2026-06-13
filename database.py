import sqlite3

def get_connection():
    return sqlite3.connect("github_data.db")

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS commits (
        sha TEXT PRIMARY KEY,
        author TEXT,
        message TEXT,
        date TEXT,
        repo TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pull_requests (
        id INTEGER PRIMARY KEY,
        title TEXT,
        body TEXT,
        state TEXT,
        author TEXT,
        created_at TEXT,
        merged_at TEXT,
        repo TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY,
        pr_number INTEGER,
        author TEXT,
        body TEXT,
        created_at TEXT,
        repo TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY,
        title TEXT,
        body TEXT,
        state TEXT,
        author TEXT,
        created_at TEXT,
        repo TEXT
    )
    """)

    conn.commit()
    conn.close()
    print("Tables created.")

def save_data(repo,prs, commits, comments, issues):
    conn = get_connection()
    cursor = conn.cursor()

    for pr in prs:
        cursor.execute("""
        INSERT OR REPLACE INTO pull_requests
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pr["number"],
            pr["title"],
            pr.get("body") or "",
            pr["state"],
            pr["user"]["login"],
            pr["created_at"],
            pr.get("merged_at"),
            repo 
        ))

    for commit in commits:
        cursor.execute("""
        INSERT OR REPLACE INTO commits
        VALUES (?, ?, ?, ?, ?)
        """, (
            commit["sha"],
            commit["commit"]["author"]["name"],
            commit["commit"]["message"],
            commit["commit"]["author"]["date"],
            repo
        ))

    for comment in comments:
        cursor.execute("""
        INSERT OR REPLACE INTO comments
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            comment["id"],
            comment.get("pr_number"),
            comment["user"]["login"],
            comment["body"],
            comment["created_at"],
            repo 
        ))

    for issue in issues:
        cursor.execute("""
        INSERT OR REPLACE INTO issues
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            issue["number"],
            issue["title"],
            issue.get("body") or "",
            issue["state"],
            issue["user"]["login"],
            issue["created_at"],
            repo 
        ))

    conn.commit()
    conn.close()
    print("Data saved.")