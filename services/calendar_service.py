from __future__ import print_function

import datetime
import json
import streamlit as st

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


# ===============================
# GOOGLE AUTHENTICATION (Cloud Safe)
# ===============================
def authenticate_google():
    """
    Authenticate using credentials stored in Streamlit secrets.
    Works on Streamlit Cloud without opening a browser.
    """

    try:
        credentials_info = json.loads(st.secrets["GOOGLE_CREDENTIALS"])

        creds = Credentials.from_authorized_user_info(
            credentials_info,
            SCOPES
        )

        service = build("calendar", "v3", credentials=creds)

        return service

    except Exception as e:
        st.error(f"Google Authentication Error: {e}")
        return None


# ===============================
# GET UPCOMING EVENTS
# ===============================
def get_calendar_events():

    service = authenticate_google()

    if service is None:
        return []

    now = datetime.datetime.utcnow().isoformat() + "Z"

    try:

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=20,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        return events_result.get("items", [])

    except Exception as e:
        st.error(f"Error fetching events: {e}")
        return []


# ===============================
# CREATE EVENT
# (Duplicate + Conflict detection)
# ===============================
def create_event(summary, start_time, end_time):

    service = authenticate_google()

    if service is None:
        return {"status": "error"}

    new_start = datetime.datetime.fromisoformat(start_time)
    new_end = datetime.datetime.fromisoformat(end_time)

    duration = new_end - new_start

    day_start = new_start.replace(hour=8, minute=0, second=0, microsecond=0)
    day_end = new_start.replace(hour=22, minute=0, second=0, microsecond=0)

    try:

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=day_start.isoformat() + "Z",
                timeMax=day_end.isoformat() + "Z",
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])
        busy_slots = []

        for event in events:

            if "dateTime" in event["start"]:

                existing_start = datetime.datetime.fromisoformat(
                    event["start"]["dateTime"].split("+")[0]
                )

                existing_end = datetime.datetime.fromisoformat(
                    event["end"]["dateTime"].split("+")[0]
                )

                existing_title = event.get("summary", "")

                # Prevent duplicate event
                if (
                    existing_start == new_start
                    and existing_end == new_end
                    and existing_title.lower() == summary.lower()
                ):
                    return {"status": "duplicate"}

                busy_slots.append((existing_start, existing_end, existing_title))

        busy_slots.sort(key=lambda x: x[0])

        # Conflict detection
        for start_dt, end_dt, title in busy_slots:

            if new_start < end_dt and new_end > start_dt:

                suggested_start = end_dt

                if suggested_start + duration > day_end:

                    return {
                        "status": "conflict",
                        "title": "No available slot today",
                        "start": "",
                        "end": "",
                        "suggested_start": None,
                    }

                return {
                    "status": "conflict",
                    "title": title,
                    "start": start_dt.strftime("%I:%M %p"),
                    "end": end_dt.strftime("%I:%M %p"),
                    "suggested_start": suggested_start.strftime("%I:%M %p"),
                }

        # Create event
        event_body = {
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

        created_event = service.events().insert(
            calendarId="primary",
            body=event_body
        ).execute()

        return {
            "status": "success",
            "link": created_event.get("htmlLink"),
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# ===============================
# CREATE WEEKLY CLASS (Recurring)
# ===============================
def create_weekly_class(summary, day_of_week, start_time_str, duration_minutes, weeks):

    service = authenticate_google()

    if service is None:
        return None

    start_time = datetime.datetime.strptime(
        start_time_str.strip(),
        "%I:%M %p"
    ).time()

    today = datetime.date.today()

    days_map = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6,
    }

    target_day = days_map[day_of_week]

    days_ahead = target_day - today.weekday()

    if days_ahead < 0:
        days_ahead += 7

    first_date = today + datetime.timedelta(days=days_ahead)

    start_datetime = datetime.datetime.combine(first_date, start_time)

    end_datetime = start_datetime + datetime.timedelta(minutes=duration_minutes)

    try:

        event_body = {
            "summary": summary,
            "start": {
                "dateTime": start_datetime.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "end": {
                "dateTime": end_datetime.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "recurrence": [
                f"RRULE:FREQ=WEEKLY;COUNT={weeks}"
            ],
        }

        created_event = service.events().insert(
            calendarId="primary",
            body=event_body
        ).execute()

        return created_event.get("htmlLink")

    except Exception as e:
        st.error(f"Error creating weekly class: {e}")
        return None