from __future__ import annotations

import pytest

from src.domain.transforms.mock_coarsening import MockCoarsening
from src.domain.graph_model import RunParams


@pytest.fixture
def transform():
    return MockCoarsening()


def test_reduces_node_count(complete5, transform):
    result = transform.run(complete5, RunParams({"reduction_ratio": 0.5}))
    assert result.node_count < complete5.node_count

def test_result_has_at_least_one_node(complete5, transform):
    result = transform.run(complete5, RunParams({"reduction_ratio": 0.99}))
    assert result.node_count >= 1

def test_zero_ratio_unchanged(complete5, transform):
    result = transform.run(complete5, RunParams({"reduction_ratio": 0.0}))
    assert result.node_count == complete5.node_count

def test_high_ratio_approaches_single_node(path10, transform):
    result = transform.run(path10, RunParams({"reduction_ratio": 0.9}))
    assert result.node_count <= 2

def test_same_seed_gives_same_result(complete5):
    t = MockCoarsening()
    params = RunParams({"reduction_ratio": 0.5, "seed": 7})
    r1 = t.run(complete5, params)
    r2 = t.run(complete5, params)
    assert r1.node_count == r2.node_count
    assert r1.edge_count == r2.edge_count

def test_output_name_contains_coarsened(path10, transform):
    result = transform.run(path10, RunParams({}))
    assert "coarsened" in result.name

def test_metadata_contains_operation(complete5, transform):
    result = transform.run(complete5, RunParams({"reduction_ratio": 0.5}))
    assert result.metadata["operation"] == "mock_coarsening"

def test_metadata_records_initial_and_final_nodes(complete5, transform):
    result = transform.run(complete5, RunParams({"reduction_ratio": 0.5}))
    assert result.metadata["initial_nodes"] == complete5.node_count
    assert "final_nodes" in result.metadata

def test_execute_injects_execution_time(complete5, no_params, transform):
    result = transform.execute(complete5, no_params)
    assert "execution_time" in result.metadata
