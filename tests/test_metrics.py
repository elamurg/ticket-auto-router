"""Tests for evaluation/metrics.py.

Hand-worked aritmetic."""

import pytest

from router.domain.models import Category
from router.evaluation.metrics import (
    accuracy,
    confusion_matrix,
    mean_confidence_by_correctness,
    precision_recall_per_class,
)

BILLING = Category.BILLING
TECHNICAL = Category.TECHNICAL
COMPLAINT = Category.COMPLAINT

Y_TRUE = [BILLING, BILLING, TECHNICAL, TECHNICAL, COMPLAINT, COMPLAINT]
Y_PRED = [BILLING, TECHNICAL, TECHNICAL, TECHNICAL, COMPLAINT, BILLING]
CONFIDENCES = [0.90, 0.60, 0.80, 0.95, 0.70, 0.40]


def test_accuracy() -> None:
    assert accuracy(Y_TRUE, Y_PRED) == pytest.approx(4 / 6)


def test_confusion_matrix() -> None:
    matrix = confusion_matrix(Y_TRUE, Y_PRED)
    assert matrix[BILLING][BILLING] == 1
    assert matrix[BILLING][TECHNICAL] == 1
    assert matrix[BILLING][COMPLAINT] == 0
    assert matrix[TECHNICAL][BILLING] == 0
    assert matrix[TECHNICAL][TECHNICAL] == 2
    assert matrix[TECHNICAL][COMPLAINT] == 0
    assert matrix[COMPLAINT][BILLING] == 1
    assert matrix[COMPLAINT][TECHNICAL] == 0
    assert matrix[COMPLAINT][COMPLAINT] == 1


def test_precision_recall_per_class() -> None:
    result = precision_recall_per_class(Y_TRUE, Y_PRED)

    assert result[BILLING].precision == pytest.approx(1 / 2)
    assert result[BILLING].recall == pytest.approx(1 / 2)
    assert result[TECHNICAL].precision == pytest.approx(2 / 3)
    assert result[TECHNICAL].recall == pytest.approx(2 / 2)
    assert result[COMPLAINT].precision == pytest.approx(1 / 1)
    assert result[COMPLAINT].recall == pytest.approx(1 / 2)


def test_mean_confidence_by_correctness() -> None:
    result = mean_confidence_by_correctness(Y_TRUE, Y_PRED, CONFIDENCES)

    assert result.mean_confidence_correct == pytest.approx((0.9 + 0.8 + 0.95 + 0.7) / 4)
    assert result.mean_confidence_incorrect == pytest.approx((0.6 + 0.4) / 2)
