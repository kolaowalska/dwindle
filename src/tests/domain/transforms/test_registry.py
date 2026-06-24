from __future__ import annotations

import pytest

from src.domain.transforms.registry import TransformRegistry, _TRANSFORMS
from src.domain.transforms.base import GraphTransform, TransformInfo
from src.domain.graph_model import Graph, RunParams


class _DummyTransform(GraphTransform):
    INFO = TransformInfo(name="dummy_transform", abbrev="dt")

    def run(self, graph: Graph, params: RunParams) -> Graph:
        return graph

def test_register_and_retrieve():
    key = "_test_transform_dummy_abc"
    try:
        TransformRegistry.register(key)(_DummyTransform)
        assert isinstance(TransformRegistry.get(key), _DummyTransform)
    finally:
        _TRANSFORMS.pop(key, None)

def test_register_duplicate_name_raises():
    key = "_test_transform_dup_xyz"

    class _OtherTransform(GraphTransform):
        INFO = TransformInfo(name="other_transform", abbrev="ot")
        def run(self, graph: Graph, params: RunParams) -> Graph:
            return graph

    try:
        TransformRegistry.register(key)(_DummyTransform)
        with pytest.raises(ValueError, match="already registered"):
            TransformRegistry.register(key)(_OtherTransform)
    finally:
        _TRANSFORMS.pop(key, None)

def test_discover_populates_known_transforms():
    TransformRegistry.discover()
    names = TransformRegistry.list()
    assert "mock_coarsening" in names
    assert "merw_coarsening" in names

def test_discover_is_idempotent():
    TransformRegistry.discover()
    before = set(TransformRegistry.list())
    TransformRegistry.discover()
    assert set(TransformRegistry.list()) == before

def test_get_unknown_name_raises_key_error():
    TransformRegistry.discover()
    with pytest.raises(KeyError):
        TransformRegistry.get("not_a_real_transform_xyzzy123")

def test_list_returns_sorted():
    TransformRegistry.discover()
    names = TransformRegistry.list()
    assert names == sorted(names)
