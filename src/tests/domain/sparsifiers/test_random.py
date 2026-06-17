from __future__ import annotations

import pytest

from src.domain.sparsifiers.random import RandomSparsifier
from src.domain.graph_model import Graph, RunParams


@pytest.fixture
def sparsifier():
    return RandomSparsifier()

def test_p_one_retains_all_edges(complete5, sparsifier):
    result = sparsifier.run(complete5, RunParams({"p": 1.0}))
    assert result.edge_count == complete5.edge_count

def test_p_zero_drops_all_edges(complete5, sparsifier):
    result = sparsifier.run(complete5, RunParams({"p": 0.0}))
    assert result.edge_count == 0

def test_nodes_always_preserved(complete5, sparsifier):
    result = sparsifier.run(complete5, RunParams({"p": 0.0}))
    assert set(result.nodes()) == set(complete5.nodes())

def test_result_edge_count_bounded(path10, sparsifier):
    result = sparsifier.run(path10, RunParams({"p": 0.5}))
    assert result.edge_count <= path10.edge_count

def test_same_seed_gives_same_result(complete5):
    s = RandomSparsifier()
    params = RunParams({"p": 0.5, "seed": 42})
    r1 = s.run(complete5, params)
    r2 = s.run(complete5, params)
    assert set(r1.edges()) == set(r2.edges())

def test_different_seeds_may_differ(complete5):
    s = RandomSparsifier()
    r1 = s.run(complete5, RunParams({"p": 0.5, "seed": 1}))
    r2 = s.run(complete5, RunParams({"p": 0.5, "seed": 99999}))
    assert set(r1.edges()) != set(r2.edges())

def test_output_name_contains_random(path10, sparsifier):
    result = sparsifier.run(path10, RunParams({}))
    assert "random" in result.name

def test_directed_graph_stays_directed(directed, sparsifier):
    result = sparsifier.run(directed, RunParams({"p": 1.0}))
    assert result.is_directed()

def test_metadata_contains_p(complete5, sparsifier):
    result = sparsifier.run(complete5, RunParams({"p": 0.7}))
    assert result.metadata["p"] == pytest.approx(0.7)

def test_execute_injects_execution_time(complete5, no_params, sparsifier):
    result = sparsifier.execute(complete5, no_params)
    assert "execution_time" in result.metadata
