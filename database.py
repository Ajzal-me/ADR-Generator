import sqlite3

def get_connnection():
    return sqlite3.connect("github_data.db")


def create_tables():
    conn = get_connnection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS commits (
        sha TEXT PRIMARY KEY,
        author TEXT,
        message TEXT,
        date TEXT
    )                          
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pull_requests (
        id INTEGER PRIMARY KEY,
        title TEXT,
        state TEXT,
        author TEXT,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY,
        user TEXT,
        body TEXT,
        created_at TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def save_data(prs,commits):
    conn = get_connnection()
    cursor = conn.cursor()

    for pr in prs:
        cursor.execute("""
        INSERT OR REPLACE INTO pull_requests
        VALUES (?, ?, ?, ?, ?)
        """, (
            pr["number"],
            pr["title"],
            pr["state"],
            pr["user"]["login"],
            pr["created_at"]
        ))
        
        
    for commit in commits:
        cursor.execute("""
        INSERT OR REPLACE INTO commits
        VALUES (?, ?, ?, ?)
        """, (
            commit["sha"],
            commit["commit"]["author"]["name"],
            commit["commit"]["message"],
            commit["commit"]["author"]["date"]
        ))

    conn.commit()
    conn.close()

