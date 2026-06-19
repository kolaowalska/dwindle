from __future__ import annotations

import pytest

from src.domain.metrics.registry import MetricRegistry, _METRICS
from src.domain.metrics.base import Metric, MetricInfo, MetricResult
from src.domain.graph_model import Graph, RunParams


class _DummyMetric(Metric):
    INFO = MetricInfo(name="dummy_test_metric")

    def compute(self, graph: Graph, params: RunParams) -> MetricResult:
        return MetricResult(metric=self.INFO.name, summary={})

def test_register_and_retrieve():
    key = "_test_metric_dummy_abc"
    try:
        MetricRegistry.register(key)(_DummyMetric)
        assert isinstance(MetricRegistry.get(key), _DummyMetric)
    finally:
        _METRICS.pop(key, None)

def test_register_duplicate_name_raises():
    key = "_test_metric_dup_xyz"

    class _OtherMetric(Metric):
        INFO = MetricInfo(name="other_test_metric")
        def compute(self, graph, params): return MetricResult(metric="other", summary={})

    try:
        MetricRegistry.register(key)(_DummyMetric)
        with pytest.raises(ValueError, match="already registered"):
            MetricRegistry.register(key)(_OtherMetric)
    finally:
        _METRICS.pop(key, None)

def test_register_empty_name_raises():
    with pytest.raises(ValueError):
        MetricRegistry.register("")
    with pytest.raises(ValueError):
        MetricRegistry.register("   ")

def test_register_same_class_twice_is_idempotent():
    key = "_test_metric_same_class"
    try:
        MetricRegistry.register(key)(_DummyMetric)
        MetricRegistry.register(key)(_DummyMetric)
    finally:
        _METRICS.pop(key, None)

def test_discover_populates_known_metrics():
    MetricRegistry.discover()
    names = MetricRegistry.list()
    for expected in ["diameter", "clustering", "connectivity", "avg_path_length",
                     "effective_resistance", "degree_distribution", "community_preservation"]:
        assert expected in names

def test_discover_is_idempotent():
    MetricRegistry.discover()
    before = set(MetricRegistry.list())
    MetricRegistry.discover()
    assert set(MetricRegistry.list()) == before

def test_get_unknown_name_raises_key_error():
    MetricRegistry.discover()
    with pytest.raises(KeyError):
        MetricRegistry.get("not_a_real_metric_xyzzy123")

def test_list_returns_sorted():
    MetricRegistry.discover()
    names = MetricRegistry.list()
    assert names == sorted(names)

def test_get_returns_fresh_instance_each_call():
    MetricRegistry.discover()
    m1 = MetricRegistry.get("diameter")
    m2 = MetricRegistry.get("diameter")
    assert m1 is not m2
