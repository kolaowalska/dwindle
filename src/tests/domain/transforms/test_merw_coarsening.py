from __future__ import annotations

import pytest
import networkx as nx

from src.domain.transforms.merw_coarsening import MERWCoarsening
from src.domain.graph_model import Graph, RunParams


@pytest.fixture
def transform():
    return MERWCoarsening()


def test_reduces_edge_count(complete5, transform):
    result = transform.run(complete5, RunParams({"rho": 0.5}))
    assert result.edge_count <= complete5.edge_count

def test_result_remains_connected(triangle, transform):
    result = transform.run(triangle, RunParams({"rho": 0.5}))
    assert nx.is_connected(result.to_networkx(copy=False))

def test_rho_one_retains_most_edges(triangle, transform):
    result = transform.run(triangle, RunParams({"rho": 1.0}))
    assert result.edge_count == triangle.edge_count

def test_rho_out_of_range_raises(triangle, transform):
    with pytest.raises(ValueError):
        transform.run(triangle, RunParams({"rho": 0.0}))
    with pytest.raises(ValueError):
        transform.run(triangle, RunParams({"rho": 1.5}))

def test_lower_rho_fewer_edges(complete5):
    t = MERWCoarsening()
    low = t.run(complete5, RunParams({"rho": 0.3}))
    high = t.run(complete5, RunParams({"rho": 0.8}))
    assert low.edge_count <= high.edge_count

def test_disconnected_graph_raises(disconnected, transform):
    with pytest.raises(ValueError):
        transform.run(disconnected, RunParams({"rho": 0.5}))

def test_output_name_contains_merw(triangle, transform):
    result = transform.run(triangle, RunParams({"rho": 1.0}))
    assert "merw" in result.name

def test_metadata_contains_rho(triangle, transform):
    result = transform.run(triangle, RunParams({"rho": 0.8}))
    assert result.metadata["rho"] == pytest.approx(0.8)

def test_execute_injects_execution_time(triangle, no_params, transform):
    result = transform.execute(triangle, no_params)
    assert "execution_time" in result.metadata
