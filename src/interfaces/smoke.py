from __future__ import annotations
import os
import networkx as nx

from src.application.experiment_service import ExperimentService
from src.infrastructure.graph_gateway import GraphSource
from src.infrastructure.persistence.stubs import InMemoryGraphRepository, InMemoryExperimentRepository


def run_smoke() -> None:
    print("\n--- SMOKE TEST ---")

    # 1. setup
    graph_repo = InMemoryGraphRepository()
    exp_repo = InMemoryExperimentRepository()
    service = ExperimentService(graph_repo=graph_repo, experiment_repo=exp_repo)

    # 2. loading data (file or fallback)
    data_path = "src/data/toy.edgelist"
    if os.path.exists(data_path):
        print(f"[smoke] loading from file: {data_path}")
        source = GraphSource(kind="file", value=data_path, name="toy-graph", weighted=True)
    else:
        print("[smoke] file not found, using in-memory fallback")
        g = nx.erdos_renyi_graph(20, 0.3, seed=42)
        source = GraphSource(kind="memory", value=g, name="mock-demo-graph")

    graph_key = service.import_graph(source)
    print(f"\n[smoke] graph imported successfully: '{graph_key}'")

    try:
        # 3. running the actual experiment
        # report = service.run_experiment(graph_key, "identity_stub", ["diameter"])
        report = service.run_experiment(graph_key, "mock_coarsening", ["diameter"])

        print("\n--- SMOKE TEST RESULTS ---")
        print(f"graph name: {report.graph_name}")
        print(f"algorithm: {report.algorithm_name}")
        print(f"reduction: {report.nodes_before} -> {report.nodes_after} nodes")

        # 4. handling metrics
        print("metrics:")
        for m in report.metric_results:
            summary_str = ", ".join([f"{k} = {v}" for k, v in m.summary.items()])
            print(f"  - {m.metric}: {summary_str}")

        print("--- SUCCESS ---")

    except Exception as e:
        print("\n--- SMOKE TEST FAILED ---")
        print(f"error: {e}")
        raise e
