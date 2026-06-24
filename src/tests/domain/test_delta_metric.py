from __future__ import annotations

import pytest

from src.domain.metrics.base import DeltaMetric, MetricResult
from src.domain.metrics.diameter import Diameter


@pytest.fixture
def delta_diameter():
    return DeltaMetric(Diameter())


def test_compute_delta_keys_present(path10, complete5, no_params, delta_diameter):
    result = delta_diameter.compute_delta(path10, complete5, no_params)
    assert "diameter_original" in result.summary
    assert "diameter_reduced" in result.summary
    assert "diameter_delta" in result.summary

def test_compute_delta_direction(path10, complete5, no_params, delta_diameter):
    result = delta_diameter.compute_delta(path10, complete5, no_params)
    assert result.summary["diameter_delta"] < 0

def test_single_graph_compute_delegates(path10, no_params, delta_diameter):
    result = delta_diameter.compute(path10, no_params)
    assert "diameter" in result.summary

def test_non_numeric_fields_are_passed_through():
    import networkx as nx
    from src.domain.graph_model import Graph, RunParams
    from src.domain.metrics.base import Metric, MetricInfo

    class _LabelMetric(Metric):
        INFO = MetricInfo(name="label_metric")
        def compute(self, graph, params):
            return MetricResult(metric="label_metric", summary={"score": 1.0, "label": "hello"})

    dm = DeltaMetric(_LabelMetric())
    g = Graph.from_networkx(nx.path_graph(3), name="p3")
    h = Graph.from_networkx(nx.path_graph(3), name="p3b")
    result = dm.compute_delta(g, h, RunParams({}))
    assert "label" in result.summary
    assert result.summary["label"] == "hello"
    assert "score_delta" in result.summary
