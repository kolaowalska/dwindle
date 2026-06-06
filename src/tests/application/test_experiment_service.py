from __future__ import annotations

import networkx as nx
import pytest

from src.application.dto import ExperimentDTO
from src.application.experiment_service import ExperimentService
from src.domain.graph_model import Graph
from src.infrastructure.graph_gateway import GraphSource
from src.infrastructure.persistence.stubs import InMemoryGraphRepository, InMemoryExperimentRepository


def _import(service, g, name):
    return service.import_graph(GraphSource(kind="memory", value=g, name=name))


# --- import_graph ---

def test_import_graph_returns_key(service):
    key = _import(service, nx.path_graph(10), "p10")
    assert key == "p10"

def test_import_graph_stores_in_repo(service):
    key = _import(service, nx.path_graph(10), "p10")
    assert key in service.list_graphs()

def test_import_graph_collision_renames(service):
    g = nx.path_graph(5)
    _import(service, g, "g")
    key2 = _import(service, g, "g")
    assert key2 == "g_2"

def test_import_graph_triple_collision_increments(service):
    g = nx.path_graph(3)
    _import(service, g, "g")
    _import(service, g, "g")
    key3 = _import(service, g, "g")
    assert key3 == "g_3"


# --- get_graph ---

def test_get_graph_returns_existing(service):
    _import(service, nx.path_graph(10), "p10")
    graph = service.get_graph("p10")
    assert graph.node_count == 10

def test_get_graph_missing_raises_key_error(service):
    with pytest.raises(KeyError, match="ghost"):
        service.get_graph("ghost")

def test_list_graphs_empty_initially(service):
    assert service.list_graphs() == []

def test_list_graphs_returns_all_imported(service):
    _import(service, nx.path_graph(5), "a")
    _import(service, nx.path_graph(5), "b")
    assert set(service.list_graphs()) == {"a", "b"}


# --- run_sparsifier ---

def test_run_sparsifier_returns_graph(service):
    key = _import(service, nx.path_graph(10), "p10")
    result = service.run_sparsifier(key, "identity_stub", {})
    assert isinstance(result, Graph)

def test_run_sparsifier_identity_preserves_graph(service):
    key = _import(service, nx.path_graph(10), "p10")
    result = service.run_sparsifier(key, "identity_stub", {})
    assert result.node_count == 10
    assert result.edge_count == 9

def test_run_sparsifier_unknown_raises(service):
    key = _import(service, nx.path_graph(10), "p10")
    with pytest.raises(KeyError):
        service.run_sparsifier(key, "not_real", {})

def test_run_sparsifier_missing_graph_raises(service):
    with pytest.raises(KeyError):
        service.run_sparsifier("ghost", "identity_stub", {})


# --- run_transform ---

def test_run_transform_returns_graph(service):
    key = _import(service, nx.complete_graph(6), "k6")
    result = service.run_transform(key, "mock_coarsening", {"reduction_ratio": 0.5})
    assert isinstance(result, Graph)

def test_run_transform_reduces_nodes(service):
    key = _import(service, nx.complete_graph(10), "k10")
    result = service.run_transform(key, "mock_coarsening", {"reduction_ratio": 0.5})
    assert result.node_count < 10


# --- compute_metrics ---

def test_compute_metrics_returns_results_for_each_name(service):
    key = _import(service, nx.path_graph(10), "p10")
    graph = service.get_graph(key)
    results = service.compute_metrics(graph, ["diameter"])
    assert len(results) == 1
    assert results[0].metric == "diameter"

def test_compute_metrics_multiple_names(service):
    key = _import(service, nx.path_graph(10), "p10")
    graph = service.get_graph(key)
    results = service.compute_metrics(graph, ["diameter", "clustering"])
    assert len(results) == 2
    names = {r.metric for r in results}
    assert "diameter" in names
    assert "clustering" in names

def test_compute_metrics_injects_execution_time(service):
    key = _import(service, nx.path_graph(10), "p10")
    graph = service.get_graph(key)
    results = service.compute_metrics(graph, ["diameter"])
    assert "execution_time" in results[0].summary

def test_compute_metrics_unknown_metric_raises(service):
    key = _import(service, nx.path_graph(10), "p10")
    graph = service.get_graph(key)
    with pytest.raises(KeyError):
        service.compute_metrics(graph, ["not_a_metric"])

def test_compute_metrics_empty_list_returns_empty(service):
    key = _import(service, nx.path_graph(10), "p10")
    graph = service.get_graph(key)
    assert service.compute_metrics(graph, []) == []


# --- run_experiment ---

def test_run_experiment_returns_dto(service):
    key = _import(service, nx.path_graph(10), "p10")
    dto = service.run_experiment(key, "identity_stub", ["diameter"])
    assert isinstance(dto, ExperimentDTO)
    assert dto.graph_name == key
    assert dto.algorithm_name == "identity_stub"

def test_run_experiment_persists_reduced_graph(service):
    key = _import(service, nx.path_graph(10), "p10")
    dto = service.run_experiment(key, "identity_stub", ["diameter"])
    assert dto.reduced_graph_key in service.list_graphs()

def test_run_experiment_persists_experiment_entity(service):
    key = _import(service, nx.path_graph(10), "p10")
    service.run_experiment(key, "identity_stub", ["diameter"])
    assert len(service.experiment_repo._storage) == 1

def test_run_experiment_dto_topology_fields(service):
    key = _import(service, nx.path_graph(10), "p10")
    dto = service.run_experiment(key, "identity_stub", ["diameter"])
    assert dto.nodes_before == 10
    assert dto.edges_before == 9
    assert isinstance(dto.nodes_after, int) and dto.nodes_after >= 0
    assert isinstance(dto.edges_after, int) and dto.edges_after >= 0

def test_run_experiment_metric_results_present(service):
    key = _import(service, nx.path_graph(10), "p10")
    dto = service.run_experiment(key, "identity_stub", ["diameter"])
    assert len(dto.metric_results) == 1
    assert dto.metric_results[0].metric == "diameter"

def test_run_experiment_metadata_has_execution_time(service):
    key = _import(service, nx.path_graph(10), "p10")
    dto = service.run_experiment(key, "identity_stub", ["diameter"])
    assert "execution_time" in dto.metadata

def test_run_experiment_unknown_algorithm_raises(service):
    key = _import(service, nx.path_graph(10), "p10")
    with pytest.raises(KeyError):
        service.run_experiment(key, "nonexistent_algo", [])
