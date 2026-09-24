from __future__ import annotations

import json
import pytest

from src.main import main
from src.interfaces.cli import _parse_params, _CSV_FIELDNAMES


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


# --- persistence & history ---

def _corpus(tmp_path):
    d = tmp_path / "corpus"
    d.mkdir()
    (d / "a.edgelist").write_text("0 1\n1 2\n2 3\n3 0\n")
    (d / "b.edgelist").write_text("0 1\n1 2\n2 0\n")
    return d

def test_run_records_the_run_to_the_store(tmp_path):
    from src.infrastructure.persistence.json_store import JsonExperimentRepository
    store = tmp_path / "store"
    g = tmp_path / "g.edgelist"
    g.write_text("0 1\n1 2\n2 3\n")
    main(["run", "--graph", str(g), "--algorithm", "identity_stub",
          "--metrics", "edge_density", "--store", str(store)])
    assert len(JsonExperimentRepository(store).list_all()) == 1

def test_no_store_writes_nothing(tmp_path):
    store = tmp_path / "store"
    g = tmp_path / "g.edgelist"
    g.write_text("0 1\n1 2\n2 3\n")
    main(["run", "--graph", str(g), "--algorithm", "identity_stub",
          "--store", str(store), "--no-store"])
    assert not store.exists()

def test_batch_records_one_run_per_graph(tmp_path):
    from src.infrastructure.persistence.json_store import JsonExperimentRepository
    store = tmp_path / "store"
    main(["batch", "--dir", str(_corpus(tmp_path)), "--algorithm", "identity_stub",
          "--store", str(store), "--output", str(tmp_path / "o.csv")])
    assert len(JsonExperimentRepository(store).list_all()) == 2

def test_successive_batches_accumulate(tmp_path):
    from src.infrastructure.persistence.json_store import JsonExperimentRepository
    store, corpus = tmp_path / "store", _corpus(tmp_path)
    for algo in ("identity_stub", "random"):
        main(["batch", "--dir", str(corpus), "--algorithm", algo,
              "--store", str(store), "--output", str(tmp_path / f"{algo}.csv")])
    runs = JsonExperimentRepository(store).list_all()
    assert len(runs) == 4
    assert {r.algorithm for r in runs} == {"identity_stub", "random"}

def test_stored_run_carries_transform_timing(tmp_path):
    from src.infrastructure.persistence.json_store import JsonExperimentRepository
    store = tmp_path / "store"
    main(["batch", "--dir", str(_corpus(tmp_path)), "--algorithm", "identity_stub",
          "--store", str(store), "--output", str(tmp_path / "o.csv")])
    assert all(r.transform_seconds is not None for r in JsonExperimentRepository(store).list_all())

def test_history_lists_recorded_runs(tmp_path, capsys):
    store = tmp_path / "store"
    main(["batch", "--dir", str(_corpus(tmp_path)), "--algorithm", "identity_stub",
          "--store", str(store), "--output", str(tmp_path / "o.csv")])
    capsys.readouterr()
    assert main(["history", "--store", str(store)]) == 0
    out = capsys.readouterr().out
    assert "identity_stub" in out
    assert "2 run(s)" in out

def test_history_on_empty_store_is_not_an_error(tmp_path, capsys):
    assert main(["history", "--store", str(tmp_path / "empty")]) == 0
    assert "no runs recorded" in capsys.readouterr().out

def test_history_exports_every_run_to_one_csv(tmp_path):
    store = tmp_path / "store"
    main(["batch", "--dir", str(_corpus(tmp_path)), "--algorithm", "identity_stub",
          "--metrics", "edge_density", "--store", str(store), "--output", str(tmp_path / "o.csv")])
    export = tmp_path / "all.csv"
    main(["history", "--store", str(store), "--output", str(export)])
    body = export.read_text().splitlines()
    assert body[0] == ",".join(_CSV_FIELDNAMES)
    assert len(body) > 1

def test_batch_and_history_csv_share_a_header(tmp_path):
    store = tmp_path / "store"
    batch_csv, export = tmp_path / "b.csv", tmp_path / "h.csv"
    main(["batch", "--dir", str(_corpus(tmp_path)), "--algorithm", "identity_stub",
          "--metrics", "edge_density", "--store", str(store), "--output", str(batch_csv)])
    main(["history", "--store", str(store), "--output", str(export)])
    assert _header(batch_csv) == _header(export)
