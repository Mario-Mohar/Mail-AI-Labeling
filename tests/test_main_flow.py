import builtins
import json
from unittest.mock import MagicMock, patch, mock_open
from main import main

@patch("ai_classify.classify_email")
@patch("gmail_utils.move_email_to_label")
@patch("gmail_utils.get_or_create_label")
@patch("gmail_utils.get_gmail_service")
def test_main_flow(mock_get_service, mock_get_label, mock_move_email, mock_classify):
    # === Fake Gmail Service ===
    fake_service = MagicMock()

    # Labels simulieren
    fake_service.users.return_value.labels.return_value.list.return_value.execute.return_value = {
        "labels": [
            {"id": "Label_1", "name": "Rechnungen"},
            {"id": "Label_2", "name": "Privat"},
        ]
    }

    # Nachrichten simulieren
    fake_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        "messages": [{"id": "123"}]
    }

    # Nachrichtendetails simulieren
    fake_service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Ihre Rechnung"},
                {"name": "From", "value": "firma@example.com"},
            ],
            "body": {"data": "SGVsdG8gd29ybGQ="}  # base64("Hello world")
        }
    }

    mock_get_service.return_value = fake_service
    mock_classify.return_value = "rechnung"
    mock_get_label.return_value = "Label_1"

    # === Regeln-Datei simulieren ===
    rules_content = {
        "rechnung": {"keywords": [], "label": "Rechnungen"}
    }
    json_rules = json.dumps(rules_content, ensure_ascii=False)

    # Richtige Verwendung von mock_open für Dateiinhalt
    with patch("builtins.open", mock_open(read_data=json_rules)):
        main()
