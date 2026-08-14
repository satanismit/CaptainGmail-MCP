from pathlib import Path
import json
import os
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv


SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
STREAMLIT_CREDENTIALS_FILE = BASE_DIR / ".streamlit" / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"


load_dotenv()


def load_client_config() -> dict[str, Any] | None:
    """Load Google OAuth client config from env or common file locations."""

    env_var_names = (
        "GOOGLE_CLIENT_SECRETS_JSON",
        "GOOGLE_OAUTH_CLIENT_SECRETS_JSON",
        "GMAIL_CLIENT_SECRETS_JSON",
    )

    for env_var_name in env_var_names:
        raw_value = os.getenv(env_var_name, "").strip()

        if not raw_value:
            continue

        try:
            return json.loads(raw_value)
        except json.JSONDecodeError:
            continue

    for credentials_file in (
        CREDENTIALS_FILE,
        STREAMLIT_CREDENTIALS_FILE,
    ):
        if credentials_file.exists():
            return json.loads(credentials_file.read_text(encoding="utf-8"))

    return None


def authenticate_gmail() -> Credentials:
    """Authenticate the user and return valid Gmail credentials."""

    credentials = None

    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(
            str(TOKEN_FILE),
            SCOPES,
        )

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    if not credentials or not credentials.valid:
        client_config = load_client_config()

        if not client_config:
            raise FileNotFoundError(
                "Google OAuth client secrets were not found. Add "
                "credentials.json to the project root or .streamlit/ "
                "or set GOOGLE_CLIENT_SECRETS_JSON."
            )

        flow = InstalledAppFlow.from_client_config(
            client_config,
            SCOPES,
        )

        credentials = flow.run_local_server(
            port=0,
            open_browser=True,
        )

    TOKEN_FILE.write_text(
        credentials.to_json(),
        encoding="utf-8",
    )

    return credentials
