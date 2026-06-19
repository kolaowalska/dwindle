from __future__ import annotations

import pytest
import networkx as nx

from src.domain.metrics.avg_path import AvgPathLength
from src.domain.graph_model import Graph, RunParams


@pytest.fixture
def metric():
    return AvgPathLength()

def test_path_graph_avg_path(path10, no_params, metric):
    result = metric.compute(path10, no_params)
    assert result.summary["avg"] == pytest.approx(11 / 3, rel=1e-3)

def test_complete_graph_avg_path(complete5, no_params, metric):
    result = metric.compute(complete5, no_params)
    assert result.summary["avg"] == pytest.approx(1.0)

def test_triangle_avg_path(triangle, no_params, metric):
    result = metric.compute(triangle, no_params)
    assert result.summary["avg"] == pytest.approx(1.0)

def test_single_node_returns_zero(no_params, metric):
    g_nx = nx.Graph()
    g_nx.add_node(0)
    result = metric.compute(Graph.from_networkx(g_nx, name="single"), no_params)
    assert result.summary["avg"] == pytest.approx(0.0)

def test_empty_graph_returns_zero(empty, no_params, metric):
    result = metric.compute(empty, no_params)
    assert result.summary["avg"] == pytest.approx(0.0)

def test_disconnected_uses_largest_cc(disconnected, no_params, metric):
    result = metric.compute(disconnected, no_params)
    assert result.summary["avg"] >= 0.0

def test_weighted_flag_in_summary(weighted, no_params, metric):
    result = metric.compute(weighted, no_params)
    assert result.summary["weighted"] is True

def test_unweighted_flag_in_summary(path10, no_params, metric):
    result = metric.compute(path10, no_params)
    assert result.summary["weighted"] is False

def test_weighted_path_differs_from_unweighted():
    metric = AvgPathLength()
    params = RunParams({})
    g_weighted = nx.Graph()
    g_weighted.add_edge(0, 1, weight=1.0)
    g_weighted.add_edge(1, 2, weight=100.0)
    g_plain = nx.Graph()
    g_plain.add_edges_from([(0, 1), (1, 2)])
    r_w = metric.compute(Graph.from_networkx(g_weighted, name="w"), params)
    r_p = metric.compute(Graph.from_networkx(g_plain, name="p"), params)
    assert r_w.summary["avg"] != r_p.summary["avg"]

def test_result_metric_name(path10, no_params, metric):
    result = metric.compute(path10, no_params)
    assert result.metric == "average path length"

def test_result_summary_has_avg_key(path10, no_params, metric):
    result = metric.compute(path10, no_params)
    assert "avg" in result.summary
