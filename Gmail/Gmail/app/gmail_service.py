from __future__ import annotations

import os
import pickle
from typing import List, Optional, Tuple

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from .config import get_settings

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

TOKEN_FILE = "token.pickle"


class GmailService:
    """
    Wrapper around Gmail API client.
    Handles OAuth2 authentication, message retrieval and sending.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.creds: Optional[Credentials] = None

    # -------------------- Auth -------------------- #
    def _load_credentials(self) -> None:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "rb") as token:
                self.creds = pickle.load(token)

    def _save_credentials(self) -> None:
        if not self.creds:
            return
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(self.creds, token)

    def generate_auth_url(self) -> str:
        flow = Flow.from_client_config(
            {
                "installed": {
                    "client_id": self.settings.google_client_id,
                    "client_secret": self.settings.google_client_secret,
                    "redirect_uris": [self.settings.google_redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES,
        )
        flow.redirect_uri = self.settings.google_redirect_uri
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        self.state = flow.state  # type: ignore
        self._flow = flow  # type: ignore
        return auth_url

    def exchange_code(self, code: str) -> None:
        if not hasattr(self, "_flow"):
            flow = Flow.from_client_config(
                {
                    "installed": {
                        "client_id": self.settings.google_client_id,
                        "client_secret": self.settings.google_client_secret,
                        "redirect_uris": [self.settings.google_redirect_uri],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                },
                scopes=SCOPES,
            )
            flow.redirect_uri = self.settings.google_redirect_uri
        else:
            flow = self._flow  # type: ignore
        flow.fetch_token(code=code)
        self.creds = flow.credentials
        self._save_credentials()

    def _get_service(self):
        if not self.creds:
            self._load_credentials()
        if not self.creds or not self.creds.valid:
            raise RuntimeError("Gmail credentials missing or invalid. Please authorize first.")
        return build("gmail", "v1", credentials=self.creds, cache_discovery=False)

    # -------------------- Messages -------------------- #
    def list_unread_message_ids(self) -> List[str]:
        service = self._get_service()
        response = (
            service.users()
            .messages()
            .list(userId="me", q="is:unread", maxResults=50)
            .execute()
        )
        messages = response.get("messages", [])
        return [m["id"] for m in messages]

    def get_message(self, msg_id: str) -> Tuple[str, str, str]:
        """
        Returns tuple (thread_id, subject, body_text)
        """
        service = self._get_service()
        msg = (
            service.users().messages().get(userId="me", id=msg_id, format="full").execute()
        )
        payload = msg["payload"]
        headers = payload.get("headers", [])
        subject = next(
            (h["value"] for h in headers if h["name"].lower() == "subject"),
            "(no subject)",
        )
        thread_id = msg["threadId"]

        body = self._get_plain_text_from_payload(payload)
        return thread_id, subject, body

    def _get_plain_text_from_payload(self, payload):  # noqa: ANN001
        import base64

        def decode_part(part):  # noqa: ANN001
            data = part.get("body", {}).get("data")
            if not data:
                return ""
            data = data.replace("-", "+").replace("_", "/")
            decoded_bytes = base64.urlsafe_b64decode(data)
            try:
                return decoded_bytes.decode()
            except UnicodeDecodeError:
                return decoded_bytes.decode("latin1")

        if payload.get("mimeType") == "text/plain":
            return decode_part(payload)
        if payload.get("mimeType", "").startswith("multipart"):
            parts = payload.get("parts", [])
            for part in parts:
                text = self._get_plain_text_from_payload(part)
                if text:
                    return text
        return ""

    def mark_as_read(self, msg_id: str):
        service = self._get_service()
        service.users().messages().modify(
            userId="me", id=msg_id, body={"removeLabelIds": ["UNREAD"]}
        ).execute()

    def send_message(
        self,
        to_email: str,
        subject: str,
        body: str,
        thread_id: Optional[str] = None,
    ):
        import base64
        from email.mime.text import MIMEText

        message = MIMEText(body)
        message["to"] = to_email
        message["subject"] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"raw": encoded_message}
        if thread_id:
            create_message["threadId"] = thread_id

        service = self._get_service()
        return (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        ) 