import os
import datetime
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import settings


SCOPES = ['https://www.googleapis.com/auth/calendar']


class GoogleCalendarClient:
    """Client for interacting with Google Calendar API."""

    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Calendar API."""
        if os.path.exists(settings.google_calendar_token_path):
            self.creds = Credentials.from_authorized_user_file(
                settings.google_calendar_token_path, SCOPES
            )

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(settings.google_calendar_credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file not found at {settings.google_calendar_credentials_path}. "
                        "Please download it from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.google_calendar_credentials_path, SCOPES
                )
                self.creds = flow.run_local_server(port=0)

            with open(settings.google_calendar_token_path, 'w') as token:
                token.write(self.creds.to_json())

        self.service = build('calendar', 'v3', credentials=self.creds)

    def get_events(
        self,
        time_min: Optional[datetime.datetime] = None,
        time_max: Optional[datetime.datetime] = None,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Retrieve calendar events within a time range.

        Args:
            time_min: Start time (defaults to now)
            time_max: End time (defaults to 30 days from now)
            max_results: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        try:
            if time_min is None:
                time_min = datetime.datetime.utcnow()
            if time_max is None:
                time_max = time_min + datetime.timedelta(days=30)

            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            return events_result.get('items', [])

        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def create_event(
        self,
        summary: str,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Create a new calendar event.

        Args:
            summary: Event title
            start_time: Event start time
            end_time: Event end time
            description: Event description
            location: Event location

        Returns:
            Created event dictionary or None if failed
        """
        try:
            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
            }

            if description:
                event['description'] = description
            if location:
                event['location'] = location

            created_event = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()

            return created_event

        except HttpError as error:
            print(f"An error occurred: {error}")
            return None

    def update_event(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[datetime.datetime] = None,
        end_time: Optional[datetime.datetime] = None,
        description: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Update an existing calendar event.

        Args:
            event_id: ID of the event to update
            summary: New event title
            start_time: New start time
            end_time: New end time
            description: New description

        Returns:
            Updated event dictionary or None if failed
        """
        try:
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()

            if summary:
                event['summary'] = summary
            if start_time:
                event['start']['dateTime'] = start_time.isoformat()
            if end_time:
                event['end']['dateTime'] = end_time.isoformat()
            if description:
                event['description'] = description

            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()

            return updated_event

        except HttpError as error:
            print(f"An error occurred: {error}")
            return None

    def delete_event(self, event_id: str) -> bool:
        """
        Delete a calendar event.

        Args:
            event_id: ID of the event to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            return True

        except HttpError as error:
            print(f"An error occurred: {error}")
            return False

    def get_free_busy(
        self,
        time_min: datetime.datetime,
        time_max: datetime.datetime
    ) -> List[Dict]:
        """
        Get free/busy information for the calendar.

        Args:
            time_min: Start time
            time_max: End time

        Returns:
            List of busy time blocks
        """
        try:
            body = {
                "timeMin": time_min.isoformat() + 'Z',
                "timeMax": time_max.isoformat() + 'Z',
                "items": [{"id": "primary"}]
            }

            response = self.service.freebusy().query(body=body).execute()
            busy_times = response['calendars']['primary'].get('busy', [])

            return busy_times

        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
