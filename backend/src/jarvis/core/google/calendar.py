from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from googleapiclient.errors import HttpError

from jarvis.core.errors import ServiceError
from jarvis.core.google.auth import TokenStore, build_service


@dataclass(frozen=True)
class CalendarEvent:
    id: str
    summary: str
    start: str
    end: str
    location: str


def _to_event(item: dict[str, Any]) -> CalendarEvent:
    return CalendarEvent(
        id=item["id"],
        summary=item.get("summary", "(untitled)"),
        start=item["start"].get("dateTime", item["start"].get("date", "")),
        end=item["end"].get("dateTime", item["end"].get("date", "")),
        location=item.get("location", ""),
    )


class CalendarService:
    def __init__(self, user_id: str, store: TokenStore, tzinfo: ZoneInfo) -> None:
        self._user_id = user_id
        self._store = store
        self._tzinfo = tzinfo
        self._service: Any = None

    @property
    def service(self) -> Any:
        if self._service is None:
            self._service = build_service("calendar", "v3", self._user_id, self._store)
        return self._service

    def list_events(self, days_ahead: int = 7, limit: int = 20) -> list[CalendarEvent]:
        now = datetime.now(self._tzinfo)
        try:
            result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=now.isoformat(),
                    timeMax=(now + timedelta(days=days_ahead)).isoformat(),
                    maxResults=limit,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
        except HttpError as exc:
            raise ServiceError(f"Could not list your events: {exc}") from exc

        return [_to_event(item) for item in result.get("items", [])]

    def create_event(
        self,
        summary: str,
        start: datetime,
        end: datetime,
        description: str = "",
        location: str = "",
    ) -> CalendarEvent:
        body = {
            "summary": summary,
            "description": description,
            "location": location,
            "start": {"dateTime": start.isoformat(), "timeZone": str(self._tzinfo)},
            "end": {"dateTime": end.isoformat(), "timeZone": str(self._tzinfo)},
        }
        try:
            item = self.service.events().insert(calendarId="primary", body=body).execute()
        except HttpError as exc:
            raise ServiceError(f"Could not create that event: {exc}") from exc
        return _to_event(item)

    def delete_event(self, event_id: str) -> None:
        try:
            self.service.events().delete(calendarId="primary", eventId=event_id).execute()
        except HttpError as exc:
            raise ServiceError(f"Could not delete that event: {exc}") from exc