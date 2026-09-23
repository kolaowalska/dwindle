from __future__ import annotations

import sys
import os

sys.path.append(os.getcwd())

from src.interfaces.api import ExperimentFacade
from src.interfaces.reporter import Reporter, ScenarioRecord
from src.domain.metrics.base import DeltaMetric
from src.domain.metrics.registry import MetricRegistry
from src.domain.graph_model import RunParams

try:
    from src.interfaces.visualizer import save_comparison_plot
    VISUALIZE = True
except ImportError:
    VISUALIZE = False
    print("visualizer not found :( plotting disabled")

# ----------------------------- CONFIGURATION -----------------------------

DATA_PATH = "src/data/toy.edgelist"

METRICS = [
    "diameter",
    "avg_path_length",
    "degree_distribution",
    "connectivity",
    "clustering",
    "community_preservation",
]

RELATIVE_METRICS = [
    "spectral_similarity"
]

SCENARIOS = [
    {
        "label": "random sparsifier (p=0.5)",
        "algorithm": "random",
        "params": {"p": 0.5, "seed": 1312},
    },
    {
        "label": "k-neighbor sparsifier (rho=0.5)",
        "algorithm": "k_neighbor",
        "params": {"rho": 0.5, "seed": 420},
    },
    {
        "label": "local degree sparsifier (rho=0.5)",
        "algorithm": "local_degree",
        "params": {"rho": 0.5},
    },
    # {
    #     "label": "graph coarsening (50% node reduction)",
    #     "algorithm": "mock_coarsening",
    #     "params": {"reduction_ratio": 0.5},
    # },
{
        "label": "pagerank pruning (rho=0.5)",
        "algorithm": "pagerank",
        "params": {"rho": 0.5, "alpha": 0.85},
    },
    {
        "label": "merw sparsifier (rho=0.5)",
        "algorithm": "merw",
        "params": {"rho": 0.5, "rescore_interval": 0},
    },
]

# -------------------------------------------------------------------------


def _format_summary(summary: dict) -> str:
    parts = []
    for k, v in summary.items():
        parts.append(f"{k} = {v:.4f}" if isinstance(v, float) else f"{k} = {v}")
    return ", ".join(parts)


def _separator():
    print("\n" + "♥ " * 21)


def _upload_graph(api: ExperimentFacade) -> str:
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"data file not found: {DATA_PATH}")

    print(f"\n[♥] uploading graph from {DATA_PATH}")
    response = api.upload_graph({
        "path": DATA_PATH,
        "name": "demo_graph",
        "kind": "file",
        "directed": True,
        "weighted": True,
    })

    if response["status"] != "success":
        raise RuntimeError(f"upload failed: {response}")

    graph_key = response["graph_key"]
    print(f" → uploaded successfully :) ID: {graph_key}")
    return graph_key


def _run_scenario(api: ExperimentFacade, graph_key: str, scenario: dict) -> dict | None:
    result = api.run_job({
        "graph_key": graph_key,
        "algorithm": scenario["algorithm"],
        "metrics": METRICS,
        "params": scenario["params"],
    })

    if result["status"] != "success":
        print(f"error running {scenario['algorithm']}: {result}")
        return None

    return result["data"]


def _print_scenario_results(data: dict):
    print(f" • nodes: {data['nodes_before']} → {data['nodes_after']}")
    print(f" • edges: {data['edges_before']} → {data['edges_after']}")
    print(f" • metrics:")
    for m in data.get("metric_results", []):
        print(f"    - {m['metric']}: {_format_summary(m['summary'])}")


def _compute_deltas(
    api: ExperimentFacade,
    graph_key: str,
    reduced_graph_key: str,
    params: dict,
) -> dict[str, dict]:
    """fetches both graphs and runs DeltaMetric for each registered metric."""
    repo = api.graph_repo
    G = repo.get(graph_key)
    H = repo.get(reduced_graph_key)
    run_params = RunParams(values=params)

    results: dict[str, dict] = {}
    # print(f" • deltas:")
    for name in METRICS + RELATIVE_METRICS:
        try:
            metric = MetricRegistry.get(name)
            if metric.INFO.type == "relative":
                result = metric.compute(G, H, run_params)
            else:
                result = DeltaMetric(metric).compute_delta(G, H, run_params)
            # print(f"    - {result.metric}: {_format_summary(result.summary)}")
            results[result.metric] = dict(result.summary)  # ← collect
        except Exception as e:
            print(f"    - {name}: error ({e})")

    return results


def _run_visualizations(api: ExperimentFacade, graph_key: str):
    repo = api.service.graph_repo
    G = repo.get(graph_key).to_networkx()

    label_map = {
        "random": "random_sparsification",
        "neighbor": "k_neighbor",
        "degree": "local_degree",
        "coarsen": "coarsening",
        "merw": "merw",
    }

    for name in repo.list_names():
        if name == graph_key:
            continue
        label = next((v for k, v in label_map.items() if k in name), "modified")
        g_mod = repo.get(name).to_networkx()
        save_comparison_plot(G, g_mod, label, f"demo_{label}.png")


def main():
    api = ExperimentFacade()
    reporter = Reporter()
    graph_key = _upload_graph(api)

    for i, scenario in enumerate(SCENARIOS, 1):
        _separator()
        print(f"\n[♥] scenario {i}/{len(SCENARIOS)}: {scenario['label']}")

        data = _run_scenario(api, graph_key, scenario)
        if data is None:
            reporter.add(ScenarioRecord(
                label=scenario["label"],
                algorithm=scenario["algorithm"],
                nodes_before=0, edges_before=0,
                nodes_after=0, edges_after=0,
                metrics={}, deltas={},
                error="run_job failed",
            ))
            continue

        # _print_scenario_results(data)

        metrics_by_name = {
            m["metric"]: m["summary"]
            for m in data.get("metric_results", [])
        }

        deltas_by_name: dict = {}
        reduced_key = data.get("reduced_graph_key")
        if reduced_key:
            deltas_by_name = _compute_deltas(
                api, graph_key, reduced_key, scenario["params"]
            )
        else:
            print(" • deltas: skipped (no reduced_graph_key in response)")

        reporter.add(ScenarioRecord(
            label=scenario["label"],
            algorithm=scenario["algorithm"],
            nodes_before=data["nodes_before"],
            edges_before=data["edges_before"],
            nodes_after=data["nodes_after"],
            edges_after=data["edges_after"],
            metrics=metrics_by_name,
            deltas=deltas_by_name,
        ))

    # ── summary report ────────────────────────────────────────────────────────

    reporter.print_report()

    if VISUALIZE:
        _separator()
        print("\n[♥] generating visualizations\n")
        try:
            _run_visualizations(api, graph_key)
        except Exception as e:
            print(f"visualization error: {e}")

    _separator()
    print("\n[♥] demo completed :)\n")


if __name__ == "__main__":
    main()