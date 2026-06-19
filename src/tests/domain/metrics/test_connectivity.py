from __future__ import annotations

import pytest

from src.domain.metrics.connectivity import Connectivity


@pytest.fixture
def metric():
    return Connectivity()

def test_connected_graph_has_one_component(path10, no_params, metric):
    result = metric.compute(path10, no_params)
    assert result.summary["n_components"] == 1

def test_disconnected_graph_component_count(disconnected, no_params, metric):
    result = metric.compute(disconnected, no_params)
    assert result.summary["n_components"] == 2

def test_empty_graph_connectivity(empty, no_params, metric):
    result = metric.compute(empty, no_params)
    assert result.summary["n_components"] == 0
    assert result.summary["largest_component_ratio"] == pytest.approx(0.0)
    assert result.summary["fiedler"] == pytest.approx(0.0)

def test_fully_connected_largest_ratio(complete5, no_params, metric):
    result = metric.compute(complete5, no_params)
    assert result.summary["largest_component_ratio"] == pytest.approx(1.0)

def test_disconnected_largest_ratio_less_than_one(disconnected, no_params, metric):
    result = metric.compute(disconnected, no_params)
    assert result.summary["largest_component_ratio"] < 1.0

def test_path_graph_fiedler_positive(path10, no_params, metric):
    result = metric.compute(path10, no_params)
    assert result.summary["fiedler"] > 0.0

def test_complete_graph_fiedler_larger_than_path(complete5, path10, no_params, metric):
    r_k5 = metric.compute(complete5, no_params)
    r_p10 = metric.compute(path10, no_params)
    assert r_k5.summary["fiedler"] > r_p10.summary["fiedler"]

def test_directed_graph_converted_to_undirected(directed, no_params, metric):
    result = metric.compute(directed, no_params)
    assert result.summary["n_components"] == 1

def test_result_metric_name(path10, no_params, metric):
    result = metric.compute(path10, no_params)
    assert result.metric == "connectivity"

def test_result_summary_keys(path10, no_params, metric):
    result = metric.compute(path10, no_params)
    assert "n_components" in result.summary
    assert "largest_component_ratio" in result.summary
    assert "fiedler" in result.summary
