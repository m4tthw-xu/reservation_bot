import datetime as dt
import os.path
import random

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import timedelta
from datetime import datetime

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def main():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port = 0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        # Call the Calendar API
        now = dt.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
        print("Getting the upcoming 10 events")
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

        if not events:
            print("No upcoming events found.")
            return

        # Prints the start and name of the next 10 events
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            print(start, event["summary"])

        rand_events(service)

    except HttpError as error:
        print(f"An error occurred: {error}")


# this function will randomly populate my gcal with events to simulate a busy schedule, since my schedule isn't busy lol
def rand_events(service):
    calendar_id = 'primary'  # or 'your_calendar_id'

    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)

    for _ in range(10):  # number of events to generate
        # Generate a random start time
        start_time = start_date + timedelta(hours=random.randint(7, 22 * 7 - 1))

        # Generate a random end time (1-3 hours after the start time)
        end_time = start_time + timedelta(hours=random.randint(1, 3))

        # Generate a random event title
        event_title = f'Random Event {random.randint(1, 100)}'

        # Create the event
        event = {
            'summary': event_title,
            'start': {'dateTime': start_time.isoformat(timespec='seconds'), 'timeZone': 'America/New_York'},
            'end': {'dateTime': end_time.isoformat(timespec='seconds'), 'timeZone': 'America/New_York'},
        }

        # Insert the event into the calendar
        event = service.events().insert(calendarId=calendar_id, body=event).execute()

        print(f'Event created: {event.get("htmlLink")}')



if __name__ == "__main__":
  main()