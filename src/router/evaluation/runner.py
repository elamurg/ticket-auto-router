"""CLI entry point: score a classifier against the golden set.

    python -m router.evaluation.runner --classifier keyword

Prints a report to the terminal and writes the same data as JSON to
results/<classifier>-<timestamp>.json.
"""

import argparse
import json
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from router.classification.base import Classifier
from router.classification.keyword import KeywordClassifier
from router.classification.semantic import SemanticClassifier
from router.domain.models import Category
from router.evaluation.dataset import GOLDEN_SET_PATH, load_golden_set
from router.evaluation.metrics import (
    accuracy,
    confusion_matrix,
    mean_confidence_by_correctness,
    precision_recall_per_class,
)

# Factories, not instances: building a SemanticClassifier loads an embedding
# model from disk, several seconds of work that should only happen for the
# classifier actually requested, not for every entry in this registry every
# time the module is imported.
CLASSIFIER_FACTORIES: Final[dict[str, Callable[[], Classifier]]] = {
    "keyword": KeywordClassifier,
    "semantic": SemanticClassifier,
}

RESULTS_DIR: Final[Path] = Path(__file__).resolve().parents[3] / "results"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a classifier against the golden set.")
    parser.add_argument(
        "--classifier",
        required=True,
        choices=sorted(CLASSIFIER_FACTORIES),
        help="Which classifier to evaluate.",
    )
    return parser.parse_args(argv)


def build_report(
    classifier_name: str,
    y_true: list[Category],
    y_pred: list[Category],
    confidences: list[float],
) -> dict[str, Any]:
    """Run every metrics.py function and assemble one JSON-serialisable report.

    Category enum members become their plain string .value here, since JSON
    object keys must be strings, and dataclass results go through
    dataclasses.asdict, since json.dumps cannot serialise a dataclass
    instance directly.
    """
    matrix = confusion_matrix(y_true, y_pred)
    precision_recall = precision_recall_per_class(y_true, y_pred)

    return {
        "classifier": classifier_name,
        "num_tickets": len(y_true),
        "accuracy": accuracy(y_true, y_pred),
        "confusion_matrix": {
            true_cat.value: {pred_cat.value: count for pred_cat, count in row.items()}
            for true_cat, row in matrix.items()
        },
        "precision_recall_per_class": {
            category.value: asdict(class_metrics)
            for category, class_metrics in precision_recall.items()
        },
        "confidence_by_correctness": asdict(
            mean_confidence_by_correctness(y_true, y_pred, confidences)
        ),
    }


def print_report(report: dict[str, Any]) -> None:
    print(f"Classifier: {report['classifier']}")
    print(f"Tickets scored: {report['num_tickets']}")
    print(f"Accuracy: {report['accuracy']:.1%}")

    print("\nConfusion matrix (rows = true, columns = predicted):")
    categories = sorted(report["confusion_matrix"])
    header = "".ljust(12) + "".join(cat.ljust(12) for cat in categories)
    print(header)
    for true_cat in categories:
        row = report["confusion_matrix"][true_cat]
        print(true_cat.ljust(12) + "".join(str(row[pred_cat]).ljust(12) for pred_cat in categories))

    print("\nPer-category precision / recall:")
    for category, metrics in sorted(report["precision_recall_per_class"].items()):
        print(
            f"  {category:10s} precision={metrics['precision']:.2f}  recall={metrics['recall']:.2f}"
        )

    confidence = report["confidence_by_correctness"]
    print("\nMean confidence:")
    print(f"  correct predictions:   {confidence['mean_confidence_correct']:.2f}")
    print(f"  incorrect predictions: {confidence['mean_confidence_incorrect']:.2f}")


def run_evaluation(
    classifier_name: str,
    golden_set_path: Path = GOLDEN_SET_PATH,
    results_dir: Path = RESULTS_DIR,
) -> dict[str, Any]:
    """Build the classifier, score it against the golden set, write the JSON
    report to disk, and return the report (so tests can check it without
    re-parsing the file the function just wrote).
    """
    classifier = CLASSIFIER_FACTORIES[classifier_name]()
    golden_set = load_golden_set(golden_set_path)

    y_true: list[Category] = []
    y_pred: list[Category] = []
    confidences: list[float] = []
    for example in golden_set:
        result = classifier.classify(example.text)
        y_true.append(example.category)
        y_pred.append(result.category)
        confidences.append(result.confidence)

    report = build_report(classifier_name, y_true, y_pred, confidences)

    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = results_dir / f"{classifier_name}-{timestamp}.json"
    out_path.write_text(json.dumps(report, indent=2))
    report["_written_to"] = str(out_path)

    return report


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    report = run_evaluation(args.classifier)
    print_report(report)
    print(f"\nWrote {report['_written_to']}")


if __name__ == "__main__":
    main()
