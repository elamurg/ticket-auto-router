"""Implementing metrics: accuracy, confusion matrix, precision and recall
per category and mean confidence from scratch

Example:

#	True	Predicted	Confidence
1	BILLING	BILLING	0.90
2	BILLING	TECHNICAL	0.60
3	TECHNICAL	TECHNICAL	0.80
4	TECHNICAL	TECHNICAL	0.95
5	COMPLAINT	COMPLAINT	0.70
6	COMPLAINT	BILLING	0.40
"""

from dataclasses import dataclass

from router.domain.models import Category


@dataclass(frozen=True)
class ClassMetrics:
    precision: float
    recall: float


@dataclass(frozen=True)
class ConfidenceByCorrectness:
    mean_confidence_correct: float
    mean_confidence_incorrect: float


def accuracy(y_true: list[Category], y_pred: list[Category]) -> float:
    """Fraction of predictions that exactly matched the true category."""
    corr_cnt = sum(
        1 for true_cat, pred_cat in zip(y_true, y_pred, strict=True) if true_cat == pred_cat
    )
    return corr_cnt / len(y_true)


def confusion_matrix(
    y_true: list[Category], y_pred: list[Category]
) -> dict[Category, dict[Category, int]]:
    """Matrix[true_category][predicted_category] -> count of tickets."""
    matrix: dict[Category, dict[Category, int]] = {
        true_cat: {pred_cat: 0 for pred_cat in Category} for true_cat in Category
    }
    for true_cat, pred_cat in zip(y_true, y_pred, strict=True):
        matrix[true_cat][pred_cat] += 1
    return matrix


def precision_recall_per_class(
    y_true: list[Category], y_pred: list[Category]
) -> dict[Category, ClassMetrics]:
    """One ClassMetrics per category, derived from the confusion metrix."""
    matrix = confusion_matrix(y_true, y_pred)
    result = {}
    for cat in Category:
        true_positive = matrix[cat][cat]
        row_total = sum(matrix[cat].values())
        column_total = sum(matrix[other_cat][cat] for other_cat in Category)

        precision = true_positive / column_total if column_total else 0
        recall = true_positive / row_total if row_total else 0
        result[cat] = ClassMetrics(precision=precision, recall=recall)
    return result


def mean_confidence_by_correctness(
    y_true: list[Category],
    y_pred: list[Category],
    confidences: list[float],
) -> ConfidenceByCorrectness:
    """Average confidence, split by whether the prediction was correct."""
    correct_confidences = [
        con
        for true_cat, pred_cat, con in zip(y_true, y_pred, confidences, strict=True)
        if true_cat == pred_cat
    ]
    incorrect_confidences = [
        con
        for true_cat, pred_cat, con in zip(y_true, y_pred, confidences, strict=True)
        if true_cat != pred_cat
    ]

    mean_correct = sum(correct_confidences) / len(correct_confidences) if correct_confidences else 0

    mean_incorrect = (
        sum(incorrect_confidences) / len(incorrect_confidences) if incorrect_confidences else 0
    )
    return ConfidenceByCorrectness(
        mean_confidence_correct=mean_correct,
        mean_confidence_incorrect=mean_incorrect,
    )
