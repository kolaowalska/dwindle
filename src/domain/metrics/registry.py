from __future__ import annotations

from typing import Union

from src.domain.common.registry import Registry
from .base import Metric, RelativeMetric

MetricRegistry: Registry[Union[Metric, RelativeMetric]] = Registry("metric", "src.domain.metrics")

_METRICS = MetricRegistry._items

register_metric = MetricRegistry.register
