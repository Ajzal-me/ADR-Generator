import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

from .config import MAX_PAGES

load_dotenv()
token: str | None = os.getenv("TOKEN")


def get_comments_for_pr(
    pr: dict[str, Any], owner: str, repo: str, headers: dict[str, str]
) -> list[dict[str, Any]]:
    comments = paginate(
        f"https://api.github.com/repos/{owner}/{repo}/issues/{pr['number']}/comments",
        headers,
    )
    for comment in comments:
        comment["pr_number"] = pr["number"]
    return comments


def get_all_pr_comments(
    prs: list[dict[str, Any]], owner: str, repo: str, headers: dict[str, str]
) -> list[dict[str, Any]]:
    pr_comments: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_comments_for_pr, pr, owner, repo, headers): pr for pr in prs}
        completed = 0
        for future in as_completed(futures):
            comments = future.result()
            pr_comments.extend(comments)
            completed += 1
            print(f"  Comments fetched: {completed}/{len(prs)} PRs", end="\r")
    print()
    return pr_comments


def paginate(
    url: str, headers: dict[str, str], max_pages: int = MAX_PAGES
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    page = 1
    while True:
        if page > max_pages:
            break
        response = requests.get(url, headers=headers, params={"page": page, "per_page": 100}).json()
        if isinstance(response, dict) and "message" in response:
            print(f"API error: {response['message']}")
            break
        if not response:
            break
        results.extend(response)
        page += 1
    return results


def load_data(url: str, token: str | None) -> dict[str, list[dict[str, Any]]]:

    parts = urlparse(url).path.strip("/").split("/")
    owner, repo = parts[0], parts[1]

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    print(f"Collecting data for {owner}/{repo}...")

    print("Fetching commits...")
    commits = paginate(f"https://api.github.com/repos/{owner}/{repo}/commits", headers)
    print(f"  Found {len(commits)} commits")

    print("Fetching pull requests...")
    prs = paginate(f"https://api.github.com/repos/{owner}/{repo}/pulls?state=all", headers)
    print(f"  Found {len(prs)} pull requests")

    print("Fetching PR comments...")
    pr_comments = get_all_pr_comments(prs, owner, repo, headers)
    print(f"  Found {len(pr_comments)} comments")

    print("Fetching issues...")
    issues = paginate(f"https://api.github.com/repos/{owner}/{repo}/issues?state=all", headers)
    real_issues = [i for i in issues if "pull_request" not in i]
    print(f"  Found {len(real_issues)} issues")

    return {
        "commits": commits,
        "pull_requests": prs,
        "comments": pr_comments,
        "issues": real_issues,
    }
