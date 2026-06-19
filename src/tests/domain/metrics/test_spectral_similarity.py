from __future__ import annotations

import pytest
import networkx as nx

from src.domain.metrics.spectral_similarity import SpectralSimilarity
from src.domain.graph_model import Graph, RunParams


@pytest.fixture
def metric():
    return SpectralSimilarity()

@pytest.fixture
def k_params():
    return RunParams({"k": 5})

def test_identical_graphs_zero_error(complete5, k_params, metric):
    result = metric.compute(complete5, complete5, k_params)
    assert result.summary["relative_l2_error"] == pytest.approx(0.0, abs=1e-6)

def test_identical_path_graphs_zero_error(path10, k_params, metric):
    result = metric.compute(path10, path10, k_params)
    assert result.summary["relative_l2_error"] == pytest.approx(0.0, abs=1e-6)

def test_different_graphs_nonzero_error(path10, complete5, k_params, metric):
    result = metric.compute(path10, complete5, k_params)
    assert result.summary["relative_l2_error"] > 0.0


def test_fiedler_values_in_summary(path10, complete5, k_params, metric):
    result = metric.compute(path10, complete5, k_params)
    assert "fiedler_G" in result.summary
    assert "fiedler_H" in result.summary

def test_fiedler_ratio_when_g_is_zero():
    metric = SpectralSimilarity()
    g_nx = nx.Graph()
    g_nx.add_node(0)
    g_single = Graph.from_networkx(g_nx, name="single")
    h = Graph.from_networkx(nx.complete_graph(3), name="k3")
    result = metric.compute(g_single, h, RunParams({"k": 3}))
    assert result.summary["fiedler_G"] == pytest.approx(0.0, abs=1e-9)
    assert result.summary["fiedler_ratio"] == pytest.approx(0.0, abs=1e-9)

def test_k_in_summary(path10, complete5, metric):
    result = metric.compute(path10, complete5, RunParams({"k": 5}))
    assert "k" in result.summary

def test_small_k_param():
    metric = SpectralSimilarity()
    g = Graph.from_networkx(nx.complete_graph(4), name="k4")
    h = Graph.from_networkx(nx.path_graph(4), name="p4")
    result = metric.compute(g, h, RunParams({"k": 2}))
    assert result.summary["k"] <= 2

def test_directed_graphs_converted(directed, k_params, metric):
    result = metric.compute(directed, directed, k_params)
    assert result.summary["relative_l2_error"] == pytest.approx(0.0, abs=1e-6)

def test_result_metric_name(path10, complete5, k_params, metric):
    result = metric.compute(path10, complete5, k_params)
    assert result.metric == "spectral similarity"
