"""Implementation of routing rules such as:

- complaints from premium customers escelate
- confidence under a threshold sets requires_huma
- unknown category goes to triage

The file is done when it is fully unit tested with parametrised cases including every boundary
and the function has zero I/O.
"""

from typing import Final  # confirms this name is never reassigned anywhere in the file

from router.domain.models import (
    Category,
    Classification,
    CustomerTier,
    Priority,
    RoutingDecision,
    Ticket,
)

QUEUE_DEFAULT: Final = "default"
QUEUE_PREMIUM_ESCALATIONS: Final = "premium_escalations"
QUEUE_HUMAN_REVIEW: Final = "human_review"
QUEUE_TRIAGE: Final = "triage"

PRIORITY_NORMAL: Final = Priority.MEDIUM

CONFIDENCE_THRESHOLD: Final = 0.5


def decide_route(classification: Classification, ticket: Ticket) -> RoutingDecision:
    category = classification.category
    customer_tier = ticket.customer_tier
    confidence = classification.confidence

    queue = QUEUE_DEFAULT
    priority = PRIORITY_NORMAL
    requires_human = False
    if customer_tier == CustomerTier.ENTERPRISE and category == Category.COMPLAINT:
        queue = QUEUE_PREMIUM_ESCALATIONS
        priority = Priority.HIGH
        requires_human = True
    elif confidence <= CONFIDENCE_THRESHOLD:
        queue = QUEUE_HUMAN_REVIEW
        priority = Priority.HIGH
        requires_human = True
    elif category == Category.OTHER:
        queue = QUEUE_TRIAGE
        priority = PRIORITY_NORMAL
        requires_human = False

    return RoutingDecision(
        ticket_id=ticket.id,
        category=category,
        queue=queue,
        priority=priority,
        requires_human=requires_human,
    )
