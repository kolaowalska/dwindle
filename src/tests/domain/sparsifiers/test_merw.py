from __future__ import annotations

import pytest
import networkx as nx

from src.domain.sparsifiers.merw import MERWSparsifier
from src.domain.graph_model import Graph, RunParams


@pytest.fixture
def sparsifier():
    return MERWSparsifier()

def test_result_has_fewer_edges(complete5, sparsifier):
    result = sparsifier.run(complete5, RunParams({"rho": 0.5}))
    assert result.edge_count <= complete5.edge_count

def test_result_remains_connected(triangle, sparsifier):
    result = sparsifier.run(triangle, RunParams({"rho": 0.5}))
    assert nx.is_connected(result.to_networkx(copy=False))

def test_rho_one_retains_all_edges(triangle, sparsifier):
    result = sparsifier.run(triangle, RunParams({"rho": 1.0}))
    assert result.edge_count == triangle.edge_count

def test_rho_out_of_range_raises():
    sparsifier = MERWSparsifier()
    g = Graph.from_networkx(nx.path_graph(4), name="p4")
    with pytest.raises(ValueError):
        sparsifier.run(g, RunParams({"rho": 0.0}))
    with pytest.raises(ValueError):
        sparsifier.run(g, RunParams({"rho": 1.5}))

def test_lower_rho_fewer_edges(complete5):
    s = MERWSparsifier()
    low = s.run(complete5, RunParams({"rho": 0.3}))
    high = s.run(complete5, RunParams({"rho": 0.8}))
    assert low.edge_count <= high.edge_count

def test_disconnected_graph_raises(disconnected, sparsifier):
    with pytest.raises(ValueError):
        sparsifier.run(disconnected, RunParams({"rho": 0.5}))

def test_rescore_interval_zero_vs_nonzero(triangle):
    s = MERWSparsifier()
    r0 = s.run(triangle, RunParams({"rho": 0.5, "rescore_interval": 0}))
    r1 = s.run(triangle, RunParams({"rho": 0.5, "rescore_interval": 1}))
    assert isinstance(r0, Graph) and r0.edge_count >= 1
    assert isinstance(r1, Graph) and r1.edge_count >= 1

def test_output_name_contains_merw(triangle, sparsifier):
    result = sparsifier.run(triangle, RunParams({"rho": 1.0}))
    assert "merw" in result.name

def test_metadata_contains_rho(triangle, sparsifier):
    result = sparsifier.run(triangle, RunParams({"rho": 0.8}))
    assert result.metadata["rho"] == pytest.approx(0.8)

def test_execute_injects_execution_time(triangle, no_params, sparsifier):
    result = sparsifier.execute(triangle, no_params)
    assert "execution_time" in result.metadata
