from typing import Literal, cast

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph

from .agents.clusterer import clusterer
from .agents.collector import collector
from .agents.reasoner import reasoner
from .agents.writer import writer
from .state import ADRState

load_dotenv(override=True)


def should_continue(state: ADRState) -> Literal["continue", "done"]:
    current_idx = state["current_cluster_index"]

    if current_idx < len(state["clusters"]):
        return "continue"

    return "done"

graph = StateGraph(ADRState)

graph.add_node("collector", collector)
graph.add_node("clusterer", clusterer)
graph.add_node("reasoner", reasoner)
graph.add_node("writer", writer)

graph.set_entry_point("collector")

graph.add_edge("collector", "clusterer")
graph.add_edge("clusterer", "reasoner")

graph.add_conditional_edges("reasoner", should_continue, {"continue": "reasoner", "done": "writer"})

graph.add_edge("writer", END)
app = graph.compile()


def run_graph(repo: str, topic: str, n_results: int = 15) -> ADRState:
    result = app.invoke(
        {
            "repo": repo,
            "topic": topic,
            "n_results": n_results,
            "relevant_prs": [],
            "relevant_commits": [],
            "clusters": [],
            "draft_adrs": [],
            "final_adrs": [],
            "current_cluster_index": 0,
            "errors": [],
            "eval_contexts": [],
        }
    )

    return cast(ADRState,result)
