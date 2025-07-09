import pytest
import builtins
import json
from unittest.mock import MagicMock, patch
from main import main

@patch("ai_classify.classify_email")
@patch("gmail_utils.move_email_to_label")
@patch("gmail_utils.get_or_create_label")
@patch("gmail_utils.get_gmail_service")
@patch("google_auth_oauthlib.flow.InstalledAppFlow.run_local_server")
def test_main_flow(mock_run_server, mock_service, mock_label, mock_move, mock_classify, tmp_path):
    # Dummy Gmail-OAuth Flow unterdrücken
    dummy_creds = MagicMock()
    dummy_creds.to_json.return_value = "{}"  # Verhindert TypeError beim write()
    mock_run_server.return_value = dummy_creds

    # Dummy Regeln-Datei vorbereiten
    rules_path = tmp_path / "regeln.json"
    rules = {"rechnung": {"keywords": [], "label": "Rechnungen"}}
    rules_path.write_text(json.dumps(rules, ensure_ascii=False), encoding="utf-8")

    # Patch open() um die Regeln-Datei zu verwenden
    open_orig = open
    def open_patched(file, mode="r", *args, **kwargs):
        if file == "regeln.json":
            return open_orig(rules_path, mode, *args, **kwargs)
        return open_orig(file, mode, *args, **kwargs)
    builtins.open = open_patched

    # Dummy Gmail Nachrichten simulieren
    mock_service.return_value.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        "messages": [{"id": "123"}]
    }
    mock_service.return_value.users.return_value.messages.return_value.get.return_value.execute.return_value = {
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Ihre Rechnung"},
                {"name": "From", "value": "firma@example.com"}
            ],
            "body": {"data": "SGVsdG8gd29ybGQ="}  # base64("Hello world")
        }
    }
    mock_classify.return_value = "rechnung"
    mock_label.return_value = "Label_1"

    # Test ausführen
    try:
        main()
    finally:
        builtins.open = open_orig
