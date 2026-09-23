from __future__ import annotations

import logging
from typing import Any, List, Tuple
from src.infrastructure.persistence.repo import GraphRepository, ExperimentRepository
from src.domain.graph_model import Graph
from src.domain.experiment import Experiment

log = logging.getLogger(__name__)


class UnitOfWork:
    """
    [UNIT OF WORK] maintains a list of objects affected by a
    transaction and coordinates the writing out of changes
    """
    def __init__(self, graph_repo: GraphRepository, experiment_repo: ExperimentRepository):
        self.graph_repo = graph_repo
        self.experiment_repo = experiment_repo
        self._new_graphs: List[Graph] = []
        self._new_experiments: List[Experiment] = []
        self.committed = False
        self.rolled_back = False

    def register_new_graph(self, graph: Graph):
        self._new_graphs.append(graph)

    def register_new_experiment(self, experiment: Experiment):
        self._new_experiments.append(experiment)

    def commit(self):
        log.info("committing transaction")
        applied: List[Tuple[Any, Any, Any]] = []

        try:
            for g in self._new_graphs:
                applied.append((self.graph_repo, g.name, self.graph_repo.get(g.name)))
                self.graph_repo.save(g)
            for e in self._new_experiments:
                applied.append((self.experiment_repo, e.run_id, self.experiment_repo.get(e.run_id)))
                self.experiment_repo.save(e)
        except Exception as exc:
            log.warning(f"commit failed, undoing {len(applied)} journalled write(s): {exc}")
            self._undo(applied)
            self.rolled_back = True
            raise

        self.committed = True
        log.info(f"committed: {len(self._new_graphs)} graph(s), {len(self._new_experiments)} experiment(s)")

    @staticmethod
    def _undo(applied: List[Tuple[Any, Any, Any]]) -> None:
        for repo, key, previous in reversed(applied):
            if previous is None:
                repo.delete(key)
            else:
                repo.save(previous)

    def rollback(self):
        log.info(f"rolling back: discarding {len(self._new_graphs)} graph(s), "
                 f"{len(self._new_experiments)} experiment(s)")
        self._new_graphs.clear()
        self._new_experiments.clear()
        self.rolled_back = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            log.warning(f"rolling back due to error: {exc_val}")
            self.rollback()
        elif not self.committed:
            self.commit()
