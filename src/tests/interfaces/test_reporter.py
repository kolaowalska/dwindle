from __future__ import annotations

import pytest

from src.interfaces.reporter import Reporter, ScenarioRecord, _fmt, _strip_ansi


@pytest.fixture
def record():
    return ScenarioRecord(
        label="identity_stub (rho=1.0)",
        algorithm="identity_stub",
        nodes_before=10,
        edges_before=9,
        nodes_after=10,
        edges_after=9,
        metrics={"diameter": {"diameter": 9.0, "execution_time": 0.001}},
        deltas={"diameter": {"diameter_delta": 0.0}},
    )

@pytest.fixture
def reporter(record):
    r = Reporter()
    r.add(record)
    return r


# --- ScenarioRecord ---

def test_scenario_record_fields_accessible(record):
    assert record.label == "identity_stub (rho=1.0)"
    assert record.algorithm == "identity_stub"
    assert record.nodes_before == 10
    assert record.edges_before == 9
    assert record.nodes_after == 10
    assert record.edges_after == 9
    assert isinstance(record.metrics, dict)
    assert isinstance(record.deltas, dict)

def test_scenario_record_error_defaults_to_none(record):
    assert record.error is None


# --- Reporter.add ---

def test_reporter_add_stores_record(reporter, record):
    assert record in reporter.records

def test_reporter_multiple_records():
    r = Reporter()
    rec1 = ScenarioRecord(
        label="a", algorithm="identity_stub",
        nodes_before=5, edges_before=4, nodes_after=5, edges_after=4,
        metrics={}, deltas={},
    )
    rec2 = ScenarioRecord(
        label="b", algorithm="random",
        nodes_before=5, edges_before=4, nodes_after=5, edges_after=2,
        metrics={}, deltas={},
    )
    r.add(rec1)
    r.add(rec2)
    assert len(r.records) == 2


# --- Reporter.print_report ---

def test_print_report_does_not_raise(reporter, capsys):
    reporter.print_report()
    capsys.readouterr()  # no assertion needed — just must not raise

def test_print_report_includes_algorithm_abbrev(reporter, capsys):
    reporter.print_report()
    out = capsys.readouterr().out
    # identity_stub INFO.abbrev is "id"
    assert "id" in out

def test_print_report_includes_metric_name(reporter, capsys):
    reporter.print_report()
    out = capsys.readouterr().out
    # "diameter" or its abbreviation "diam" should appear
    assert "diam" in out or "diameter" in out

def test_print_report_empty_reporter(capsys):
    Reporter().print_report()
    capsys.readouterr()


# --- formatting helpers ---

def test_fmt_positive_delta_is_green():
    result = _fmt(0.5, is_delta=True)
    assert "\033[92m" in result  # _GREEN

def test_fmt_negative_delta_is_red():
    result = _fmt(-0.5, is_delta=True)
    assert "\033[91m" in result  # _RED

def test_strip_ansi_removes_codes():
    assert _strip_ansi("\033[91mred\033[0m") == "red"
    assert _strip_ansi("\033[1m\033[92mgreen\033[0m") == "green"
    assert _strip_ansi("plain") == "plain"
