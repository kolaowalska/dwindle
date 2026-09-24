from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.domain.experiment import Experiment, ExperimentStatus
from src.domain.graph_model import RunID, RunParams
from src.domain.metrics.base import MetricResult
from src.infrastructure.persistence.repo import ExperimentRepository

log = logging.getLogger(__name__)

STORE_ENV_VAR = "DWINDLE_STORE"
DEFAULT_STORE = ".dwindle"


def resolve_store(explicit: Optional[str] = None) -> Path:
    return Path(explicit or os.environ.get(STORE_ENV_VAR) or DEFAULT_STORE)


def _jsonable(value: Any) -> Any:
    """numpy scalars and the like reach summaries; keep the file readable"""
    if isinstance(value, (str, bool, int, float)) or value is None:
        return value
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return str(value)


class ExperimentMapper:
    """[DATA MAPPER] between the Experiment entity and a plain json row"""

    @staticmethod
    def to_row(experiment: Experiment) -> Dict[str, Any]:
        return {
            "run_id": str(experiment.run_id),
            "status": experiment.status.value,
            "graph_name": experiment.graph_name,
            "algorithm": experiment.algorithm,
            "params": {k: _jsonable(v) for k, v in dict(experiment.params.values).items()},
            "nodes_before": experiment.nodes_before,
            "edges_before": experiment.edges_before,
            "nodes_after": experiment.nodes_after,
            "edges_after": experiment.edges_after,
            "transform_seconds": experiment.transform_seconds,
            "created_at": experiment.created_at.isoformat(),
            "completed_at": experiment.completed_at.isoformat() if experiment.completed_at else None,
            "duration_seconds": experiment.duration,
            "errors": list(experiment.errors),
            # artifacts deliberately not persisted
            "results": {
                name: {k: _jsonable(v) for k, v in dict(result.summary).items()}
                for name, result in experiment.results.items()
            },
        }

    @staticmethod
    def to_domain(row: Dict[str, Any]) -> Experiment:
        experiment = Experiment(
            run_id=RunID(row["run_id"]),
            params=RunParams(row.get("params") or {}),
            status=ExperimentStatus(row.get("status", "pending")),
            graph_name=row.get("graph_name"),
            algorithm=row.get("algorithm"),
            nodes_before=row.get("nodes_before"),
            edges_before=row.get("edges_before"),
            nodes_after=row.get("nodes_after"),
            edges_after=row.get("edges_after"),
            transform_seconds=row.get("transform_seconds"),
            created_at=datetime.fromisoformat(row["created_at"]),
            completed_at=(
                datetime.fromisoformat(row["completed_at"]) if row.get("completed_at") else None
            ),
            errors=list(row.get("errors") or []),
        )
        for name, summary in (row.get("results") or {}).items():
            experiment.add_result(name, MetricResult(metric=name, summary=summary))
        return experiment


class JsonExperimentRepository(ExperimentRepository):
    """
    [REPOSITORY] backed by one json file per run. swapping in a database
    means writing another ExperimentRepository, nothing above this changes.
    """

    def __init__(self, store: str | Path = DEFAULT_STORE):
        self.root = Path(store) / "experiments"
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, run_id: RunID) -> Path:
        return self.root / f"{run_id}.json"

    def save(self, experiment: Experiment) -> None:
        path = self._path(experiment.run_id)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(ExperimentMapper.to_row(experiment), indent=2))
        tmp.replace(path)
        log.debug(f"wrote {path}")

    def get(self, run_id: RunID) -> Optional[Experiment]:
        path = self._path(run_id)
        if not path.exists():
            return None
        return ExperimentMapper.to_domain(json.loads(path.read_text()))

    def delete(self, run_id: RunID) -> None:
        self._path(run_id).unlink(missing_ok=True)

    def list_all(self) -> List[Experiment]:
        experiments = []
        for path in self.root.glob("*.json"):
            try:
                experiments.append(ExperimentMapper.to_domain(json.loads(path.read_text())))
            except Exception as e:
                log.warning(f"skipping unreadable run {path.name}: {e}")
        return sorted(experiments, key=lambda e: e.created_at)
