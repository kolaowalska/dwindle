from __future__ import annotations

import json

import numpy as np
import pytest

from src.domain.experiment import Experiment, ExperimentStatus
from src.domain.graph_model import RunParams
from src.domain.metrics.base import MetricResult
from src.infrastructure.persistence.json_store import (
    DEFAULT_STORE,
    ExperimentMapper,
    JsonExperimentRepository,
    resolve_store,
)


@pytest.fixture
def repo(tmp_path):
    return JsonExperimentRepository(tmp_path / "store")


@pytest.fixture
def experiment():
    e = Experiment(
        params=RunParams({"rho": 0.5}),
        graph_name="karate",
        algorithm="k_neighbor",
        nodes_before=34, edges_before=78,
        nodes_after=34, edges_after=48,
        transform_seconds=0.031,
    )
    e.start()
    e.add_result("clustering", MetricResult(metric="clustering", summary={"avg_delta": -0.3}))
    e.finish()
    return e


# --- round trip ---

def test_saved_run_can_be_read_back(repo, experiment):
    repo.save(experiment)
    loaded = repo.get(experiment.run_id)
    assert loaded is not None
    assert loaded.run_id == experiment.run_id
    assert loaded.graph_name == "karate"
    assert loaded.algorithm == "k_neighbor"

def test_round_trip_preserves_provenance(repo, experiment):
    repo.save(experiment)
    loaded = repo.get(experiment.run_id)
    assert loaded.params.get("rho") == 0.5
    assert (loaded.nodes_before, loaded.edges_before) == (34, 78)
    assert (loaded.nodes_after, loaded.edges_after) == (34, 48)
    assert loaded.transform_seconds == pytest.approx(0.031)
    assert loaded.status is ExperimentStatus.COMPLETED

def test_round_trip_preserves_metric_summaries(repo, experiment):
    repo.save(experiment)
    loaded = repo.get(experiment.run_id)
    assert loaded.results["clustering"].summary["avg_delta"] == pytest.approx(-0.3)

def test_round_trip_preserves_timestamps(repo, experiment):
    repo.save(experiment)
    loaded = repo.get(experiment.run_id)
    assert loaded.created_at == experiment.created_at
    assert loaded.completed_at == experiment.completed_at

def test_missing_run_returns_none(repo):
    assert repo.get("no-such-run") is None


# --- collection behaviour ---

def test_list_all_returns_every_saved_run(repo):
    for name in ("a", "b", "c"):
        e = Experiment(graph_name=name)
        e.finish()
        repo.save(e)
    assert {e.graph_name for e in repo.list_all()} == {"a", "b", "c"}

def test_list_all_is_ordered_by_creation(repo):
    made = []
    for name in ("first", "second", "third"):
        e = Experiment(graph_name=name)
        e.finish()
        repo.save(e)
        made.append(e)
    assert [e.graph_name for e in repo.list_all()] == ["first", "second", "third"]

def test_list_all_empty_store(repo):
    assert repo.list_all() == []

def test_delete_removes_the_file(repo, experiment):
    repo.save(experiment)
    repo.delete(experiment.run_id)
    assert repo.get(experiment.run_id) is None
    assert repo.list_all() == []

def test_unreadable_run_is_skipped_not_fatal(repo, experiment):
    repo.save(experiment)
    (repo.root / "corrupt.json").write_text("{not json")
    assert len(repo.list_all()) == 1


# --- persistence across instances ---

def test_a_second_repository_sees_earlier_runs(tmp_path, experiment):
    JsonExperimentRepository(tmp_path / "s").save(experiment)
    assert len(JsonExperimentRepository(tmp_path / "s").list_all()) == 1


# --- serialisation edge cases ---

def test_numpy_scalars_survive_serialisation(repo):
    e = Experiment(graph_name="np")
    e.add_result("m", MetricResult(metric="m", summary={"v": np.float64(1.5)}))
    e.finish()
    repo.save(e)
    assert json.loads((repo.root / f"{e.run_id}.json").read_text())["results"]["m"]["v"] == 1.5

def test_artifacts_are_not_persisted(repo):
    e = Experiment(graph_name="art")
    e.add_result("m", MetricResult(metric="m", summary={"v": 1}, artifacts={"blob": "x"}))
    e.finish()
    repo.save(e)
    assert "artifacts" not in json.loads((repo.root / f"{e.run_id}.json").read_text())

def test_mapper_row_is_json_serialisable(experiment):
    json.dumps(ExperimentMapper.to_row(experiment))


# --- store location ---

def test_store_defaults_when_nothing_set(monkeypatch):
    monkeypatch.delenv("DWINDLE_STORE", raising=False)
    assert resolve_store() == pytest.importorskip("pathlib").Path(DEFAULT_STORE)

def test_env_var_sets_the_store(monkeypatch):
    monkeypatch.setenv("DWINDLE_STORE", "/tmp/from-env")
    assert str(resolve_store()) == "/tmp/from-env"

def test_explicit_path_beats_the_env_var(monkeypatch):
    monkeypatch.setenv("DWINDLE_STORE", "/tmp/from-env")
    assert str(resolve_store("/tmp/explicit")) == "/tmp/explicit"
