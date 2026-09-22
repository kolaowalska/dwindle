from __future__ import annotations

import pytest

from src.domain.sparsifiers.registry import SparsifierRegistry
from src.domain.transforms.registry import TransformRegistry
from src.domain.transforms.base import TransformInfo


def _registered():
    SparsifierRegistry.discover()
    TransformRegistry.discover()
    return list(SparsifierRegistry.items()) + list(TransformRegistry.items())


@pytest.mark.parametrize("name,cls", _registered())
def test_every_algorithm_declares_info(name, cls):
    assert isinstance(getattr(cls, "INFO", None), TransformInfo), f"{name} has no INFO"

@pytest.mark.parametrize("name,cls", _registered())
def test_every_algorithm_info_has_name_and_abbrev(name, cls):
    assert cls.INFO.name.strip()
    assert cls.INFO.abbrev.strip()

def test_abbrevs_are_unique():
    abbrevs = [cls.INFO.abbrev for _, cls in _registered()]
    assert len(abbrevs) == len(set(abbrevs))
