from __future__ import print_function
import datetime
import json
import os
import streamlit as st

from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


# ===============================
# AUTHENTICATION
# ===============================
def authenticate_google():
    """
    Works both locally and on Streamlit Cloud.
    Uses credentials stored in Streamlit Secrets.
    """

    try:
        credentials_info = json.loads(st.secrets["GOOGLE_CREDENTIALS"])

        creds = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=SCOPES
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


# ===============================
# CREATE EVENT
# ===============================
def create_event(summary, start_time, end_time):

    service = authenticate_google()

    if service is None:
        return {"status": "error"}

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


# ===============================
# CREATE WEEKLY CLASS
# ===============================
def create_weekly_class(summary, day_of_week, start_time_str, duration_minutes, weeks):

    service = authenticate_google()

    if service is None:
        return None

    start_time = datetime.datetime.strptime(start_time_str.strip(), "%I:%M %p").time()

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