from __future__ import annotations

import dataclasses
import pytest

from src.application.dto import ExperimentDTO
from src.domain.metrics.base import MetricResult


@pytest.fixture
def sample_dto():
    return ExperimentDTO(
        graph_name="g",
        reduced_graph_key="g_identity_stub",
        nodes_before=10,
        edges_before=9,
        nodes_after=10,
        edges_after=9,
        algorithm_name="identity_stub",
        metric_results=[MetricResult(metric="diameter", summary={"diameter": 9.0})],
        metadata={"execution_time": 0.001},
    )


# --- field access ---

def test_dto_fields_accessible(sample_dto):
    assert sample_dto.graph_name == "g"
    assert sample_dto.reduced_graph_key == "g_identity_stub"
    assert sample_dto.nodes_before == 10
    assert sample_dto.edges_before == 9
    assert sample_dto.nodes_after == 10
    assert sample_dto.edges_after == 9
    assert sample_dto.algorithm_name == "identity_stub"
    assert sample_dto.metadata == {"execution_time": 0.001}

def test_dto_is_immutable(sample_dto):
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        sample_dto.graph_name = "other"

# --- metric_results ---

def test_dto_metric_results_list(sample_dto):
    assert isinstance(sample_dto.metric_results, list)
    assert all(isinstance(r, MetricResult) for r in sample_dto.metric_results)

def test_dto_metric_results_accessible_by_index(sample_dto):
    assert sample_dto.metric_results[0].metric == "diameter"

def test_dto_metric_results_summary_accessible(sample_dto):
    assert sample_dto.metric_results[0].summary["diameter"] == 9.0

def test_dto_empty_metric_results():
    dto = ExperimentDTO(
        graph_name="g", reduced_graph_key="g_r",
        nodes_before=5, edges_before=4,
        nodes_after=5, edges_after=4,
        algorithm_name="identity_stub",
        metric_results=[],
        metadata={},
    )
    assert dto.metric_results == []

# --- edge retention ratio ---

def test_edge_retention_ratio_computable(sample_dto):
    ratio = sample_dto.edges_after / sample_dto.edges_before
    assert 0.0 <= ratio <= 1.0

def test_node_reduction_computable(sample_dto):
    delta = sample_dto.nodes_after - sample_dto.nodes_before
    assert isinstance(delta, int)

def test_zero_edges_before_construction_does_not_raise():
    dto = ExperimentDTO(
        graph_name="empty", reduced_graph_key="empty_r",
        nodes_before=5, edges_before=0,
        nodes_after=5, edges_after=0,
        algorithm_name="identity_stub",
        metric_results=[],
        metadata={},
    )
    assert dto.edges_before == 0
