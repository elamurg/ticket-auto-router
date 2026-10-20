"""Tests for evaluation/dataset.py."""

import json
from pathlib import Path

from router.domain.models import Category
from router.evaluation.dataset import load_golden_set


def _write_golden_file(tmp_path: Path, rows: list[dict[str, str]]) -> Path:
    path = tmp_path / "golden.jsonl"
    with path.open("w", encoding="utf-8") as golden_file:
        for row in rows:
            golden_file.write(json.dumps(row) + "\n")
    return path


def test_load_golden_set_combines_subject_and_body(tmp_path: Path) -> None:
    path = _write_golden_file(
        tmp_path,
        [
            {
                "id": "t001",
                "subject": "Charged twice",
                "body": "Please refund one charge.",
                "category": "BILLING",
                "tier": "clear",
                "note": "duplicate charge",
            }
        ],
    )

    examples = load_golden_set(path)

    assert len(examples) == 1
    assert examples[0].id == "t001"
    assert examples[0].category == Category.BILLING
    assert "Charged twice" in examples[0].text
    assert "Please refund one charge." in examples[0].text


def test_load_golden_set_skips_blank_lines(tmp_path: Path) -> None:
    path = tmp_path / "golden.jsonl"
    row = json.dumps(
        {
            "id": "t001",
            "subject": "s",
            "body": "b",
            "category": "OTHER",
            "tier": "clear",
            "note": "n",
        }
    )
    path.write_text(f"{row}\n\n{row}\n")

    examples = load_golden_set(path)

    assert len(examples) == 2


def test_load_golden_set_preserves_order(tmp_path: Path) -> None:
    path = _write_golden_file(
        tmp_path,
        [
            {
                "id": "t001",
                "subject": "first",
                "body": "b",
                "category": "BILLING",
                "tier": "clear",
                "note": "n",
            },
            {
                "id": "t002",
                "subject": "second",
                "body": "b",
                "category": "TECHNICAL",
                "tier": "clear",
                "note": "n",
            },
        ],
    )

    examples = load_golden_set(path)

    assert [example.id for example in examples] == ["t001", "t002"]
