import requests
from urllib.parse import urlparse
from dotenv import load_dotenv
import os
from database import create_tables, save_data
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import MAX_PAGES


load_dotenv()
token = os.getenv('TOKEN')

def get_comments_for_pr(pr, owner, repo, headers):
    comments = paginate(
        f"https://api.github.com/repos/{owner}/{repo}/issues/{pr['number']}/comments",
        headers
    )
    for comment in comments:
        comment["pr_number"] = pr["number"]
    return comments

def get_all_pr_comments(prs, owner, repo, headers):
    pr_comments = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(get_comments_for_pr, pr, owner, repo, headers): pr
            for pr in prs
        }
        completed = 0
        for future in as_completed(futures):
            comments = future.result()
            pr_comments.extend(comments)
            completed += 1
            print(f"  Comments fetched: {completed}/{len(prs)} PRs", end="\r")
    print()
    return pr_comments

def paginate(url, headers,max_pages=MAX_PAGES):
    results = []
    page = 1
    while True:
        if page>max_pages:
            break
        response = requests.get(
            url,
            headers=headers,
            params={"page": page, "per_page": 100}
        ).json()
        if isinstance(response, dict) and "message" in response:
            print(f"API error: {response['message']}")
            break
        if not response:
            break
        results.extend(response)
        page += 1
    return results

def load_data(url, token):
    
    parts = urlparse(url).path.strip("/").split("/")
    owner, repo = parts[0], parts[1]
    full_repo = f"{owner}/{repo}"

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    print(f"Collecting data for {owner}/{repo}...")

    print("Fetching commits...")
    commits = paginate(
        f"https://api.github.com/repos/{owner}/{repo}/commits",
        headers
    )
    print(f"  Found {len(commits)} commits")

    print("Fetching pull requests...")
    prs = paginate(
        f"https://api.github.com/repos/{owner}/{repo}/pulls?state=all",
        headers
    )
    print(f"  Found {len(prs)} pull requests")

    print("Fetching PR comments...")
    pr_comments = get_all_pr_comments(prs, owner, repo, headers)
    print(f"  Found {len(pr_comments)} comments")

    print("Fetching issues...")
    issues = paginate(
        f"https://api.github.com/repos/{owner}/{repo}/issues?state=all",
        headers
    )
    real_issues = [i for i in issues if "pull_request" not in i]
    print(f"  Found {len(real_issues)} issues")

    return {
        "commits": commits,
        "pull_requests": prs,
        "comments": pr_comments,
        "issues": real_issues
    }



if __name__ == "__main__":
    from config import REPO_URL
    data = load_data(REPO_URL, token)
    parts = urlparse(REPO_URL).path.strip("/").split("/")
    full_repo = f"{parts[0]}/{parts[1]}"
    create_tables()
    save_data(
        full_repo,
        data["pull_requests"],
        data["commits"],
        data["comments"],
        data["issues"]
    )
    print("\nDone.")
    print(f"  Commits   : {len(data['commits'])}")
    print(f"  PRs       : {len(data['pull_requests'])}")
    print(f"  Comments  : {len(data['comments'])}")
    print(f"  Issues    : {len(data['issues'])}")