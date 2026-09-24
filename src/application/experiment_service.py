from __future__ import annotations

import time
from typing import Any, Optional, Dict

from src.domain.transforms.registry import TransformRegistry
from src.domain.graph_model import Graph, RunParams
from src.domain.experiment import Experiment
from src.domain.sparsifiers.registry import SparsifierRegistry
from src.domain.metrics.registry import MetricRegistry
from src.domain.metrics.base import MetricResult, RelativeMetric, DeltaMetric

from src.infrastructure.graph_gateway import GraphGateway, GraphSource
from src.infrastructure.persistence.repo import GraphRepository, ExperimentRepository
from src.infrastructure.persistence.unit_of_work import UnitOfWork
from src.application.dto import ExperimentDTO


class ExperimentService:
    def __init__(
            self,
            graph_repo: GraphRepository,
            experiment_repo: ExperimentRepository,
            gateway: Optional[GraphGateway] = None):
        self.graph_repo = graph_repo
        self.experiment_repo = experiment_repo
        self.gateway = gateway or GraphGateway()

    def import_graph(self, source: GraphSource) -> str:
        """
        imports a graph into the service store and returns an internal handle
        """
        graph = self.gateway.load(source)
        key = graph.name

        if self.graph_repo.get(key) is not None:
            i = 2
            while self.graph_repo.get(f"{key}_{i}") is not None:
                i += 1
            key = f"{key}_{i}"
            graph = Graph.from_networkx(
                graph.to_networkx(copy=True),
                name=key,
                metadata=dict(graph.metadata)
            )
        self.graph_repo.save(graph)
        return key

    def get_graph(self, graph_key: str) -> Graph:
        graph = self.graph_repo.get(graph_key)
        if graph is None:
            available = ", ".join(self.graph_repo.list_names())
            raise KeyError(f"graph not found: {graph_key}. available graphs: [{available}]")
        return graph

    def list_graphs(self) -> list[str]:
        return self.graph_repo.list_names()

    def run_sparsifier(
        self,
        graph_key: str,
        sparsifier_name: str,
        params: Dict[str, Any],
    ) -> Graph:
        """
        applies a sparsifier using [LAYER SUPERTYPE] execute method and returns a graph object
        """
        SparsifierRegistry.discover()

        G = self.get_graph(graph_key)
        sparsifier = SparsifierRegistry.get(sparsifier_name)

        # calls execute() (layer supertype) not run()!
        return sparsifier.execute(G, RunParams(params))


    def run_transform(
        self,
        graph_key: str,
        transform_name: str,
        params: Dict[str, Any],
    ) -> Graph:
        """
        applies a transformation using [LAYER SUPERTYPE] execute method and returns a graph object
        """
        TransformRegistry.discover()

        G = self.get_graph(graph_key)
        transform = TransformRegistry.get(transform_name)
        return transform.execute(G, RunParams(params))


    def compute_metrics(
        self,
        original: Graph,
        reduced: Graph,
        metric_names: list[str],
        params: Optional[Dict[str, Any]] = None,
    ) -> list[MetricResult]:
        """
        measures each metric on both graphs. absolute metrics are wrapped in a
        DeltaMetric, relative ones already take a pair.
        """
        MetricRegistry.discover()
        run_params = RunParams(params or {})
        results = []

        for name in metric_names:
            metric = MetricRegistry.get(name)

            start = time.perf_counter()
            if isinstance(metric, RelativeMetric):
                result = metric.compute(original, reduced, run_params)
            else:
                result = DeltaMetric(metric).compute_delta(original, reduced, run_params)
            duration = time.perf_counter() - start

            results.append(MetricResult(
                metric=metric.INFO.name,
                summary={**result.summary, "execution_time": duration},
                artifacts=result.artifacts,
            ))

        return results


# SERVICE LAYER ORCHESTRATION

    def run_experiment(
        self,
        graph_key: str,
        algorithm_name: str,
        metric_names: list[str],
        params: Optional[Dict[str, Any]] = None,
    ) -> ExperimentDTO:
        """
        uses the [DTO] to orchestrate an experiment within a [UNIT OF WORK]
        """
        # 0. start UOW
        uow = UnitOfWork(self.graph_repo, self.experiment_repo)
        run_params = params or {}
        original_graph = self.get_graph(graph_key)

        with uow:
            # 0. open the record first so created_at marks the start of the run
            experiment = Experiment(
                params=RunParams(run_params),
                graph_name=graph_key,
                algorithm=algorithm_name,
                nodes_before=original_graph.node_count,
                edges_before=original_graph.edge_count,
            )
            experiment.start()

            # 1. discovery
            SparsifierRegistry.discover()
            TransformRegistry.discover()

            # 2. polymorphic execution (timing handled inside execute())
            if algorithm_name in SparsifierRegistry.list():
                h = self.run_sparsifier(graph_key, algorithm_name, run_params)
            elif algorithm_name in TransformRegistry.list():
                h = self.run_transform(graph_key, algorithm_name, run_params)
            else:
                all_algos = sorted(SparsifierRegistry.list() + TransformRegistry.list())
                raise KeyError(f"algorithm '{algorithm_name}' not found. available: {all_algos}")

            # 3. compute metrics on both graphs
            metric_results = self.compute_metrics(original_graph, h, metric_names, run_params)

            # 4. close the record out
            experiment.nodes_after = h.node_count
            experiment.edges_after = h.edge_count
            experiment.transform_seconds = h.metadata.get("execution_time")
            for m in metric_results:
                experiment.add_result(m.metric, m)
            experiment.finish()

            # 5. register new objects; UnitOfWork commits on __exit__ when no exception
            uow.register_new_graph(h)
            uow.register_new_experiment(experiment)

        # 6. return DTO for UI/console
        return ExperimentDTO(
            graph_name=graph_key,
            reduced_graph_key=h.name,
            run_id=str(experiment.run_id),
            nodes_before=original_graph.node_count,
            edges_before=original_graph.edge_count,
            nodes_after=h.node_count,
            edges_after=h.edge_count,
            algorithm_name=algorithm_name,
            metric_results=metric_results,
            metadata=h.metadata,
            transform_seconds=experiment.transform_seconds,
        )

