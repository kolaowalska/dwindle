from __future__ import annotations

import pytest
import networkx as nx

from src.domain.sparsifiers.k_neighbor import KNeighborSparsifier
from src.domain.graph_model import Graph, RunParams


@pytest.fixture
def sparsifier():
    return KNeighborSparsifier()

def test_all_nodes_preserved(complete5, sparsifier):
    result = sparsifier.run(complete5, RunParams({"rho": 0.5}))
    assert set(result.nodes()) == set(complete5.nodes())

def test_result_edge_count_at_most_original(path10, sparsifier):
    result = sparsifier.run(path10, RunParams({"rho": 0.5}))
    assert result.edge_count <= path10.edge_count

def test_rho_one_may_retain_all_edges(complete5, sparsifier):
    result = sparsifier.run(complete5, RunParams({"rho": 1.0}))
    assert result.edge_count == complete5.edge_count

def test_rho_zero_retains_one_edge_per_node():
    sparsifier = KNeighborSparsifier()
    g = Graph.from_networkx(nx.complete_graph(6), name="k6")
    result = sparsifier.run(g, RunParams({"rho": 0.0}))
    assert result.edge_count <= g.node_count

def test_high_rho_retains_more_edges_than_low_rho(complete5):
    s = KNeighborSparsifier()
    low = s.run(complete5, RunParams({"rho": 0.2, "seed": 42}))
    high = s.run(complete5, RunParams({"rho": 0.9, "seed": 42}))
    assert high.edge_count >= low.edge_count

def test_weighted_graph_samples_proportionally(sparsifier):
    g = nx.Graph()
    g.add_edge(0, 1, weight=10.0)
    g.add_edge(0, 2, weight=1.0)
    g.add_edge(1, 2, weight=1.0)
    graph = Graph.from_networkx(g, name="tri_weighted")
    high_wins = sum(
        1 for seed in range(50)
        if sparsifier.run(graph, RunParams({"rho": 0.5, "seed": seed}))
               .to_networkx(copy=False).has_edge(0, 1)
    )
    assert high_wins > 35

def test_same_seed_gives_same_result(complete5):
    s = KNeighborSparsifier()
    params = RunParams({"rho": 0.5, "seed": 7})
    r1 = s.run(complete5, params)
    r2 = s.run(complete5, params)
    assert set(r1.edges()) == set(r2.edges())

def test_output_name_contains_k_neighbor(path10, sparsifier):
    result = sparsifier.run(path10, RunParams({"rho": 0.5}))
    assert "k_neighbor" in result.name

def test_metadata_contains_rho(complete5, sparsifier):
    result = sparsifier.run(complete5, RunParams({"rho": 0.7}))
    assert result.metadata["rho"] == pytest.approx(0.7)

def test_execute_injects_execution_time(complete5, no_params, sparsifier):
    result = sparsifier.execute(complete5, no_params)
    assert "execution_time" in result.metadata
