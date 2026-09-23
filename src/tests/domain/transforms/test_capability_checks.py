from __future__ import annotations

import pytest

from src.domain.graph_model import Graph, RunParams
from src.domain.transforms.base import GraphTransform, TransformInfo


class _UndirectedOnly(GraphTransform):
    INFO = TransformInfo(name="undirected only", abbrev="uo", supports_directed=False)

    def run(self, graph: Graph, params: RunParams) -> Graph:
        return graph


class _UnweightedOnly(GraphTransform):
    INFO = TransformInfo(name="unweighted only", abbrev="wo", supports_weighted=False)

    def run(self, graph: Graph, params: RunParams) -> Graph:
        return graph


class _NoInfo(GraphTransform):
    def run(self, graph: Graph, params: RunParams) -> Graph:
        return graph


def test_directed_graph_is_refused(directed, no_params):
    with pytest.raises(ValueError, match="directed"):
        _UndirectedOnly().execute(directed, no_params)

def test_undirected_graph_is_accepted(path10, no_params):
    assert _UndirectedOnly().execute(path10, no_params).node_count == 10

def test_weighted_graph_is_refused(weighted, no_params):
    with pytest.raises(ValueError, match="weighted"):
        _UnweightedOnly().execute(weighted, no_params)

def test_unweighted_graph_is_accepted(path10, no_params):
    assert _UnweightedOnly().execute(path10, no_params).node_count == 10

def test_missing_info_reports_the_real_problem(path10, no_params):
    with pytest.raises(AttributeError, match="INFO"):
        _NoInfo().execute(path10, no_params)

def test_builtin_sparsifiers_still_accept_directed_graphs(directed, no_params):
    from src.domain.sparsifiers.registry import SparsifierRegistry
    for name in ("random", "k_neighbor", "local_degree", "identity_stub"):
        assert SparsifierRegistry.get(name).execute(directed, no_params) is not None
