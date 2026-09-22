from datetime import datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from router.domain.models import (
    Category,
    Classification,
    CustomerTier,
    Priority,
    RoutingDecision,
    Ticket,
)


def test_strenum_val() -> None:
    """Checking for clear serialisation with StrEnum"""
    assert Category.BILLING == "BILLING"
    assert Priority.LOW == "LOW"
    assert CustomerTier.PRO == "PRO"


class TestTicketModel:
    def test_valid_ticket_creation(self) -> None:
        ticket = Ticket(
            subject="Cannot access dashboard.",
            body="I got error message 500 on screen.",
        )

        assert isinstance(ticket.id, UUID)
        assert isinstance(ticket.created_at, datetime)
        assert ticket.customer_tier == CustomerTier.FREE

    def test_white_space_stripping(self) -> None:
        ticket = Ticket(
            subject="  Bug in checkout.  ",
            body="\nPayment fails on step 2.\n",
        )

        assert ticket.subject == "Bug in checkout."
        assert ticket.body == "Payment fails on step 2."

    def test_white_space_stripping_fails(self) -> None:
        with pytest.raises(ValidationError):
            Ticket(subject=" ", body="Valid body text.")

    def test_ticket_immutability(self) -> None:
        """Verification that frozen config works."""
        ticket = Ticket(subject="Help.", body="Need assistance.")
        with pytest.raises(ValidationError):
            ticket.subject = "New subject"


class TestClassificationModel:
    def test_confidence_bound_validation(self) -> None:
        classification = Classification(
            category=Category.TECHNICAL,
            confidence=0.95,
            reasoning="Contains keywords 'error' and '500'",
            classifier_name="llm_v2",
        )
        assert classification.confidence == 0.95
        assert classification.category == Category.TECHNICAL

    @pytest.mark.parametrize("invalid_confidence", [-0.1, 1.05, 2.0])
    def test_invalid_confidence(self, invalid_confidence: float) -> None:
        """Validate the confidence score is between 0.0 and 1.0"""
        with pytest.raises(ValidationError):
            Classification(
                category=Category.TECHNICAL,
                confidence=invalid_confidence,
                reasoning="Invalid test score",
                classifier_name="test",
            )

    def test_classification_immutability(self) -> None:
        classification = Classification(
            category=Category.TECHNICAL,
            confidence=0.8,
            reasoning="Invoice issue.",
            classifier_name="new_rule",
        )
        with pytest.raises(ValidationError):
            classification.confidence = 0.9


class TestRoutingDecision:
    def test_valid_routing_decision(self) -> None:
        ticket_id = uuid4()
        decision = RoutingDecision(
            ticket_id=ticket_id,
            category=Category.BILLING,
            queue="billing_queue",
            priority=Priority.LOW,
            requires_human=True,
            classification_confidence=0.6,
        )

        assert decision.ticket_id == ticket_id
        assert decision.queue == "billing_queue"
        assert isinstance(decision.decided_at, datetime)

    def test_routing_decision_confidence_defaults_to_none(self) -> None:
        decision = RoutingDecision(
            ticket_id=uuid4(),
            category=Category.BILLING,
            queue="billing_queue",
            priority=Priority.LOW,
            requires_human=True,
        )

        assert decision.classification_confidence is None

    def test_empty_queue(self) -> None:
        """Verify min_length=1 on queue name."""
        with pytest.raises(ValidationError):
            RoutingDecision(
                ticket_id=uuid4(),
                category=Category.OTHER,
                queue="",
                priority=Priority.LOW,
                requires_human=False,
            )
