"""Tests for classification/semantic.py.

The classifier loads a real embedding model, a few seconds of work, so it's
built once per test session (scope="session") and reused across every test
in this file instead of once per test function.
"""

import pytest

from router.classification.base import Classifier
from router.classification.semantic import SemanticClassifier
from router.domain.models import Category


@pytest.fixture(scope="session")
def classifier() -> SemanticClassifier:
    return SemanticClassifier()


def _accepts_classifier(classifier: Classifier) -> None:
    pass


def test_semantic_classifier_satisfies_protocol(classifier: SemanticClassifier) -> None:
    _accepts_classifier(classifier)


def test_classifies_a_clear_billing_ticket(classifier: SemanticClassifier) -> None:
    result = classifier.classify(
        "I was billed twice for the same invoice this month, can I get one charge refunded?"
    )

    assert result.category == Category.BILLING
    assert 0.0 <= result.confidence <= 1.0
    assert result.classifier_name == "semantic"


def test_classifies_a_clear_technical_ticket(classifier: SemanticClassifier) -> None:
    result = classifier.classify(
        "Every time I try to export a report the page crashes with a server error."
    )

    assert result.category == Category.TECHNICAL


def test_confidence_reflects_a_clear_margin(classifier: SemanticClassifier) -> None:
    clear = classifier.classify(
        "I need a refund, I was charged for a plan I cancelled two invoices ago."
    )
    ambiguous = classifier.classify("hmm")

    # not a guarantee for every possible input, but a clearly on-topic ticket
    # should produce a larger margin-derived confidence than three characters
    # with no real content
    assert clear.confidence > ambiguous.confidence
