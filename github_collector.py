import requests
from urllib.parse import urlparse
from dotenv import load_dotenv
import os
from database import create_tables, save_data


load_dotenv()
token = os.getenv('TOKEN')

def paginate(url, headers,max_pages=3):
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
    pr_comments = []
    # for pr in prs:
    #     comments = paginate(
    #         f"https://api.github.com/repos/{owner}/{repo}/issues/{pr['number']}/comments",
    #         headers
    #     )
    #     for comment in comments:
    #         comment["pr_number"] = pr["number"]
    #     pr_comments.extend(comments)
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


#to be fixed
if __name__ == "__main__":
    data = load_data(url,token)
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