"""Testing for rules.py:
- plain default path
- checking premium escalation
- checking confidence threshold maps to human review (above and below)
- what happens if confidence is exactly at threshold
- checking triage queue
- edge case: an enterprise customer's complaint with low confidence,
which branch wins, escelation or human review?
"""

from router.domain.models import Category, Classification, CustomerTier, Priority, Ticket
from router.domain.rules import (
    CONFIDENCE_THRESHOLD,
    PRIORITY_NORMAL,
    QUEUE_DEFAULT,
    QUEUE_HUMAN_REVIEW,
    QUEUE_PREMIUM_ESCALATIONS,
    QUEUE_TRIAGE,
    decide_route,
)


def test_default_path() -> None:
    ticket = Ticket(
        subject="Standard problem",
        body="...",
        customer_tier=CustomerTier.FREE,
    )
    classification = Classification(
        category=Category.ACCOUNT,
        confidence=0.8,
        reasoning="...",
        classifier_name="keyword",
    )
    decision = decide_route(classification, ticket)

    assert decision.queue == QUEUE_DEFAULT
    assert decision.requires_human is False


def test_enterprise_complaint_escelates() -> None:
    ticket = Ticket(
        subject="Billing issue",
        body="...",
        customer_tier=CustomerTier.ENTERPRISE,
    )
    classification = Classification(
        category=Category.COMPLAINT,
        confidence=0.9,
        reasoning="clearly a complaint",
        classifier_name="keyword",
    )

    decision = decide_route(classification, ticket)

    assert decision.queue == QUEUE_PREMIUM_ESCALATIONS
    assert decision.priority == Priority.HIGH
    assert decision.requires_human is True


def test_mapping_to_human_review_below_threshold() -> None:
    classification = Classification(
        category=Category.BILLING,
        confidence=CONFIDENCE_THRESHOLD - 0.1,
        reasoning="...",
        classifier_name="keyword",
    )
    ticket = Ticket(subject="...", body="...")

    decision = decide_route(classification, ticket)

    assert decision.queue == QUEUE_HUMAN_REVIEW
    assert decision.priority == Priority.HIGH
    assert decision.requires_human is True


def test_mapping_to_human_review_above_threshold() -> None:
    classification = Classification(
        category=Category.BILLING,
        confidence=CONFIDENCE_THRESHOLD + 0.1,
        reasoning="...",
        classifier_name="keyword",
    )
    ticket = Ticket(subject="...", body="...")

    decision = decide_route(classification, ticket)

    assert decision.queue == QUEUE_DEFAULT
    assert decision.priority == PRIORITY_NORMAL
    assert decision.requires_human is False


def test_mapping_to_human_review_equals_threshold() -> None:
    classification = Classification(
        category=Category.BILLING,
        confidence=CONFIDENCE_THRESHOLD,
        reasoning="...",
        classifier_name="keyword",
    )
    ticket = Ticket(subject="...", body="...")

    decision = decide_route(classification, ticket)

    assert decision.queue == QUEUE_HUMAN_REVIEW
    assert decision.priority == Priority.HIGH
    assert decision.requires_human is True


def test_triage_queue_adoptation() -> None:
    ticket = Ticket(
        subject="Standard problem",
        body="...",
        customer_tier=CustomerTier.FREE,
    )
    classification = Classification(
        category=Category.OTHER,
        confidence=0.8,
        reasoning="...",
        classifier_name="keyword",
    )
    decision = decide_route(classification, ticket)

    assert decision.queue == QUEUE_TRIAGE
    assert decision.category == Category.OTHER
    assert decision.priority == PRIORITY_NORMAL
    assert decision.requires_human is False


def test_unique_edge_case() -> None:
    ticket = Ticket(
        subject="Billing issue",
        body="...",
        customer_tier=CustomerTier.ENTERPRISE,
    )
    classification = Classification(
        category=Category.COMPLAINT,
        confidence=CONFIDENCE_THRESHOLD - 0.1,
        reasoning="clearly a complaint",
        classifier_name="keyword",
    )

    decision = decide_route(classification, ticket)

    assert decision.queue == QUEUE_PREMIUM_ESCALATIONS
    assert decision.priority == Priority.HIGH
    assert decision.requires_human is True
