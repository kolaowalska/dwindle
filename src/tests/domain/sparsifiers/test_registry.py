from __future__ import annotations

import pytest

from src.domain.sparsifiers.registry import SparsifierRegistry, _SPARSIFIERS
from src.domain.sparsifiers.base import Sparsifier
from src.domain.graph_model import Graph, RunParams
from src.domain.transforms.base import TransformInfo


class _DummySparsifier(Sparsifier):
    INFO = TransformInfo(name="dummy", abbrev="d")

    def run(self, graph: Graph, params: RunParams) -> Graph:
        return graph

def test_register_and_retrieve():
    key = "_test_reg_dummy_abc"
    try:
        SparsifierRegistry.register(key)(_DummySparsifier)
        assert isinstance(SparsifierRegistry.get(key), _DummySparsifier)
    finally:
        _SPARSIFIERS.pop(key, None)

def test_register_duplicate_name_raises():
    key = "_test_reg_dup_xyz"

    class _OtherDummy(Sparsifier):
        INFO = TransformInfo(name="other_dummy", abbrev="od")
        def run(self, graph: Graph, params: RunParams) -> Graph:
            return graph

    try:
        SparsifierRegistry.register(key)(_DummySparsifier)
        with pytest.raises(ValueError, match="already registered"):
            SparsifierRegistry.register(key)(_OtherDummy)
    finally:
        _SPARSIFIERS.pop(key, None)

# TODO
def test_discover_populates_known_sparsifiers():
    SparsifierRegistry.discover()
    names = SparsifierRegistry.list()
    for expected in ["random", "k_neighbor", "local_degree", "pagerank", "merw", "identity_stub"]:
        assert expected in names

def test_discover_is_idempotent():
    SparsifierRegistry.discover()
    before = set(SparsifierRegistry.list())
    SparsifierRegistry.discover()
    assert set(SparsifierRegistry.list()) == before

def test_get_unknown_name_raises_key_error():
    SparsifierRegistry.discover()
    with pytest.raises(KeyError):
        SparsifierRegistry.get("not_a_real_sparsifier_xyzzy123")

def test_list_returns_sorted():
    SparsifierRegistry.discover()
    names = SparsifierRegistry.list()
    assert names == sorted(names)
