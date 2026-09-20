from __future__ import annotations

import base64
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any

from googleapiclient.errors import HttpError

from jarvis.core.errors import ServiceError
from jarvis.core.google.auth import TokenStore, build_service


@dataclass(frozen=True)
class MessageSummary:
    id: str
    sender: str
    subject: str
    snippet: str
    unread: bool


@dataclass(frozen=True)
class MessageBody:
    id: str
    sender: str
    subject: str
    body: str


def _header(payload: dict[str, Any], name: str) -> str:
    for header in payload.get("headers", []):
        if header["name"].lower() == name.lower():
            return str(header["value"])
    return ""


def _plain_text(payload: dict[str, Any]) -> str:
    """Walk the MIME tree and return the first text/plain part."""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        if text := _plain_text(part):
            return text
    return ""


class GmailService:
    def __init__(self, user_id: str, store: TokenStore) -> None:
        self._user_id = user_id
        self._store = store
        self._service: Any = None

    @property
    def service(self) -> Any:
        if self._service is None:
            self._service = build_service("gmail", "v1", self._user_id, self._store)
        return self._service

    def search(self, query: str, limit: int = 10) -> list[MessageSummary]:
        try:
            listing = (
                self.service.users()
                .messages()
                .list(userId="me", q=query, maxResults=limit)
                .execute()
            )
            results = []
            for ref in listing.get("messages", []):
                message = (
                    self.service.users()
                    .messages()
                    .get(
                        userId="me",
                        id=ref["id"],
                        format="metadata",
                        metadataHeaders=["From", "Subject"],
                    )
                    .execute()
                )
                results.append(
                    MessageSummary(
                        id=message["id"],
                        sender=_header(message["payload"], "From"),
                        subject=_header(message["payload"], "Subject"),
                        snippet=message.get("snippet", ""),
                        unread="UNREAD" in message.get("labelIds", []),
                    )
                )
            return results
        except HttpError as exc:
            raise ServiceError(f"Gmail search failed: {exc}") from exc

    def read(self, message_id: str) -> MessageBody:
        try:
            message = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
        except HttpError as exc:
            raise ServiceError(f"Could not read that message: {exc}") from exc

        payload = message["payload"]
        return MessageBody(
            id=message["id"],
            sender=_header(payload, "From"),
            subject=_header(payload, "Subject"),
            body=_plain_text(payload).strip(),
        )

    @staticmethod
    def _encode(to: str, subject: str, body: str, cc: str | None) -> dict[str, str]:
        message = EmailMessage()
        message["To"] = to
        message["Subject"] = subject
        if cc:
            message["Cc"] = cc
        message.set_content(body)
        return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}

    def create_draft(self, to: str, subject: str, body: str, cc: str | None = None) -> str:
        try:
            draft = (
                self.service.users()
                .drafts()
                .create(userId="me", body={"message": self._encode(to, subject, body, cc)})
                .execute()
            )
            return str(draft["id"])
        except HttpError as exc:
            raise ServiceError(f"Could not create the draft: {exc}") from exc

    def send_draft(self, draft_id: str) -> str:
        try:
            sent = (
                self.service.users().drafts().send(userId="me", body={"id": draft_id}).execute()
            )
            return str(sent["id"])
        except HttpError as exc:
            raise ServiceError(f"Could not send the draft: {exc}") from exc

    def archive(self, message_id: str) -> None:
        try:
            self.service.users().messages().modify(
                userId="me", id=message_id, body={"removeLabelIds": ["INBOX"]}
            ).execute()
        except HttpError as exc:
            raise ServiceError(f"Could not archive that message: {exc}") from exc

    def trash(self, message_id: str) -> None:
        try:
            self.service.users().messages().trash(userId="me", id=message_id).execute()
        except HttpError as exc:
            raise ServiceError(f"Could not move that message to trash: {exc}") from exc