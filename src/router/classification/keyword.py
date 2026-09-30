"""Keyword baseline classifier, a fixed keyword map per category.

- a keyword map for all the categories implemented in models.py,
- if the best score matches to 3 keywords is gets classified with highest confidence,
- if best score is 0 then the ticket belongs to category other,
"""

from typing import Final

from router.domain.models import Category, Classification

KEYWORD_MAP: Final[dict[Category, list[str]]] = {
    Category.BILLING: [
        "invoice",
        "charge",
        "refund",
        "payment",
        "billing",
        "subscription",
        "price",
    ],
    Category.TECHNICAL: ["error", "bug", "crash", "not working", "install", "500"],
    Category.ACCOUNT: ["password", "profile", "account", "locked out", "access"],
    Category.COMPLAINT: [
        "dissapointed",
        "angry",
        "terrible",
        "worst",
        "unacceptable",
        "frustrated",
    ],
}

MAX_SCORE_FOR_FULL_CONFIDENCE: Final = 3
# best score reaching these many word hits maps to full confidence

FALLBACK_CONFIDENCE: Final = 0.2
# when no keywords match


class KeywordClassifier:
    """Baseline classifier. Satisfies the Classifier protocol
    stucturally no inheritance required."""

    def classify(self, text: str) -> Classification:
        normalised_text = text.lower()
        scores: dict[Category, int] = {
            category: sum(1 for keyword in keywords if keyword in normalised_text)
            for category, keywords in KEYWORD_MAP.items()
        }

        best_category = max(scores, key=lambda category: scores[category])
        best_score = scores[best_category]

        if best_score == 0:
            return Classification(
                category=Category.OTHER,
                confidence=FALLBACK_CONFIDENCE,
                reasoning="no keywords matched",
                classifier_name="keyword",
            )

        matched_keywords = [kw for kw in KEYWORD_MAP[best_category] if kw in normalised_text]
        confidence = min(1.0, best_score / MAX_SCORE_FOR_FULL_CONFIDENCE)

        return Classification(
            category=best_category,
            confidence=confidence,
            reasoning=f"matched keywords: {', '.join(matched_keywords)}",
            classifier_name="keyword",
        )
