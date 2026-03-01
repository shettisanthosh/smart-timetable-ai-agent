from __future__ import print_function
import datetime
import os.path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Full access (read + write)
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def authenticate_google():
    creds = None

    # Load saved token if exists
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If credentials invalid or not available, login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("calendar", "v3", credentials=creds)
    return service


#  Get upcoming events
def get_calendar_events():
    service = authenticate_google()

    now = datetime.datetime.utcnow().isoformat() + "Z"

    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    events = events_result.get("items", [])

    event_list = []

    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        event_list.append(
            {
                "title": event.get("summary", "No Title"),
                "time": start,
            }
        )

    return event_list


#  Create new event
def create_event(summary, start_time, end_time):
    service = authenticate_google()

    event = {
        "summary": summary,
        "start": {
            "dateTime": start_time,
            "timeZone": "Asia/Kolkata",
        },
        "end": {
            "dateTime": end_time,
            "timeZone": "Asia/Kolkata",
        },
    }

    event = service.events().insert(calendarId="primary", body=event).execute()

    return event.get("htmlLink")