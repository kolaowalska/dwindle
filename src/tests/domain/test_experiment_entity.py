from __future__ import annotations

import pytest

from src.domain.experiment import Experiment, ExperimentStatus
from src.domain.metrics.base import MetricResult


def test_initial_status_is_pending():
    exp = Experiment()
    assert exp.status == ExperimentStatus.PENDING

def test_start_sets_running():
    exp = Experiment()
    exp.start()
    assert exp.status == ExperimentStatus.RUNNING

def test_finish_sets_completed():
    exp = Experiment()
    exp.start()
    exp.finish()
    assert exp.status == ExperimentStatus.COMPLETED
    assert exp.completed_at is not None

def test_failed_records_message():
    exp = Experiment()
    exp.failed("something went wrong :(")
    assert exp.status == ExperimentStatus.FAILED
    assert "something went wrong :(" in exp.errors

def test_duration_none_before_finish():
    exp = Experiment()
    exp.start()
    assert exp.duration is None

def test_duration_positive_after_finish():
    exp = Experiment()
    exp.start()
    exp.finish()
    assert exp.duration is not None
    assert exp.duration >= 0

def test_add_result_stores_by_name():
    exp = Experiment()
    result = MetricResult(metric="diameter", summary={"diameter": 5})
    exp.add_result("diameter", result)
    assert "diameter" in exp.results
    assert exp.results["diameter"].summary["diameter"] == 5

def test_two_experiments_have_different_run_ids():
    assert Experiment().run_id != Experiment().run_id
