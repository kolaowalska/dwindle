from __future__ import annotations

import json
import pytest

from src.main import main
from src.interfaces.cli import _parse_params


# --- smoke / help ---

def test_list_algorithms_exits_zero():
    assert main(["list-algorithms"]) == 0

def test_list_metrics_exits_zero():
    assert main(["list-metrics"]) == 0

def test_smoke_command_exits_zero():
    assert main(["smoke"]) == 0


# --- cmd_run ---

def test_run_with_memory_graph_succeeds(tmp_path):
    edgefile = tmp_path / "graph.edgelist"
    edgefile.write_text("0 1\n1 2\n2 3\n")
    ret = main(["run", "--graph", str(edgefile), "--algorithm", "identity_stub"])
    assert ret == 0

def test_run_missing_file_exits_nonzero():
    ret = main(["run", "--graph", "/no/such/file.edgelist", "--algorithm", "identity_stub"])
    assert ret != 0

def test_run_unknown_algorithm_exits_nonzero(tmp_path):
    edgefile = tmp_path / "graph.edgelist"
    edgefile.write_text("0 1\n1 2\n")
    ret = main(["run", "--graph", str(edgefile), "--algorithm", "not_real_algo_xyzzy"])
    assert ret != 0


# --- cmd_batch ---

def test_batch_on_directory_succeeds(tmp_path):
    (tmp_path / "a.edgelist").write_text("0 1\n1 2\n")
    (tmp_path / "b.edgelist").write_text("0 1\n1 2\n2 3\n")
    output = tmp_path / "out.csv"
    ret = main(["batch", "--dir", str(tmp_path), "--algorithm", "identity_stub",
                "--output", str(output)])
    assert ret == 0
    assert output.exists()

def test_batch_missing_directory_exits_nonzero(tmp_path):
    ret = main(["batch", "--dir", "/no/such/directory_xyzzy",
                "--algorithm", "identity_stub",
                "--output", str(tmp_path / "out.csv")])
    assert ret != 0


# --- param parsing ---

def test_parse_params_key_value():
    # values are coerced: float for decimals, int for integers
    result = _parse_params(["rho=0.5", "seed=42"])
    assert result["rho"] == pytest.approx(0.5)
    assert result["seed"] == 42

def test_parse_params_json():
    result = _parse_params(['{"rho": 0.5}'])
    assert result == {"rho": 0.5}


# --- output formats ---

def test_run_json_output_is_valid_json(tmp_path):
    edgefile = tmp_path / "graph.edgelist"
    edgefile.write_text("0 1\n1 2\n2 3\n")
    output = tmp_path / "results.json"
    ret = main(["run", "--graph", str(edgefile), "--algorithm", "identity_stub",
                "--output", str(output)])
    assert ret == 0
    with open(output) as f:
        data = json.load(f)
    assert isinstance(data, dict)
    assert "graph_name" in data

def test_run_csv_output_has_header(tmp_path):
    edgefile = tmp_path / "graph.edgelist"
    edgefile.write_text("0 1\n1 2\n2 3\n")
    output = tmp_path / "results.csv"
    ret = main(["run", "--graph", str(edgefile), "--algorithm", "identity_stub",
                "--metrics", "diameter", "--output", str(output)])
    assert ret == 0
    with open(output) as f:
        header = f.readline()
    assert "metric" in header or "graph" in header


# --- csv schema parity ---

def _header(path):
    return path.read_text().splitlines()[0]

def test_run_and_batch_csv_share_a_header(tmp_path):
    edgefile = tmp_path / "g.edgelist"
    edgefile.write_text("0 1\n1 2\n2 3\n")
    run_csv = tmp_path / "run.csv"
    batch_csv = tmp_path / "batch.csv"

    main(["run", "--graph", str(edgefile), "--algorithm", "identity_stub",
          "--metrics", "edge_density", "--output", str(run_csv)])
    main(["batch", "--dir", str(tmp_path), "--algorithm", "identity_stub",
          "--metrics", "edge_density", "--output", str(batch_csv)])

    assert _header(run_csv) == _header(batch_csv)

def test_run_csv_carries_topology_columns(tmp_path):
    edgefile = tmp_path / "g.edgelist"
    edgefile.write_text("0 1\n1 2\n2 3\n")
    out = tmp_path / "run.csv"
    main(["run", "--graph", str(edgefile), "--algorithm", "identity_stub",
          "--metrics", "edge_density", "--output", str(out)])
    assert "nodes_before" in _header(out)


# --- logging ---

def test_verbose_flag_lowers_log_level(tmp_path):
    import logging
    edgefile = tmp_path / "g.edgelist"
    edgefile.write_text("0 1\n1 2\n")
    try:
        main(["-v", "run", "--graph", str(edgefile), "--algorithm", "identity_stub"])
        assert logging.getLogger().level == logging.INFO
        main(["-vv", "run", "--graph", str(edgefile), "--algorithm", "identity_stub"])
        assert logging.getLogger().level == logging.DEBUG
    finally:
        logging.getLogger().setLevel(logging.WARNING)

def test_default_verbosity_is_quiet(tmp_path):
    import logging
    edgefile = tmp_path / "g.edgelist"
    edgefile.write_text("0 1\n1 2\n")
    try:
        main(["run", "--graph", str(edgefile), "--algorithm", "identity_stub"])
        assert logging.getLogger().level == logging.WARNING
    finally:
        logging.getLogger().setLevel(logging.WARNING)


# --- before/after output ---

def test_run_prints_before_and_after(tmp_path, capsys):
    import re
    edgefile = tmp_path / "g.edgelist"
    edgefile.write_text("0 1\n1 2\n2 3\n3 4\n4 0\n")
    main(["run", "--graph", str(edgefile), "--algorithm", "random",
          "--params", "p=0.5", "seed=1", "--metrics", "edge_density"])
    out = capsys.readouterr().out
    assert re.search(r"density\s+\S+ → \S+ \([-+]\S+\)", out)

def test_run_csv_carries_delta_keys(tmp_path):
    edgefile = tmp_path / "g.edgelist"
    edgefile.write_text("0 1\n1 2\n2 3\n3 4\n4 0\n")
    out = tmp_path / "r.csv"
    main(["run", "--graph", str(edgefile), "--algorithm", "random",
          "--params", "p=0.5", "seed=1", "--metrics", "edge_density", "--output", str(out)])
    body = out.read_text()
    assert "density_original" in body
    assert "density_reduced" in body
    assert "density_delta" in body

def test_relative_metric_is_accepted(tmp_path):
    edgefile = tmp_path / "g.edgelist"
    edgefile.write_text("0 1\n1 2\n2 3\n3 4\n4 0\n")
    assert main(["run", "--graph", str(edgefile), "--algorithm", "identity_stub",
                 "--metrics", "spectral_similarity"]) == 0
