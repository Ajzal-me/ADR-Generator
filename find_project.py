from dotenv import load_dotenv
load_dotenv(override=True)
from langsmith import Client
import os

c = Client()
proj = c.read_project(project_name="adr-generator")
print("Project ID:", proj.id)
print("Tenant/Workspace ID:", proj.tenant_id)
print("Endpoint in use:", os.getenv("LANGCHAIN_ENDPOINT"))
print()
print("Direct link to try:")
print(f"https://apac.smith.langchain.com/o/{proj.tenant_id}/projects/p/{proj.id}")