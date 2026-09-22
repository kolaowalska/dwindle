from __future__ import annotations

import math
import warnings

import networkx as nx
import pytest

from src.domain.graph_model import Graph, RunParams, new_graph_id


def test_from_networkx_preserves_node_edge_count(path10):
    assert path10.node_count == 10
    assert path10.edge_count == 9

def test_from_networkx_name_is_set(path10):
    assert path10.name == "path10"

def test_from_networkx_directed_flag(directed):
    assert directed.is_directed() is True

def test_from_networkx_undirected_flag(path10):
    assert path10.is_directed() is False

def test_from_loader_defers_load():
    calls = []
    def loader():
        calls.append(1)
        return nx.path_graph(3)
    g = Graph.from_loader(name="lazy", loader_f=loader)
    assert len(calls) == 0
    _ = g.node_count
    assert len(calls) == 1

def test_from_loader_caches_after_first_access():
    calls = []
    def loader():
        calls.append(1)
        return nx.path_graph(3)
    g = Graph.from_loader(name="lazy", loader_f=loader)
    g.to_networkx()
    g.to_networkx()
    assert len(calls) == 1

def test_node_count_empty(empty):
    assert empty.node_count == 0

def test_edge_count_empty(empty):
    assert empty.edge_count == 0

def test_copy_is_independent(path10):
    copy = path10.copy()
    nx_copy = copy.to_networkx()
    nx_copy.remove_node(0)
    assert path10.node_count == 10

def test_edge_weight_returns_value(weighted):
    assert weighted.edge_weight(0, 1) == pytest.approx(2.0)

def test_edge_weight_missing_raises(path10):
    with pytest.raises(KeyError):
        path10.edge_weight(0, 9)

def test_is_weighted_true_for_weighted_graph(weighted):
    assert weighted.is_weighted() is True

def test_is_weighted_false_for_plain_graph(path10):
    assert path10.is_weighted() is False

def test_run_params_get_returns_value():
    p = RunParams({"k": 3})
    assert p.get("k") == 3

def test_run_params_get_returns_default():
    p = RunParams({})
    assert p.get("missing", 42) == 42

def test_run_params_with_overrides_merges():
    p = RunParams({"k": 3, "seed": 1})
    p2 = p.with_overrides(seed=99)
    assert p2.get("k") == 3
    assert p2.get("seed") == 99

def test_run_params_with_overrides_does_not_mutate_original():
    p = RunParams({"k": 3})
    p.with_overrides(k=99)
    assert p.get("k") == 3

def test_empty_graph_is_not_mistaken_for_missing():
    """networkx graphs are falsy when empty, so `if self._nx` took the None branch."""
    assert Graph(nx.Graph(), id="e").directed is False
    assert Graph(nx.DiGraph(), id="e").directed is True

def test_empty_graph_directed_flag_matches_is_directed():
    g = Graph(nx.DiGraph(), id="e")
    assert g.directed == g.is_directed()

def test_perron_root_is_positive_on_bipartite_graph():
    """which='LM' could return -lambda on a bipartite spectrum, giving log(neg) = nan."""
    b = nx.complete_bipartite_graph(30, 30)
    for _ in range(25):
        props = Graph(b, id="b").spectral_properties
        assert props["lambda"] == pytest.approx(30.0)
        assert math.isfinite(props["entropy_rate"])

def test_entropy_rate_without_edges_is_negative_infinity():
    """log(0) used to be evaluated directly, emitting a divide-by-zero warning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        props = Graph(nx.empty_graph(5), id="n").spectral_properties
    assert props["entropy_rate"] == float("-inf")
