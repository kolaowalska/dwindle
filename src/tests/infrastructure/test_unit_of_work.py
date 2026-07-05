from __future__ import annotations

import pytest

from src.infrastructure.persistence.unit_of_work import UnitOfWork
from src.infrastructure.persistence.stubs import InMemoryGraphRepository, InMemoryExperimentRepository
from src.domain.experiment import Experiment


@pytest.fixture
def repos():
    return InMemoryGraphRepository(), InMemoryExperimentRepository()

def test_commit_persists_registered_graph(path10, repos):
    graph_repo, exp_repo = repos
    uow = UnitOfWork(graph_repo, exp_repo)
    uow.register_new_graph(path10)
    uow.commit()
    assert graph_repo.get("path10") is path10

def test_commit_persists_registered_experiment(repos):
    graph_repo, exp_repo = repos
    uow = UnitOfWork(graph_repo, exp_repo)
    exp = Experiment()
    uow.register_new_experiment(exp)
    uow.commit()
    assert exp_repo.get(exp.run_id) is exp

def test_commit_sets_committed_flag(repos):
    graph_repo, exp_repo = repos
    uow = UnitOfWork(graph_repo, exp_repo)
    uow.commit()
    assert uow.committed is True

def test_committed_is_false_before_commit(repos):
    graph_repo, exp_repo = repos
    uow = UnitOfWork(graph_repo, exp_repo)
    assert uow.committed is False

def test_multiple_commits_do_not_raise(path10, repos):
    graph_repo, exp_repo = repos
    uow = UnitOfWork(graph_repo, exp_repo)
    uow.register_new_graph(path10)
    uow.commit()
    uow.commit()
    assert graph_repo.get("path10") is path10

def test_context_manager_auto_commits(path10, repos):
    graph_repo, exp_repo = repos
    with UnitOfWork(graph_repo, exp_repo) as uow:
        uow.register_new_graph(path10)
    assert graph_repo.get("path10") is path10

def test_context_manager_does_not_commit_on_exception(path10, repos):
    graph_repo, exp_repo = repos
    try:
        with UnitOfWork(graph_repo, exp_repo) as uow:
            uow.register_new_graph(path10)
            raise RuntimeError("intentional failure")
    except RuntimeError:
        pass
    assert graph_repo.get("path10") is None

def test_context_manager_returns_uow_instance(repos):
    graph_repo, exp_repo = repos
    with UnitOfWork(graph_repo, exp_repo) as uow:
        assert isinstance(uow, UnitOfWork)

def test_register_new_graph_queues_for_commit(path10, repos):
    graph_repo, exp_repo = repos
    uow = UnitOfWork(graph_repo, exp_repo)
    uow.register_new_graph(path10)
    assert graph_repo.get("path10") is None

def test_register_multiple_graphs(path10, complete5, repos):
    graph_repo, exp_repo = repos
    uow = UnitOfWork(graph_repo, exp_repo)
    uow.register_new_graph(path10)
    uow.register_new_graph(complete5)
    uow.commit()
    assert graph_repo.get("path10") is path10
    assert graph_repo.get("complete5") is complete5

def test_register_graph_and_experiment_together(path10, repos):
    graph_repo, exp_repo = repos
    uow = UnitOfWork(graph_repo, exp_repo)
    exp = Experiment()
    uow.register_new_graph(path10)
    uow.register_new_experiment(exp)
    uow.commit()
    assert graph_repo.get("path10") is path10
    assert exp_repo.get(exp.run_id) is exp
