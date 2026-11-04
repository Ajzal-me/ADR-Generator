from typing import Any, TypedDict


class ADRState(TypedDict, total=False):
    repo: str
    topic: str
    n_results: int
    relevant_prs: list[dict[str, Any]]
    relevant_commits: list[dict[str, Any]]
    clusters: list[dict[str, Any]]
    draft_adrs: list[str]
    final_adrs: list[str]
    current_cluster_index: int
    errors: list[str]
    eval_contexts: list[dict[str, Any]]