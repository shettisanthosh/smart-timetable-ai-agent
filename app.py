import streamlit as st
from services.calendar_service import get_calendar_events, create_event
import datetime

st.title("Smart Timetable AI Agent")

st.subheader("Create New Event")

event_title = st.text_input("Event Title")

date = st.date_input("Event Date")
start_time = st.time_input("Start Time")
end_time = st.time_input("End Time")

if st.button("Create Event"):
    start_datetime = datetime.datetime.combine(date, start_time)
    end_datetime = datetime.datetime.combine(date, end_time)

    start_iso = start_datetime.isoformat()
    end_iso = end_datetime.isoformat()

    link = create_event(event_title, start_iso, end_iso)
    st.success(f"Event Created! View here: {link}")

st.divider()

st.subheader("Upcoming Events")

events = get_calendar_events()

if not events:
    st.write("No upcoming events found.")

for event in events:
    st.write(f"{event['title']} - {event['time']}")