import streamlit as st
import datetime
from services.calendar_service import create_event, get_calendar_events, create_weekly_class
from utils.ai_agent import parse_schedule_request


def convert_to_24hr(time_str):
    try:
        return datetime.datetime.strptime(time_str.strip(), "%I:%M %p").time()
    except:
        return None


if "recommended_request" not in st.session_state:
    st.session_state.recommended_request = ""

if "success_message" not in st.session_state:
    st.session_state.success_message = ""

if "show_manual" not in st.session_state:
    st.session_state.show_manual = False

if "show_class_form" not in st.session_state:
    st.session_state.show_class_form = False


st.title("Smart Timetable AI Agent")

if st.session_state.success_message:
    st.success(st.session_state.success_message)


# ================= AI SECTION =================
st.subheader("AI Schedule Assistant")
st.caption("Enter request like: Schedule project discussion tomorrow at 5 PM for 2 hours")

user_request = st.text_input("", value=st.session_state.recommended_request)

if st.button("Schedule with AI"):

    parsed = parse_schedule_request(user_request)

    if not parsed:
        st.error("Could not understand the request.")
    else:
        title = parsed["title"]
        date_obj = datetime.datetime.strptime(parsed["date"], "%Y-%m-%d").date()
        start_time = convert_to_24hr(parsed["start_time"])
        duration = parsed["duration_minutes"]

        if not start_time:
            st.error("Invalid time format.")
        else:
            start_dt = datetime.datetime.combine(date_obj, start_time)
            end_dt = start_dt + datetime.timedelta(minutes=duration)

            result = create_event(title, start_dt.isoformat(), end_dt.isoformat())

            if result["status"] == "duplicate":
                st.warning("⚠ This exact event already exists.")

            elif result["status"] == "conflict":
                st.error(
                    f"⚠ Conflict with '{result['title']}' "
                    f"from {result['start']} to {result['end']}"
                )

                if result["suggested_start"]:
                    st.info(f"Suggested Start Time: {result['suggested_start']}")
                    st.session_state.recommended_request = (
                        f"Schedule {title} tomorrow at "
                        f"{result['suggested_start']} for "
                        f"{duration // 60} hour"
                    )

            else:
                st.session_state.success_message = (
                    f"✅ Successfully scheduled '{title}' "
                    f"on {date_obj.strftime('%d %b %Y')} "
                    f"at {parsed['start_time']}."
                )
                st.session_state.recommended_request = ""
                st.rerun()


st.divider()


# ================= MANUAL SECTION =================
st.subheader("Create Schedule Manually")

if st.button("Create Manually"):
    st.session_state.show_manual = True

if st.session_state.show_manual:

    event_title = st.text_input("Event Title")
    date = st.date_input("Event Date")
    start_input = st.text_input("Start Time (e.g., 5:00 PM)")
    end_input = st.text_input("End Time (e.g., 6:00 PM)")

    if st.button("Create Event"):

        start_time = convert_to_24hr(start_input)
        end_time = convert_to_24hr(end_input)

        if not event_title:
            st.error("Enter event title.")
        elif not start_time or not end_time:
            st.error("Invalid time format.")
        elif end_time <= start_time:
            st.error("End must be after start.")
        else:
            start_dt = datetime.datetime.combine(date, start_time)
            end_dt = datetime.datetime.combine(date, end_time)

            result = create_event(event_title, start_dt.isoformat(), end_dt.isoformat())

            if result["status"] == "duplicate":
                st.warning("⚠ This exact event already exists.")
            elif result["status"] == "conflict":
                st.error("⚠ Conflict detected.")
            else:
                st.session_state.success_message = (
                    f"✅ Successfully scheduled '{event_title}'."
                )
                st.rerun()


st.divider()


# ================= CLASS TEMPLATE =================
st.subheader("📚 Class Schedule Template")

if st.button("Add Weekly Class"):
    st.session_state.show_class_form = True

if st.session_state.show_class_form:

    class_name = st.text_input("Class Name")
    day = st.selectbox(
        "Day of Week",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    )
    class_time = st.text_input("Start Time (e.g., 9:00 AM)")
    duration = st.number_input("Duration (minutes)", 30, 300, 60, step=30)
    weeks = st.number_input("Number of Weeks", 1, 16, 8)

    if st.button("Create Weekly Class"):
        if not class_name:
            st.error("Enter class name.")
        else:
            try:
                link = create_weekly_class(
                    class_name, day, class_time, duration, weeks
                )
                st.success("✅ Weekly class created successfully!")
                st.write(f"View in Calendar: {link}")
            except:
                st.error("Invalid time format.")


st.divider()

st.subheader("Upcoming Events")

events = get_calendar_events()

if not events:
    st.write("No upcoming events found.")

for event in events:
    start = event["start"].get("dateTime", event["start"].get("date"))
    if "T" in start:
        dt = datetime.datetime.fromisoformat(start.split("+")[0])
        formatted = dt.strftime("%d %b %Y | %I:%M %p")
    else:
        formatted = start

    st.write(f"{event.get('summary', 'No Title')} - {formatted}")