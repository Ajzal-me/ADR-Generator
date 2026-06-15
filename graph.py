from langgraph.graph import StateGraph, END
from state import ADRState
from agents.collector import collector
from agents.clusterer import clusterer
from agents.reasoner import reasoner
from agents.writer import writer

def should_continue(state:ADRState):
    current_idx = state['current_cluster_index']
    if current_idx < len(state["clusters"]):
        return "continue"
    return "done"
    


graph = StateGraph(ADRState)

graph.add_node("collector",collector)
graph.add_node("clusterer",clusterer)
graph.add_node("reasoner",reasoner)
graph.add_node("writer",writer)

graph.set_entry_point("collector")

graph.add_edge("collector","clusterer")
graph.add_edge("clusterer","reasoner")

graph.add_conditional_edges(
    "reasoner",
    should_continue,
    {
        "continue": "reasoner",
        "done":"writer"
    }
)

graph.add_edge("writer",END)
app=graph.compile()

if __name__ == "__main__":
    result = app.invoke({
        "repo": "encode/httpx",
        "topic": "authentication",
        "relevant_prs": [],
        "relevant_commits": [],
        "clusters": [],
        "draft_adrs": [],
        "final_adrs": [],
        "current_cluster_index": 0,
        "errors": []
    })
    
    print("\nDone! ADRs saved:")
    for path in result["final_adrs"]:
        print(f"  {path}")