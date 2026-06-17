from __future__ import annotations

import pytest
import networkx as nx

from src.domain.sparsifiers.pagerank import PageRankPruning
from src.domain.graph_model import Graph, RunParams


@pytest.fixture
def sparsifier():
    return PageRankPruning()

def test_result_has_fewer_edges(complete5, sparsifier):
    result = sparsifier.run(complete5, RunParams({"rho": 0.5}))
    assert result.edge_count < complete5.edge_count

def test_result_remains_connected(complete5, sparsifier):
    result = sparsifier.run(complete5, RunParams({"rho": 0.5}))
    assert nx.is_connected(result.to_networkx(copy=False))

def test_rho_one_retains_all_edges(triangle, sparsifier):
    result = sparsifier.run(triangle, RunParams({"rho": 1.0}))
    assert result.edge_count == triangle.edge_count

def test_disconnected_graph_raises(disconnected, sparsifier):
    with pytest.raises(ValueError):
        sparsifier.run(disconnected, RunParams({"rho": 0.5}))

def test_lower_rho_fewer_edges(complete5):
    s = PageRankPruning()
    low = s.run(complete5, RunParams({"rho": 0.3}))
    high = s.run(complete5, RunParams({"rho": 0.7}))
    assert low.edge_count <= high.edge_count

def test_output_name_contains_pr(complete5, sparsifier):
    result = sparsifier.run(complete5, RunParams({"rho": 0.5}))
    assert "pr" in result.name

def test_metadata_contains_rho_and_alpha(complete5, sparsifier):
    result = sparsifier.run(complete5, RunParams({"rho": 0.5, "alpha": 0.9}))
    assert result.metadata["rho"] == pytest.approx(0.5)
    assert result.metadata["alpha"] == pytest.approx(0.9)

def test_execute_injects_execution_time(complete5, no_params, sparsifier):
    result = sparsifier.execute(complete5, no_params)
    assert "execution_time" in result.metadata
