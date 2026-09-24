from __future__ import annotations
import os
import networkx as nx
import pytest

from src.application.experiment_service import ExperimentService
from src.infrastructure.graph_gateway import GraphSource
from src.infrastructure.persistence.stubs import InMemoryGraphRepository, InMemoryExperimentRepository


def test_pipeline():
    # 1. setup
    graph_repo = InMemoryGraphRepository()
    exp_repo = InMemoryExperimentRepository()
    svc = ExperimentService(graph_repo, exp_repo)

    # 2. importing data
    nx_g = nx.path_graph(10)
    gkey = svc.import_graph(GraphSource(kind="memory", value=nx_g, name="test_graph"))

    # 3. running the experiment
    dto = svc.run_experiment(gkey, "identity_stub", ["diameter"])

    # 4. [LAYER SUPERTYPE] verification (metadata injection)
    assert "execution_time" in dto.metadata
    assert dto.metadata["algorithm"] == "IdentitySparsifier"
    print(f"graph transform took {dto.metadata['execution_time']:.5f}s")

    # 5. [UNIT OF WORK] verification (persistence)
    saved_graphs = graph_repo.list_names()
    assert len(saved_graphs) >= 2, f"expected original + result graphs, got: {saved_graphs}"
    assert any("identity" in name for name in saved_graphs)
    assert len(exp_repo._storage) == 1

    # 6. verifying metric results
    assert len(dto.metric_results) == 1
    result = dto.metric_results[0]

    assert result.metric == "diameter"

    assert result.summary["diameter_original"] == 9
    assert result.summary["diameter_reduced"] == 9
    assert result.summary["diameter_delta"] == 0