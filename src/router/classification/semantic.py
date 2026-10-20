"""Semantic classifier: embeds a handful of canonical examples per category at
startup, then classifies new text by cosine similarity to the nearest one.

These canonical examples are written independently of data/golden.jsonl on
purpose. Using golden-set tickets as the reference examples here would leak
the evaluation set into the classifier: several golden tickets are close
paraphrases of each other, so the classifier could end up recognising a
golden ticket's own phrasing rather than genuinely generalising, which would
make its evaluation score an overestimate of how it would do on a ticket it
has never seen anything similar to.
"""

from typing import Final

from sentence_transformers import SentenceTransformer, util

from router.domain.models import Category, Classification

MODEL_NAME: Final = "all-MiniLM-L6-v2"

# margin (best similarity minus runner-up similarity) is typically small,
# cosine similarities between unrelated sentences from the same embedding
# model still cluster fairly close together, so a raw margin of, say, 0.08
# would map to a barely-there confidence if used unscaled. This factor was
# chosen by checking the actual margins produced against a few dozen golden
# tickets (see LEARNING.md) so that a clear, unambiguous win still produces a
# confidence a human would recognise as "confident", not just "slightly
# ahead".
CONFIDENCE_MARGIN_SCALE: Final = 6.0

CATEGORY_EXAMPLES: Final[dict[Category, list[str]]] = {
    Category.BILLING: [
        "I was charged twice for my subscription this month, please refund the extra charge.",
        "Can you send me an invoice for last quarter's payments?",
        "Why did my plan price increase without any notice?",
    ],
    Category.TECHNICAL: [
        "The app crashes every time I try to upload a file.",
        "I'm getting a 500 error when I submit the form.",
        "The integration stopped syncing data after the last update.",
    ],
    Category.ACCOUNT: [
        "I forgot my password and the reset link isn't arriving.",
        "I need to add a new user to our workspace.",
        "I'm locked out of my account after changing my email address.",
    ],
    Category.COMPLAINT: [
        "I've been waiting three weeks for a reply and nobody has helped me.",
        "This is the second time this has happened and I want it escalated.",
        "I'm extremely unhappy with how this was handled.",
    ],
    Category.OTHER: [
        "I'd like to apply for a sales role at your company.",
        "Do you offer partnership opportunities for resellers?",
        "I'm a journalist writing about your product, can we talk?",
    ],
}


class SemanticClassifier:
    """Embedding-similarity classifier. Satisfies the Classifier protocol
    structurally, same as KeywordClassifier, no inheritance required.
    """

    def __init__(self, model_name: str = MODEL_NAME) -> None:
        self._model = SentenceTransformer(model_name)

        self._category_order: list[Category] = []
        example_texts: list[str] = []
        for category, examples in CATEGORY_EXAMPLES.items():
            for example in examples:
                self._category_order.append(category)
                example_texts.append(example)

        self._example_embeddings = self._model.encode(example_texts, convert_to_tensor=True)

    def classify(self, text: str) -> Classification:
        text_embedding = self._model.encode(text, convert_to_tensor=True)
        similarities = util.cos_sim(text_embedding, self._example_embeddings)[0].tolist()

        # best similarity per category, not per individual example, an
        # unusually good match on one example shouldn't need every example in
        # that category to also score well
        best_per_category: dict[Category, float] = {}
        for category, score in zip(self._category_order, similarities, strict=True):
            if category not in best_per_category or score > best_per_category[category]:
                best_per_category[category] = score

        ranked = sorted(best_per_category.items(), key=lambda item: item[1], reverse=True)
        best_category, best_score = ranked[0]
        second_score = ranked[1][1] if len(ranked) > 1 else 0.0
        margin = best_score - second_score

        confidence = max(0.0, min(1.0, margin * CONFIDENCE_MARGIN_SCALE))

        return Classification(
            category=best_category,
            confidence=confidence,
            reasoning=(
                f"closest category by embedding similarity (score={best_score:.3f}, "
                f"margin over runner-up={margin:.3f})"
            ),
            classifier_name="semantic",
        )
