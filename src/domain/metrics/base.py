from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Mapping, Literal

from src.domain.graph_model import Graph, RunParams, ArtifactHandle


@dataclass(frozen=True)
class MetricInfo:
    name: str
    type: Literal["absolute", "relative"] = "absolute"
    version: str = "0.1.0"
    description: str = ""

@dataclass(frozen=True)
class MetricResult:
    """results returned by Metric.compute()"""
    metric: str
    summary: Mapping[str, float | int | str] = field(default_factory=dict)
    artifacts: Mapping[str, ArtifactHandle] = field(default_factory=dict)


class Metric(ABC):
    INFO: MetricInfo

    @abstractmethod
    def compute(self, graph: Graph, params: RunParams) -> MetricResult:
        pass


class RelativeMetric(ABC):
    """
    for metrics that are inherently two-graph. use DeltaMetric instead
    if you just want before and after deltas for a specific Metric.
    """
    INFO: MetricInfo

    @abstractmethod
    def compute(self, g: Graph, h: Graph, params: RunParams) -> MetricResult:
        pass

class DeltaMetric(Metric):
    """
    decorator that wraps any Metric and computes the delta
    between the original and reduced graph. satisfies the Metric
    interface so it can be used anywhere a Metric is expected.
    """

    def __init__(self, base_metric: Metric):
        self.base_metric = base_metric
        self.INFO = MetricInfo(
            name=f"{base_metric.INFO.name} delta",
            type="absolute",
            description=f"delta of {base_metric.INFO.name} between two graphs",
        )

    def compute(self, graph: Graph, params: RunParams) -> MetricResult:
        """
        single-graph call - delegates to the wrapped metric
        """
        return self.base_metric.compute(graph, params)

    def compute_delta(self, g: Graph, h: Graph, params: RunParams) -> MetricResult:
        """
        two-graph call - computes the before and after diff
        """
        g_result = self.base_metric.compute(g, params)
        h_result = self.base_metric.compute(h, params)
        g_summary, h_summary = g_result.summary, h_result.summary

        delta_summary: dict[str, float | int | str] = {}
        for key in g_summary.keys():
            g_val = g_summary[key]
            h_val = h_summary.get(key)

            numeric = (int, float)
            if (
                isinstance(g_val, numeric) and not isinstance(g_val, bool)
                and isinstance(h_val, numeric) and not isinstance(h_val, bool)
            ):
                delta_summary[f"{key}_original"] = g_val
                delta_summary[f"{key}_reduced"] = h_val
                delta_summary[f"{key}_delta"] = h_val - g_val
            else:
                delta_summary[key] = g_val

        return MetricResult(
            metric=self.INFO.name,
            summary=delta_summary,
            artifacts=h_result.artifacts,
        )
