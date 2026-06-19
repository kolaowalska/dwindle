from __future__ import annotations

import pytest
import networkx as nx

from src.domain.metrics.diameter import Diameter
from src.domain.graph_model import Graph, RunParams


@pytest.fixture
def metric():
    return Diameter()

def test_path_graph_diameter(path10, no_params, metric):
    result = metric.compute(path10, no_params)
    assert result.summary["diameter"] == pytest.approx(9.0)

def test_complete_graph_diameter(complete5, no_params, metric):
    result = metric.compute(complete5, no_params)
    assert result.summary["diameter"] == pytest.approx(1.0)

def test_disconnected_uses_largest_cc(disconnected, no_params, metric):
    result = metric.compute(disconnected, no_params)
    assert result.summary["diameter"] == pytest.approx(1.0)
    assert result.summary["component_nodes"] < result.summary["total_nodes"]

def test_empty_graph_returns_zero(empty, no_params, metric):
    result = metric.compute(empty, no_params)
    assert result.summary["diameter"] == 0.0

def test_result_metric_name(path10, no_params, metric):
    result = metric.compute(path10, no_params)
    assert result.metric == "diameter"

def test_weighted_diameter_differs_from_unweighted():
    metric = Diameter()
    params = RunParams({})
    g_weighted = nx.Graph()
    g_weighted.add_edge(0, 1, weight=1.0)
    g_weighted.add_edge(1, 2, weight=1.0)
    g_weighted.add_edge(0, 2, weight=100.0)
    g_plain = nx.Graph()
    g_plain.add_edges_from([(0, 1), (1, 2), (0, 2)])
    r_w = metric.compute(Graph.from_networkx(g_weighted, name="w"), params)
    r_p = metric.compute(Graph.from_networkx(g_plain, name="p"), params)
    assert r_w.summary["diameter"] != r_p.summary["diameter"]

def test_directed_graph_uses_undirected_view():
    metric = Diameter()
    g = Graph.from_networkx(nx.DiGraph([(0, 1), (1, 2), (2, 0)]), name="cycle")
    result = metric.compute(g, RunParams({}))
    assert result.summary["diameter"] == pytest.approx(1.0)
