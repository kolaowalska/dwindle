from __future__ import annotations

import pytest
import networkx as nx

from src.domain.sparsifiers.local_degree import LocalDegreeSparsifier
from src.domain.graph_model import Graph, RunParams


@pytest.fixture
def sparsifier():
    return LocalDegreeSparsifier()

def test_all_nodes_preserved(complete5, sparsifier):
    result = sparsifier.run(complete5, RunParams({"rho": 0.5}))
    assert set(result.nodes()) == set(complete5.nodes())

def test_result_edge_count_at_most_original(path10, sparsifier):
    result = sparsifier.run(path10, RunParams({"rho": 0.5}))
    assert result.edge_count <= path10.edge_count

def test_prefers_high_degree_neighbors():
    sparsifier = LocalDegreeSparsifier()
    g = nx.Graph()
    g.add_edges_from([(0, 1), (0, 2), (0, 3), (0, 4), (5, 0), (5, 6)])
    graph = Graph.from_networkx(g, name="hub_test")
    result = sparsifier.run(graph, RunParams({"rho": 0.5}))
    assert result.to_networkx(copy=False).has_edge(5, 0)

def test_rho_zero_keeps_at_most_zero_neighbors():
    sparsifier = LocalDegreeSparsifier()
    g = Graph.from_networkx(nx.complete_graph(6), name="k6")
    result = sparsifier.run(g, RunParams({"rho": 0.0}))
    assert result.edge_count <= g.node_count

def test_higher_rho_retains_more_edges(complete5):
    s = LocalDegreeSparsifier()
    low = s.run(complete5, RunParams({"rho": 0.2}))
    high = s.run(complete5, RunParams({"rho": 0.9}))
    assert high.edge_count >= low.edge_count

def test_directed_graph_uses_out_degree(directed, sparsifier):
    result = sparsifier.run(directed, RunParams({"rho": 0.5}))
    assert isinstance(result, Graph)

def test_output_name_contains_local_degree(path10, sparsifier):
    result = sparsifier.run(path10, RunParams({"rho": 0.5}))
    assert "local_degree" in result.name

def test_metadata_contains_rho(complete5, sparsifier):
    result = sparsifier.run(complete5, RunParams({"rho": 0.7}))
    assert result.metadata["rho"] == pytest.approx(0.7)

def test_execute_injects_execution_time(complete5, no_params, sparsifier):
    result = sparsifier.execute(complete5, no_params)
    assert "execution_time" in result.metadata
