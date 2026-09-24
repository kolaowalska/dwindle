from __future__ import annotations

from src.domain.common.registry import Registry
from .base import Sparsifier

SparsifierRegistry: Registry[Sparsifier] = Registry("sparsifier", "src.domain.sparsifiers")

_SPARSIFIERS = SparsifierRegistry._items

register_sparsifier = SparsifierRegistry.register
