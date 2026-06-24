from __future__ import annotations

import networkx as nx
import pytest

from src.domain.graph_model import Graph
from src.infrastructure.graph_gateway import GraphGateway, GraphSource


@pytest.fixture
def gateway():
    return GraphGateway()


# memory source

def test_load_from_memory_networkx(gateway):
    result = gateway.load(GraphSource(kind="memory", value=nx.path_graph(5), name="p5"))
    assert isinstance(result, Graph)
    assert result.node_count == 5
    assert result.edge_count == 4

def test_load_from_memory_name_is_set(gateway):
    result = gateway.load(GraphSource(kind="memory", value=nx.path_graph(3), name="myname"))
    assert result.name == "myname"

def test_load_from_memory_none_returns_empty_domain_graph(gateway):
    result = gateway.load(GraphSource(kind="memory", value=None, name="empty"))
    assert isinstance(result, Graph)
    assert result.node_count == 0
    assert result.name == "empty"

def test_load_from_memory_directed(gateway):
    g = nx.DiGraph([(0, 1), (1, 2)])
    result = gateway.load(GraphSource(kind="memory", value=g, name="dg"))
    assert result.is_directed()


# lazy loading

def test_load_from_edgelist_file_returns_graph(gateway, tmp_path):
    edgefile = tmp_path / "graph.edgelist"
    edgefile.write_text("0 1\n1 2\n2 3\n")
    result = gateway.load(GraphSource(kind="file", value=str(edgefile), name="test"))
    assert isinstance(result, Graph)

def test_load_from_edgelist_file_correct_topology(gateway, tmp_path):
    edgefile = tmp_path / "graph.edgelist"
    edgefile.write_text("0 1\n1 2\n2 3\n")
    result = gateway.load(GraphSource(kind="file", value=str(edgefile), name="test"))
    assert result.node_count == 4
    assert result.edge_count == 3

def test_lazy_loading_does_not_read_file_immediately(gateway, tmp_path):
    edgefile = tmp_path / "graph.edgelist"
    edgefile.write_text("0 1\n1 2\n")
    result = gateway.load(GraphSource(kind="file", value=str(edgefile), name="lazy"))
    assert result._nx is None

def test_lazy_loading_populates_on_access(gateway, tmp_path):
    edgefile = tmp_path / "graph.edgelist"
    edgefile.write_text("0 1\n1 2\n")
    result = gateway.load(GraphSource(kind="file", value=str(edgefile), name="lazy"))
    _ = result.node_count
    assert result._nx is not None


# error handling

def test_file_not_found_raises(gateway):
    with pytest.raises(FileNotFoundError):
        gateway.load(GraphSource(kind="file", value="/nonexistent/path.edgelist", name="x"))

def test_file_path_none_raises(gateway):
    with pytest.raises(ValueError):
        gateway.load(GraphSource(kind="file", value=None, name="x"))

def test_file_path_wrong_type_raises(gateway):
    with pytest.raises(TypeError):
        gateway.load(GraphSource(kind="file", value=123, name="x"))


# format support

def test_load_weighted_edgelist(gateway, tmp_path):
    edgefile = tmp_path / "weighted.edgelist"
    edgefile.write_text("0 1 2.5\n1 2 1.0\n")
    result = gateway.load(GraphSource(kind="file", value=str(edgefile), name="w", weighted=True))
    g = result.to_networkx(copy=False)
    assert g[0][1]["weight"] == pytest.approx(2.5)
    assert g[1][2]["weight"] == pytest.approx(1.0)

def test_load_graphml_file(gateway, tmp_path):
    g = nx.path_graph(4)
    path = str(tmp_path / "graph.graphml")
    nx.write_graphml(g, path)
    result = gateway.load(GraphSource(kind="file", value=path, name="graphml_test"))
    assert result.node_count == 4
    assert result.edge_count == 3

def test_unknown_kind_raises(gateway):
    with pytest.raises(ValueError, match="unknown source kind"):
        gateway.load(GraphSource(kind="ftp", name="x"))
