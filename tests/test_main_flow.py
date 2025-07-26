import os
import json
import builtins
from unittest.mock import patch, MagicMock, mock_open
from main import main

@patch("ai_classify.classify_email")
@patch("gmail_utils.move_email_to_label")
@patch("gmail_utils.get_or_create_label")
@patch("gmail_utils.get_gmail_service")
@patch("utils.get_email_body", return_value="Test Body")
@patch("rules_utils.lade_regeln")
@patch("rules_utils.speichere_regeln")
@patch("utils.log_unsubscribe_link")
@patch("utils.logge_neue_kategorie")
def test_main_flow(mock_log_kat, mock_log_unsub, mock_save_rules, mock_load_rules, mock_get_body, mock_get_service, mock_get_label, mock_move_email, mock_classify):
    # === Fake Gmail Service ===
    fake_service = MagicMock()

    fake_service.users.return_value.labels.return_value.list.return_value.execute.return_value = {
        "labels": [
            {"id": "Label_1", "name": "Rechnungen"},
            {"id": "Label_2", "name": "Privat"},
        ]
    }

    fake_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        "messages": [{"id": "123"}]
    }

    fake_service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Ihre Rechnung"},
                {"name": "From", "value": "firma@example.com"},
            ],
            "body": {"data": "SGVsdG8gd29ybGQ="}
        }
    }

    mock_get_service.return_value = fake_service
    mock_classify.return_value = {
        "kategorie": "rechnung",
        "ist_newsletter": False,
        "ist_unbezahlt": False,
        "unsubscribe_url": None
    }
    mock_get_label.return_value = "Label_1"

    # Regeln laden mocken
    rules_content = {
        "rechnung": {"keywords": [], "label": "Rechnungen"}
    }
    mock_load_rules.return_value = rules_content

    # Umgebungsvariablen patchen
    with patch.dict(os.environ, {"REGELN_DATEI": "regeln.json", "LOG_DATEI": "mail_log.txt", "MAX_EMAILS": "50", "UNSUBSCRIBE_LOG": "unsubscribe_log.txt"}):
        main()
