import re
import datetime


def parse_schedule_request(user_input):

    user_input_lower = user_input.lower()

    # Duration
    duration_match = re.search(r'(\d+)\s*(hour|hours|minute|minutes)', user_input_lower)

    if duration_match:
        value = int(duration_match.group(1))
        unit = duration_match.group(2)
        duration_minutes = value * 60 if "hour" in unit else value
    else:
        duration_minutes = 60

    # Time
    time_match = re.search(r'(\d{1,2}(:\d{2})?\s*(am|pm))', user_input_lower)
    if not time_match:
        return None

    start_time = time_match.group(1).upper()

    # Date
    today = datetime.date.today()
    if "tomorrow" in user_input_lower:
        date = today + datetime.timedelta(days=1)
    else:
        date = today

    # Title (clean)
    title_match = re.search(r'schedule\s+(.*?)\s+at', user_input_lower)
    title = title_match.group(1).strip().title() if title_match else "Meeting"

    return {
        "title": title,
        "date": date.strftime("%Y-%m-%d"),
        "start_time": start_time,
        "duration_minutes": duration_minutes
    }