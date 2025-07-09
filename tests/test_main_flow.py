import pytest
import builtins
import json
from unittest.mock import MagicMock, patch
from main import main

@patch("google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file")
@patch("ai_classify.classify_email")
@patch("gmail_utils.move_email_to_label")
@patch("gmail_utils.get_or_create_label")
@patch("gmail_utils.get_gmail_service")
def test_main_flow(mock_get_service, mock_get_label, mock_move_email, mock_classify, mock_from_client_secrets_file, tmp_path):
    # === Dummy Credentials mit gültigem universe_domain ===
    dummy_creds = MagicMock()
    dummy_creds.to_json.return_value = "{}"
    dummy_creds.universe_domain = "googleapis.com"

    # === OAuth Flow Simulation ===
    mock_flow = MagicMock()
    mock_flow.run_local_server.return_value = dummy_creds
    mock_from_client_secrets_file.return_value = mock_flow

    # === Gmail Service Simulation ===
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service

    # Simuliere vorhandene Labels
    mock_service.users.return_value.labels.return_value.list.return_value.execute.return_value = {
        "labels": [
            {"id": "Label_1", "name": "Rechnungen"},
            {"id": "Label_2", "name": "Privat"},
        ]
    }

    # Simuliere ungelesene Nachrichten
    mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        "messages": [{"id": "123"}]
    }

    # Simuliere E-Mail Inhalt
    mock_service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Ihre Rechnung"},
                {"name": "From", "value": "firma@example.com"}
            ],
            "body": {"data": "SGVsdG8gd29ybGQ="}  # base64("Hello world")
        }
    }

    # Simuliere Klassifizierung
    mock_classify.return_value = "rechnung"

    # Simuliere Label-Zuweisung
    mock_get_label.return_value = "Label_1"

    # === Regeln-Datei vorbereiten ===
    rules_path = tmp_path / "regeln.json"
    rules = {"rechnung": {"keywords": [], "label": "Rechnungen"}}
    rules_path.write_text(json.dumps(rules, ensure_ascii=False), encoding="utf-8")

    # === open() patchen, um regeln.json zu erzwingen ===
    open_orig = open

    def open_patched(file, mode="r", *args, **kwargs):
        if file == "regeln.json":
            return open_orig(rules_path, mode, *args, **kwargs)
        return open_orig(file, mode, *args, **kwargs)

    builtins.open = open_patched

    # === Test ausführen ===
    try:
        main()
    finally:
        builtins.open = open_orig
