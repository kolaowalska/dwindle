from __future__ import annotations

from abc import ABC
from src.domain.transforms.base import GraphTransform


class Sparsifier(GraphTransform, ABC):
    """
    [SEPARATED INTERFACE] marker class (specifically a sparsifier)
    inherits 'execute' from GraphTransform
    """
    pass
