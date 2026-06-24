from __future__ import annotations

import networkx as nx
import pytest

from src.application.experiment_service import ExperimentService
from src.interfaces.api import ExperimentFacade


@pytest.fixture
def facade():
    return ExperimentFacade()


def _upload_memory(facade, g, name):
    # kind="memory", value passed via "path" key (facade passes request_json["path"] as value)
    return facade.upload_graph({"kind": "memory", "path": g, "name": name})


# --- upload_graph ---

def test_upload_graph_returns_key(facade):
    resp = _upload_memory(facade, nx.path_graph(5), "p5")
    assert resp["status"] == "success"
    assert resp["graph_key"] == "p5"

def test_upload_graph_stores_in_service(facade):
    _upload_memory(facade, nx.path_graph(5), "p5")
    assert "p5" in facade.service.list_graphs()

def test_upload_graph_missing_payload_raises(facade):
    # "path" key is accessed outside the try/except → propagates KeyError
    with pytest.raises(KeyError):
        facade.upload_graph({})


# --- run_job ---

def test_run_job_returns_dto_dict(facade):
    _upload_memory(facade, nx.path_graph(10), "p10")
    resp = facade.run_job({
        "graph_key": "p10",
        "algorithm": "identity_stub",
        "metrics": ["diameter"],
    })
    assert resp["status"] == "success"
    data = resp["data"]
    assert data["graph_name"] == "p10"
    assert data["algorithm_name"] == "identity_stub"

def test_run_job_unknown_algorithm_raises(facade):
    _upload_memory(facade, nx.path_graph(5), "p5")
    with pytest.raises(KeyError):
        facade.run_job({
            "graph_key": "p5",
            "algorithm": "not_a_real_algorithm_xyzzy",
            "metrics": [],
        })

def test_run_job_unknown_graph_key_raises(facade):
    with pytest.raises(KeyError):
        facade.run_job({
            "graph_key": "ghost",
            "algorithm": "identity_stub",
            "metrics": [],
        })


# --- service property ---

def test_facade_exposes_service(facade):
    assert isinstance(facade.service, ExperimentService)
