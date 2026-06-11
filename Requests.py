import requests 
from urllib.parse import urlparse
from dotenv import load_dotenv
import os
from database import create_tables, save_data

load_dotenv()

token = os.getenv('TOKEN')

url = "https://github.com/Rizzy-2005/Exam-Duty-Management-System"

def load_data(url,token):
    parts = urlparse(url).path.strip("/").split("/")
    owner,repo = parts[0],parts[1]
    
    headers={}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    commits = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/commits",
        headers=headers
    ).json()
    
    pr = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls?state=all",
        headers=headers
    ).json()
    
    return {"commits":commits,"pull_requests":pr}
    
data = load_data(url,None)

create_tables()
save_data(data["pull_requests"], data["commits"])

print(f"Commits: {len(data['commits'])}, Pull Requests: {len(data['pull_requests'])}")
