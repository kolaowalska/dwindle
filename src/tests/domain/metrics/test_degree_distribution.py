from __future__ import annotations

import pytest
import networkx as nx

from src.domain.metrics.degree_distribution import APSPMetric as DegreeDistribution
from src.domain.graph_model import Graph, RunParams


@pytest.fixture
def metric():
    return DegreeDistribution()

def test_complete_graph_max_degree(complete5, no_params, metric):
    result = metric.compute(complete5, no_params)
    assert result.summary["max_degree"] == 4

def test_path_graph_max_degree(path10, no_params, metric):
    result = metric.compute(path10, no_params)
    assert result.summary["max_degree"] == 2

def test_path_graph_min_degree(path10, no_params, metric):
    result = metric.compute(path10, no_params)
    assert result.summary["min_degree"] == 1

def test_complete_graph_unique_degrees(complete5, no_params, metric):
    result = metric.compute(complete5, no_params)
    assert result.summary["unique_degrees"] == 1

def test_path_graph_unique_degrees(path10, no_params, metric):
    result = metric.compute(path10, no_params)
    assert result.summary["unique_degrees"] == 2

def test_empty_graph_returns_zero_entropy(empty, no_params, metric):
    result = metric.compute(empty, no_params)
    assert result.summary["entropy"] == pytest.approx(0.0)

def test_single_edge_graph_degrees():
    metric = DegreeDistribution()
    g = Graph.from_networkx(nx.Graph([(0, 1)]), name="one_edge")
    result = metric.compute(g, RunParams({}))
    assert result.summary["max_degree"] == 1
    assert result.summary["min_degree"] == 1
    assert result.summary["unique_degrees"] == 1

def test_artifacts_contain_distribution(path10, no_params, metric):
    result = metric.compute(path10, no_params)
    assert "distribution" in result.artifacts
    assert isinstance(result.artifacts["distribution"], dict)

def test_distribution_sums_to_one(complete5, no_params, metric):
    result = metric.compute(complete5, no_params)
    total = sum(result.artifacts["distribution"].values())
    assert total == pytest.approx(1.0)

def test_result_metric_name(path10, no_params, metric):
    result = metric.compute(path10, no_params)
    assert result.metric == "degree distribution"
