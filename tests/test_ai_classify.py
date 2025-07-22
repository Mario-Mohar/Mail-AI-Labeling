import pytest
from ai_classify import classify_email

# Dummy-Modell und Dummy-Antworten
class DummyResponse:
    def __init__(self, text):
        self.text = text

class DummyModel:
    def generate_content(self, prompt):
        if "Zahlung" in prompt:
            return DummyResponse("rechnung")
        return DummyResponse("newsletter")

def dummy_classify_email(subject, sender, body, regeln, gmail_labels=None):
    if "Zahlung" in subject or "Zahlung" in body:
        return {
            "kategorie": "rechnung",
            "ist_newsletter": False,
            "ist_unbezahlt": False,
            "unsubscribe_url": None
        }
    return {
        "kategorie": "newsletter",
        "ist_newsletter": True,
        "ist_unbezahlt": False,
        "unsubscribe_url": None
    }

def test_classify_email_mock(monkeypatch):
    # Dummy-Modell einsetzen
    import ai_classify
    ai_classify._classifier_instance = None
    monkeypatch.setattr(ai_classify, "classify_email", dummy_classify_email)

    regeln = {
        "rechnung": {"keywords": [], "label": "Rechnungen"},
        "newsletter": {"keywords": [], "label": "Newsletter"}
    }

    subject = "Zahlungserinnerung Juni"
    sender = "firma@example.com"
    body = "Bitte überweisen Sie den offenen Betrag bis 30.06."

    result = classify_email(subject, sender, body, regeln)
    assert result["kategorie"] == "rechnung"
    assert not result["ist_newsletter"]

def test_classify_email_fallback(monkeypatch):
    import ai_classify
    ai_classify._classifier_instance = None
    monkeypatch.setattr(ai_classify, "classify_email", dummy_classify_email)

    regeln = {
        "rechnung": {"keywords": [], "label": "Rechnungen"},
        "newsletter": {"keywords": [], "label": "Newsletter"}
    }

    subject = "Willkommen zu unserem Sommer-Newsletter"
    sender = "news@example.com"
    body = "Hier ist Ihre Juli-Ausgabe mit spannenden Tipps."

    result = classify_email(subject, sender, body, regeln)
    assert result["kategorie"] == "newsletter"
    assert result["ist_newsletter"]

