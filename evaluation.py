"""
Ragas evaluation for the ADR Generator.

Scores each generated ADR against the PR/commit context it was actually
built from, using two reference-free RAG metrics:

- Faithfulness:      does the ADR stay grounded in the retrieved PRs/commits,
                     or does it hallucinate details not present in them?
- Answer Relevancy:  does the ADR actually address the cluster's theme?

Both metrics only need (question, retrieved_contexts, answer) — no hand
written ground truth required, which fits this project since nobody has
pre-written "correct" ADRs to compare against.

The judge model is a local Ollama model (mistral by default), wrapped for
Ragas via langchain-ollama, so evaluation runs fully offline like the rest
of the pipeline.
"""

import os
from ragas import evaluate, EvaluationDataset
from ragas.metrics import Faithfulness, ResponseRelevancy
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_ollama import ChatOllama, OllamaEmbeddings


def build_ragas_dataset(state):
    """
    Turn the ADRState returned by run_graph()/app.invoke() into a Ragas
    EvaluationDataset. Relies on `eval_contexts`, populated by
    agents/reasoner.py, which pairs each draft ADR with the exact PR/commit
    text it was generated from.
    """
    eval_contexts = state.get("eval_contexts") or []
    if not eval_contexts:
        raise ValueError(
            "No eval_contexts found in state — make sure agents/reasoner.py "
            "was updated to populate eval_contexts, and that you ran the "
            "graph (run_graph or app.invoke) AFTER that change."
        )

    samples = []
    for item in eval_contexts:
        samples.append({
            "user_input": item["theme"],
            "retrieved_contexts": item["contexts"],
            "response": item["response"],
        })

    return EvaluationDataset.from_list(samples)


def run_ragas_evaluation(state, judge_model="mistral", embed_model="nomic-embed-text",
                          output_csv="adr_output/ragas_eval_results.csv"):
    """
    Evaluate every ADR in `state` and return a pandas DataFrame of
    per-ADR scores. Also writes a CSV next to the generated ADR files.
    """
    dataset = build_ragas_dataset(state)

    llm = LangchainLLMWrapper(ChatOllama(model=judge_model))
    embeddings = LangchainEmbeddingsWrapper(OllamaEmbeddings(model=embed_model))

    metrics = [Faithfulness(), ResponseRelevancy()]

    result = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=llm,
        embeddings=embeddings,
    )

    df = result.to_pandas()

    if output_csv:
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        df.to_csv(output_csv, index=False)
        print(f"Saved Ragas results to {output_csv}")

    cols = [c for c in ["user_input", "faithfulness", "answer_relevancy"] if c in df.columns]
    print(df[cols] if cols else df)

    return df


if __name__ == "__main__":
    # Run this file directly to generate ADRs for a repo/topic and
    # immediately score them:
    #     python evaluation.py
    #
    # Edit REPO / TOPIC below to match a repo you've already run
    # "Collect Data" for (via ui.py or embedder.py) — this script only
    # runs the graph + evaluation, it doesn't collect/embed GitHub data.
    from graph import run_graph

    REPO = "pallets/flask"
    TOPIC = "error handling"

    print(f"Running pipeline for {REPO} / '{TOPIC}'...")
    state = run_graph(REPO, TOPIC)
    print(f"Generated {len(state['final_adrs'])} ADRs. Scoring with Ragas...")

    df = run_ragas_evaluation(state)

    if "faithfulness" in df.columns:
        print(f"\nAverage faithfulness:     {df['faithfulness'].mean():.2f}")
    if "answer_relevancy" in df.columns:
        print(f"Average answer relevancy: {df['answer_relevancy'].mean():.2f}")