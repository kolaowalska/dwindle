from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict

from src.domain.graph_model import RunID, RunParams, new_run_id
from src.domain.metrics.base import MetricResult

class ExperimentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

# DOMAIN ENTITY

@dataclass
class Experiment:
    """
    domain entity representing a single execution of a graph algorithm.
    the entity encapsulates the identity (run_id), configuration (params),
    lifecycle state (status), and outcomes (results) of the execution
    """

    # identity
    run_id: RunID = field(default_factory=new_run_id)

    # state & configuration
    params: RunParams = field(default_factory=RunParams)
    status: ExperimentStatus = ExperimentStatus.PENDING

    # output
    results: Dict[str, MetricResult] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    # auditing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    def start(self) -> None:
        self.status = ExperimentStatus.RUNNING

    def finish(self) -> None:
        self.status = ExperimentStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)

    def failed(self, error_msg: str) -> None:
        self.status = ExperimentStatus.FAILED
        self.errors.append(error_msg)
        self.completed_at = datetime.now(timezone.utc)

    def add_result(self, name: str, result: MetricResult) -> None:
        self.results[name] = result

    @property
    def duration(self) -> Optional[float]:
        if self.completed_at:
            return (self.completed_at - self.created_at).total_seconds()
        return None

    def __hash__(self) -> int:
        return hash(self.run_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Experiment):
            return NotImplemented
        return self.run_id == other.run_id