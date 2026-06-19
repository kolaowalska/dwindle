from __future__ import annotations

import pytest

from src.domain.metrics.effective_resistance import EffectiveResistance


@pytest.fixture
def metric():
    return EffectiveResistance()

def test_complete_graph_kirchhoff(complete5, no_params, metric):
    result = metric.compute(complete5, no_params)
    assert result.summary["kirchhoff_index"] == pytest.approx(4.0, rel=1e-3)

def test_kirchhoff_positive(path10, no_params, metric):
    result = metric.compute(path10, no_params)
    assert result.summary["kirchhoff_index"] > 0.0

def test_complete_graph_lower_kirchhoff_than_path(complete5, path10, no_params, metric):
    r_k5 = metric.compute(complete5, no_params)
    r_p10 = metric.compute(path10, no_params)
    assert r_k5.summary["kirchhoff_index"] < r_p10.summary["kirchhoff_index"]

def test_disconnected_uses_largest_cc(disconnected, no_params, metric):
    result = metric.compute(disconnected, no_params)
    assert result.summary["kirchhoff_index"] >= 0.0

def test_component_nodes_in_summary(disconnected, no_params, metric):
    result = metric.compute(disconnected, no_params)
    assert result.summary["component_nodes"] < disconnected.node_count

def test_directed_graph_converted_to_undirected(directed, no_params, metric):
    result = metric.compute(directed, no_params)
    assert result.summary["kirchhoff_index"] > 0.0

def test_result_metric_name(path10, no_params, metric):
    result = metric.compute(path10, no_params)
    assert result.metric == "effective resistance"

def test_result_summary_keys(path10, no_params, metric):
    result = metric.compute(path10, no_params)
    assert "kirchhoff_index" in result.summary
    assert "component_nodes" in result.summary
