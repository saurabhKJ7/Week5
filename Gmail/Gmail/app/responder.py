from __future__ import annotations

import re
from typing import List

import openai

from .cache import RedisCache
from .config import get_settings
from .embeddings import DocumentIngestor
from .gmail_service import GmailService

settings = get_settings()
openai.api_key = settings.openai_api_key


class AutoResponder:
    def __init__(self):
        self.gmail = GmailService()
        self.ingestor = DocumentIngestor()
        self.cache = RedisCache()

    # ------------ Helpers ------------- #
    @staticmethod
    def _professional_tone() -> str:
        return (
            "You are an automated email responder representing Acme Corp."
            " Maintain a polite, professional, and concise tone in all replies."
        )

    def _build_prompt(self, email_body: str, policy_chunks: List[str]) -> List[dict]:
        context = "\n\n".join(policy_chunks)
        system_prompt = self._professional_tone()
        user_prompt = (
            f"Company Policies & FAQs:\n{context}\n\nIncoming email:\n{email_body}\n\nDraft a reply:"  # noqa: E501
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _generate_reply(self, body: str, chunks: List[str]) -> str:
        cached = self.cache.get(body)
        if cached:
            return cached
        messages = self._build_prompt(body, chunks)
        completion = openai.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=0.3,
            max_tokens=400,
        )
        reply = completion.choices[0].message.content.strip()
        self.cache.set(body, reply)
        return reply

    # ------------ Main loop ----------- #
    def process_unread_emails(self):
        ids = self.gmail.list_unread_message_ids()
        for msg_id in ids:
            try:
                thread_id, subject, body = self.gmail.get_message(msg_id)
                chunks = self.ingestor.search(body)
                reply_body = self._generate_reply(body, chunks)
                to_email = self._extract_sender(msg_id)
                self.gmail.send_message(
                    to_email=to_email,
                    subject=f"Re: {subject}",
                    body=reply_body,
                    thread_id=thread_id,
                )
            finally:
                self.gmail.mark_as_read(msg_id)

    def _extract_sender(self, msg_id: str) -> str:
        service = self.gmail._get_service()
        metadata = (
            service.users()
            .messages()
            .get(userId="me", id=msg_id, format="metadata", metadataHeaders=["From"])
            .execute()
        )
        from_header = next(
            (h["value"] for h in metadata["payload"]["headers"] if h["name"] == "From"),
            "",
        )
        match = re.search(r"<(.+?)>", from_header)
        return match.group(1) if match else from_header 