from __future__ import annotations

from src.domain.common.registry import Registry
from .base import GraphTransform

TransformRegistry: Registry[GraphTransform] = Registry("transform", "src.domain.transforms")

_TRANSFORMS = TransformRegistry._items

register_transform = TransformRegistry.register
