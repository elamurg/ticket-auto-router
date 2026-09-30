"""Defining the Classifier Protocol with one method.
Anything that wants to count as a Classifier,
must have a method named classify.
"""

from typing import Protocol

from router.domain.models import Classification


class Classifier(Protocol):
    def classify(self, text: str) -> Classification: ...
