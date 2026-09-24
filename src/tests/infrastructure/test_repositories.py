from __future__ import annotations

import networkx as nx

from src.domain.graph_model import Graph
from src.domain.experiment import Experiment
from src.infrastructure.persistence.stubs import (
    InMemoryGraphRepository,
    InMemoryExperimentRepository,
)


def test_graph_repo_save_and_get(path10):
    repo = InMemoryGraphRepository()
    repo.save(path10)
    assert repo.get("path10") is path10

def test_graph_repo_get_missing_returns_none():
    repo = InMemoryGraphRepository()
    assert repo.get("ghost") is None

def test_graph_repo_list_names_sorted(path10, complete5):
    repo = InMemoryGraphRepository()
    repo.save(complete5)
    repo.save(path10)
    assert repo.list_names() == ["complete5", "path10"]

def test_graph_repo_overwrite_on_same_name():
    repo = InMemoryGraphRepository()
    g1 = Graph.from_networkx(nx.path_graph(3), name="g")
    g2 = Graph.from_networkx(nx.path_graph(7), name="g")
    repo.save(g1)
    repo.save(g2)
    assert repo.get("g").node_count == 7

def test_graph_repo_empty_list():
    assert InMemoryGraphRepository().list_names() == []

def test_graph_repo_save_multiple(path10, complete5):
    repo = InMemoryGraphRepository()
    repo.save(path10)
    repo.save(complete5)
    assert set(repo.list_names()) == {"path10", "complete5"}

def test_experiment_repo_save_and_get():
    repo = InMemoryExperimentRepository()
    exp = Experiment()
    repo.save(exp)
    assert repo.get(exp.run_id) is exp

def test_experiment_repo_get_missing_returns_none():
    repo = InMemoryExperimentRepository()
    assert repo.get("no-such-run-id") is None

def test_experiment_repo_multiple_experiments():
    repo = InMemoryExperimentRepository()
    e1, e2 = Experiment(), Experiment()
    repo.save(e1)
    repo.save(e2)
    assert repo.get(e1.run_id) is e1
    assert repo.get(e2.run_id) is e2

def test_experiment_repo_overwrite_on_same_run_id():
    repo = InMemoryExperimentRepository()
    e1 = Experiment()
    e2 = Experiment()
    object.__setattr__(e2, "run_id", e1.run_id)
    repo.save(e1)
    repo.save(e2)
    assert repo.get(e1.run_id) is e2

def test_graph_repository_delete_removes_entry(path10):
    repo = InMemoryGraphRepository()
    repo.save(path10)
    repo.delete("path10")
    assert repo.get("path10") is None

def test_graph_repository_delete_missing_key_is_noop():
    InMemoryGraphRepository().delete("nothing-here")

def test_experiment_repository_delete_removes_entry():
    repo = InMemoryExperimentRepository()
    exp = Experiment()
    repo.save(exp)
    repo.delete(exp.run_id)
    assert repo.get(exp.run_id) is None
