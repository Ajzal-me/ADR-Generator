from typing import TypedDict, List

class ADRState(TypedDict):
    repo: str
    topic: str
    n_results: int
    relevant_prs: List[dict]
    relevant_commits: List[dict]
    clusters: List[dict]
    draft_adrs: List[str]
    final_adrs: List[str]
    current_cluster_index: int
    errors: List[str]
