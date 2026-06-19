from __future__ import annotations

import pytest

from src.domain.metrics.clustering import Clustering


@pytest.fixture
def metric():
    return Clustering()

def test_complete_graph_clustering(complete5, no_params, metric):
    result = metric.compute(complete5, no_params)
    assert result.summary["avg_clustering"] == pytest.approx(1.0)
    assert result.summary["transitivity"] == pytest.approx(1.0)

def test_path_graph_clustering(path10, no_params, metric):
    result = metric.compute(path10, no_params)
    assert result.summary["avg_clustering"] == pytest.approx(0.0)
    assert result.summary["transitivity"] == pytest.approx(0.0)

def test_triangle_clustering(triangle, no_params, metric):
    result = metric.compute(triangle, no_params)
    assert result.summary["avg_clustering"] == pytest.approx(1.0)

def test_empty_graph_clustering(empty, no_params, metric):
    result = metric.compute(empty, no_params)
    assert result.summary["avg_clustering"] == pytest.approx(0.0)
    assert result.summary["transitivity"] == pytest.approx(0.0)

def test_disconnected_graph_clustering(disconnected, no_params, metric):
    result = metric.compute(disconnected, no_params)
    assert result.summary["avg_clustering"] == pytest.approx(0.0)

def test_weighted_flag_in_summary(weighted, no_params, metric):
    result = metric.compute(weighted, no_params)
    assert result.summary["weighted"] is True

def test_directed_graph_uses_undirected_view(directed, no_params, metric):
    result = metric.compute(directed, no_params)
    assert isinstance(result.summary["avg_clustering"], float)

def test_result_metric_name(triangle, no_params, metric):
    result = metric.compute(triangle, no_params)
    assert result.metric == "clustering"

def test_result_summary_keys(triangle, no_params, metric):
    result = metric.compute(triangle, no_params)
    assert "avg_clustering" in result.summary
    assert "transitivity" in result.summary
    assert "weighted" in result.summary
