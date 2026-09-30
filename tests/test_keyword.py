from router.classification.base import Classifier
from router.classification.keyword import FALLBACK_CONFIDENCE, KeywordClassifier
from router.domain.models import Category


def test_classifies_clear_billing_ticket() -> None:
    classifier = KeywordClassifier()
    result = classifier.classify("I was charger twice on my last invoice, please refund me.")

    assert result.category == Category.BILLING
    assert result.confidence > 0
    assert "invoice" in result.reasoning
    assert result.classifier_name == "keyword"


def test_tie_between_two_tickets() -> None:
    classifier = KeywordClassifier()
    result = classifier.classify(
        "I ran into two main issues. I cannot change my password on my "
        "account and I have not gotten an invoice for my next payment."
    )

    assert result.category == Category.BILLING
    assert result.confidence > 0
    assert "invoice" in result.reasoning
    assert "payment" in result.reasoning
    assert result.classifier_name == "keyword"


def test_ticket_category_other() -> None:
    classifier = KeywordClassifier()
    result = classifier.classify("I am interested in applying to the CEO position on your company.")

    assert result.category == Category.OTHER
    assert result.confidence == FALLBACK_CONFIDENCE
    assert result.classifier_name == "keyword"


def test_ticket_with_full_confidence() -> None:
    classifier = KeywordClassifier()
    result = classifier.classify(
        "I cannot express how dissapointed, angry and frustrated "
        "I have been trying to solve this issue."
    )

    assert result.category == Category.COMPLAINT
    assert result.confidence == 1.0
    assert "dissapointed" in result.reasoning
    assert "angry" in result.reasoning
    assert "frustrated" in result.reasoning
    assert result.classifier_name == "keyword"


def _accepts_classifier(classifier: Classifier) -> None:
    pass


def test_keyword_classifier_satisifies_protocol() -> None:
    _accepts_classifier(KeywordClassifier())
