from __future__ import print_function
import datetime
import streamlit as st

from google.oauth2 import service_account
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/calendar"]


# ===============================
# AUTHENTICATION
# ===============================
def authenticate_google():
    """
    Authenticate using Service Account stored in Streamlit Secrets
    Works locally and on Streamlit Cloud
    """

    try:
        creds = service_account.Credentials.from_service_account_info(
            dict(st.secrets["GOOGLE_CREDENTIALS"]),
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
# ===============================
def create_event(summary, start_time, end_time):

    service = authenticate_google()

    if service is None:
        return {"status": "error"}

    try:
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
# CREATE WEEKLY CLASS
# ===============================
def create_weekly_class(summary, day_of_week, start_time_str, duration_minutes, weeks):

    service = authenticate_google()

    if service is None:
        return None

    try:

        start_time = datetime.datetime.strptime(
            start_time_str.strip(), "%I:%M %p"
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