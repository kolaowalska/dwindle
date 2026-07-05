from __future__ import annotations

import logging
from typing import List
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

    def register_new_graph(self, graph: Graph):
        self._new_graphs.append(graph)

    def register_new_experiment(self, experiment: Experiment):
        self._new_experiments.append(experiment)

    def commit(self):
        log.info("committing transaction")

        for g in self._new_graphs:
            self.graph_repo.save(g)
        for e in self._new_experiments:
            self.experiment_repo.save(e)

        self.committed = True
        log.info(f"committed: {len(self._new_graphs)} graph(s), {len(self._new_experiments)} experiment(s)")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.committed and exc_type is None:
            self.commit()
        elif exc_type:
            log.warning(f"rolling back due to error: {exc_val}")
