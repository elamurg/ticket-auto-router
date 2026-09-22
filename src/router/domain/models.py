from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Category(StrEnum):
    BILLING = "BILLING"
    TECHNICAL = "TECHNICAL"
    ACCOUNT = "ACCOUNT"
    COMPLAINT = "COMPLAINT"
    OTHER = "OTHER"


class CustomerTier(StrEnum):
    FREE = "FREE"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


class Priority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class Ticket(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    subject: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    customer_tier: CustomerTier = CustomerTier.FREE

    @model_validator(mode="before")
    @classmethod
    def strip_whitespace(cls, values: dict[str, Any]) -> dict[str, Any]:
        if isinstance(values, dict):
            for field in ("subject", "body"):
                if isinstance(values.get(field), str):
                    values[field] = values[field].strip()
        return values

    model_config = ConfigDict(frozen=True)


class Classification(BaseModel):
    category: Category
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., min_length=1)
    classifier_name: str = Field(..., min_length=1)
    model_config = ConfigDict(frozen=True)


class RoutingDecision(BaseModel):
    ticket_id: UUID
    category: Category
    queue: str = Field(..., min_length=1)
    priority: Priority
    requires_human: bool
    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    classification_confidence: float | None = Field(ge=0.0, le=1.0, default=None)
    model_config = ConfigDict(frozen=True)
