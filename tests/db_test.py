import pytest

from adr_generator.database import create_tables, get_connection, save_data
from adr_generator.settings import get_settings


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Point the app at a throw-away data folder for every test."""
    monkeypatch.setenv("ADR_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    create_tables()
    yield
    get_settings.cache_clear()


def make_pr(number, title, user="alice"):
    return {
        "number": number,
        "title": title,
        "body": "body",
        "state": "closed",
        "user": {"login": user} if user else None,
        "created_at": "2024-01-01T00:00:00Z",
        "merged_at": None,
    }


def titles(repo):
    conn = get_connection()
    rows = conn.execute("SELECT title FROM pull_requests WHERE repo = ?", (repo,)).fetchall()
    conn.close()
    return [r[0] for r in rows]


def test_same_pr_number_in_two_repos_does_not_collide():
    save_data("a/x", [make_pr(5, "from A")], [], [], [])
    save_data("b/y", [make_pr(5, "from B")], [], [], [])
    assert titles("a/x") == ["from A"]
    assert titles("b/y") == ["from B"]


def test_saving_twice_updates_instead_of_duplicating():
    save_data("a/x", [make_pr(5, "old")], [], [], [])
    save_data("a/x", [make_pr(5, "new")], [], [], [])
    assert titles("a/x") == ["new"]


def test_deleted_user_becomes_ghost():
    save_data("a/x", [make_pr(1, "t", user=None)], [], [], [])
    conn = get_connection()
    author = conn.execute("SELECT author FROM pull_requests").fetchone()[0]
    conn.close()
    assert author == "ghost"


def test_comments_and_issues_are_saved_per_repo():
    comment = {"id": 9, "pr_number": 5, "user": None, "body": "hi", "created_at": "2024-01-02T00:00:00Z"}
    issue = {"number": 5, "title": "bug", "body": None, "state": "open",
             "user": {"login": "bob"}, "created_at": "2024-01-03T00:00:00Z"}
    save_data("a/x", [], [], [comment], [issue])
    save_data("b/y", [], [], [], [issue])
    conn = get_connection()
    assert conn.execute("SELECT COUNT(*) FROM comments WHERE repo='a/x'").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM issues").fetchone()[0] == 2
    conn.close()