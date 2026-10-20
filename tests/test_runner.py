"""Tests for evaluation/runner.py.

The semantic classifier is deliberately not exercised here: loading its
embedding model takes a few seconds, which would slow down the whole test
suite for every run. These tests use only the keyword classifier (fast,
no model to load) to check the runner's own wiring, argument parsing,
report assembly, JSON serialisation, writing a results file. Scoring the
semantic classifier for real happens by actually running the CLI, same as
the ticket's own "done when" asks for, not inside pytest.
"""

import json
from pathlib import Path

import pytest

from router.domain.models import Category
from router.evaluation.runner import build_report, parse_args, run_evaluation


def test_parse_args_accepts_a_known_classifier() -> None:
    args = parse_args(["--classifier", "keyword"])
    assert args.classifier == "keyword"


def test_parse_args_rejects_an_unknown_classifier() -> None:
    with pytest.raises(SystemExit):
        parse_args(["--classifier", "not-a-real-classifier"])


def test_build_report_matches_hand_worked_example() -> None:
    # same six-row example as test_metrics.py, so these expected values are
    # already independently hand-verified there, not invented fresh here
    billing, technical, complaint = Category.BILLING, Category.TECHNICAL, Category.COMPLAINT
    y_true = [billing, billing, technical, technical, complaint, complaint]
    y_pred = [billing, technical, technical, technical, complaint, billing]
    confidences = [0.90, 0.60, 0.80, 0.95, 0.70, 0.40]

    report = build_report("test-classifier", y_true, y_pred, confidences)

    assert report["classifier"] == "test-classifier"
    assert report["num_tickets"] == 6
    assert report["accuracy"] == pytest.approx(4 / 6)
    assert report["confusion_matrix"]["BILLING"]["BILLING"] == 1
    assert report["confusion_matrix"]["COMPLAINT"]["BILLING"] == 1
    assert report["precision_recall_per_class"]["BILLING"]["precision"] == pytest.approx(1 / 2)
    assert report["confidence_by_correctness"]["mean_confidence_correct"] == pytest.approx(0.8375)


def test_run_evaluation_writes_a_results_file(tmp_path: Path) -> None:
    golden_path = tmp_path / "golden.jsonl"
    rows = [
        {
            "id": "t001",
            "subject": "Charged twice",
            "body": "Please refund the extra invoice charge.",
            "category": "BILLING",
            "tier": "clear",
            "note": "n",
        },
        {
            "id": "t002",
            "subject": "App keeps crashing",
            "body": "Getting a 500 error every time.",
            "category": "TECHNICAL",
            "tier": "clear",
            "note": "n",
        },
    ]
    golden_path.write_text("\n".join(json.dumps(row) for row in rows))
    results_dir = tmp_path / "results"

    report = run_evaluation("keyword", golden_set_path=golden_path, results_dir=results_dir)

    assert report["num_tickets"] == 2
    written_files = list(results_dir.glob("keyword-*.json"))
    assert len(written_files) == 1
    on_disk = json.loads(written_files[0].read_text())
    assert on_disk["classifier"] == "keyword"
    assert on_disk["num_tickets"] == 2
