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

def test_classify_email_mock(monkeypatch):
    # Dummy-Modell einsetzen
    import ai_classify
    ai_classify._model = DummyModel()

    regeln = {
        "rechnung": {"keywords": [], "label": "Rechnungen"},
        "newsletter": {"keywords": [], "label": "Newsletter"}
    }

    subject = "Zahlungserinnerung Juni"
    sender = "firma@example.com"
    body = "Bitte überweisen Sie den offenen Betrag bis 30.06."

    result = classify_email(subject, sender, body, regeln)
    assert result == "rechnung"

def test_classify_email_fallback(monkeypatch):
    import ai_classify
    ai_classify._model = DummyModel()

    regeln = {
        "rechnung": {"keywords": [], "label": "Rechnungen"},
        "newsletter": {"keywords": [], "label": "Newsletter"}
    }

    subject = "Willkommen zu unserem Sommer-Newsletter"
    sender = "news@example.com"
    body = "Hier ist Ihre Juli-Ausgabe mit spannenden Tipps."

    result = classify_email(subject, sender, body, regeln)
    assert result == "newsletter"

