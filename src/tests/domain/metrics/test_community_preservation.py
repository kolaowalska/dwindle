from __future__ import annotations

import pytest
import networkx as nx

from src.domain.metrics.community_preservation import CommunityPreservation
from src.domain.graph_model import Graph, RunParams


@pytest.fixture
def metric():
    return CommunityPreservation()

def test_triangle_community_count(triangle, no_params, metric):
    result = metric.compute(triangle, no_params)
    assert result.summary["n_communities"] >= 1
    assert -0.5 <= result.summary["modularity"] <= 1.0

def test_community_count_at_least_one(complete5, no_params, metric):
    result = metric.compute(complete5, no_params)
    assert result.summary["n_communities"] >= 1

def test_two_clique_graph_detects_two_communities():
    metric = CommunityPreservation()
    g = nx.complete_graph(5)
    for i in range(5, 10):
        for j in range(i + 1, 10):
            g.add_edge(i, j)
    g.add_edge(4, 5)
    graph = Graph.from_networkx(g, name="two_cliques")
    result = metric.compute(graph, RunParams({"seed": 2137}))
    assert result.summary["n_communities"] == 2

def test_modularity_range(path10, no_params, metric):
    result = metric.compute(path10, no_params)
    assert -0.5 <= result.summary["modularity"] <= 1.0

def test_no_edges_returns_zero(no_params, metric):
    g_nx = nx.Graph()
    g_nx.add_node(0)
    g_nx.add_node(1)
    result = metric.compute(Graph.from_networkx(g_nx, name="no_edges"), no_params)
    assert result.summary["modularity"] == pytest.approx(0.0)
    assert result.summary["n_communities"] == 0

def test_empty_graph_no_edges(empty, no_params, metric):
    result = metric.compute(empty, no_params)
    assert result.summary["modularity"] == pytest.approx(0.0)

def test_same_seed_gives_same_result(complete5):
    metric = CommunityPreservation()
    params = RunParams({"seed": 42})
    r1 = metric.compute(complete5, params)
    r2 = metric.compute(complete5, params)
    assert r1.summary == r2.summary

def test_directed_graph_converted_to_undirected(directed, no_params, metric):
    result = metric.compute(directed, no_params)
    assert result.summary["n_communities"] >= 1

def test_result_metric_name(triangle, no_params, metric):
    result = metric.compute(triangle, no_params)
    assert result.metric == "community preservation"

def test_result_summary_keys(triangle, no_params, metric):
    result = metric.compute(triangle, no_params)
    assert "modularity" in result.summary
    assert "n_communities" in result.summary
