import asyncio
import random
from datetime import datetime, timedelta

import pytz

import gcal_parse
import resy_scraper
import tagging_gpt
import db_manager
import restaurant_graph_visual
import request_gpt
import automation.sb as sb


async def main():

    # restaurants = ["LENOIR", "Carpenters Hall", "Launderette"]
    # requests = generate_random_requests(restaurants)

    # the restaurant data we need to create a request. we need to parse this request to actions
    requests = [
        {
         "date": "06/28/2024",
         "seats": 1,
         "restaurant": "Launderette",
         "city": "austin-tx",
         "time": "12:00",
         "time-zone": "America/Chicago",
         "duration": 2,
         "travel-buffer": 0
        }
    ]

    prompt = ("Can you reserve a lunch spot at Launderette for me and my girlfriend on Friday? I would like to spend two hours "
              "there.")

    # requests.append(request_gpt.get_request(prompt))

    for request in requests:
        print(request)

        # look in the database for the restaurant, get the link and modify it to match the request

        venue = db_manager.get_restaurant(request['restaurant'])
        link = venue['link']

        link = resy_scraper.update_url(link, request['date'], request['seats'])

        times = []

        attempts = 0
        while attempts < 3:
            attempts += 1
            times = await resy_scraper.scrape_reservation_buttons(link)
            if times:  # Check if times is not empty
                break
            await asyncio.sleep(1)  # Optional: wait before retrying
            print("trying to get reservations again...")

        print(times)

        date = request['date'].split('/')

        # get unavailable times from the GCAL
        unavailable_times = gcal_parse.get_events_on_day(int(date[2]), int(date[0]), int(date[1]), request['time-zone'])
        print(unavailable_times)

        try:
            closest_reservation = find_closest_reservation(request['date'], request['time'], float(request['duration']), float(request['travel-buffer']), times, unavailable_times, request['restaurant'])
            print(closest_reservation)

            times = extract_military_time(closest_reservation[len(closest_reservation) // 2])
            sb.click_time_button(times[0] + ":00", link, '')

            # Adjust the timezone offset
            offset = timedelta(hours=5)  # This timezone offset is for Austin, Texas

            adjusted_events = []
            for event in closest_reservation:
                start_time = datetime.strptime(event[0], '%Y-%m-%dT%H:%M:%S%z') + offset
                end_time = datetime.strptime(event[1], '%Y-%m-%dT%H:%M:%S%z') + offset
                adjusted_events.append((start_time.isoformat(), end_time.isoformat(), event[2]))

            gcal_parse.add_events_to_calendar(adjusted_events)


        except:
            continue





def find_closest_reservation(requested_date, requested_time, duration, travel_time, available_reservations, unavailable_times, restaurant_name):
    # Check for valid input
    if not isinstance(requested_date, str) or len(requested_date) != 10 or requested_date[2] != '/' or requested_date[5] != '/':
        raise ValueError("Invalid requested date")
    if not isinstance(requested_time, str) or len(requested_time) != 5 or requested_time[2] != ':':
        raise ValueError("Invalid requested time")
    if not isinstance(duration, (int, float)) or duration <= 0:
        raise ValueError("Invalid duration")
    if not isinstance(travel_time, (int, float)) or travel_time < 0:
        raise ValueError("Invalid travel time")
    if not isinstance(available_reservations, list) or not all(isinstance(reservation, dict) and 'time' in reservation and 'type' in reservation for reservation in available_reservations):
        raise ValueError("Invalid available reservations")
    if not isinstance(unavailable_times, dict) or not all(isinstance(times, tuple) and len(times) == 2 for times in unavailable_times.values()):
        raise ValueError("Invalid unavailable times")
    if not isinstance(restaurant_name, str):
        raise ValueError("Invalid restaurant name")

    # Convert requested time to minutes
    requested_time_minutes = int(requested_time[:2]) * 60 + int(requested_time[3:])

    # Convert unavailable times to minutes
    unavailable_minutes = []
    for start, end in unavailable_times.values():
        start_minutes = int(start[:2]) * 60 + int(start[2:])
        end_minutes = int(end[:2]) * 60 + int(end[2:])
        unavailable_minutes.append((start_minutes, end_minutes))

    # Find closest available reservation
    closest_reservation = None
    closest_diff = float('inf')
    for reservation in available_reservations:
        # Convert reservation time to minutes
        reservation_time_minutes = int(reservation['time'][:2]) * 60 + int(reservation['time'][3:])

        # Calculate start and end time with travel time buffer
        start_time_minutes = reservation_time_minutes - int(travel_time * 60)
        end_time_minutes = reservation_time_minutes + int(duration * 60) + int(travel_time * 60)

        # Check if reservation time is available
        is_available = True
        for start, end in unavailable_minutes:
            if (start_time_minutes >= start and start_time_minutes < end) or \
                    (end_time_minutes > start and end_time_minutes <= end) or \
                    (start_time_minutes < start and end_time_minutes > end):
                is_available = False
                break

        # If available, calculate difference from requested time
        if is_available:
            diff = abs(reservation_time_minutes - requested_time_minutes)
            if diff < closest_diff:
                closest_diff = diff
                closest_reservation = reservation

    # Return closest available reservation
    if closest_reservation:
        reservation_time = closest_reservation['time']
        if travel_time > 0:
            travel_start_time = (datetime.strptime(requested_date + ' ' + reservation_time, '%m/%d/%Y %H:%M') - timedelta(hours=travel_time)).isoformat() + '+00:00'
            travel_end_time = datetime.strptime(requested_date + ' ' + reservation_time, '%m/%d/%Y %H:%M').isoformat() + '+00:00'
            reservation_end_time = (datetime.strptime(requested_date + ' ' + reservation_time, '%m/%d/%Y %H:%M') + timedelta(hours=duration)).isoformat() + '+00:00'
            travel_back_start_time = reservation_end_time
            travel_back_end_time = (datetime.strptime(reservation_end_time, '%Y-%m-%dT%H:%M:%S%z') + timedelta(hours=travel_time)).isoformat()
            # Check for overlaps again before returning
            all_events = [
                (travel_start_time, travel_end_time, 'Travel to ' + restaurant_name),
                (travel_end_time, reservation_end_time, restaurant_name),
                (reservation_end_time, travel_back_end_time, 'Travel from ' + restaurant_name)
            ]
            for event in all_events:
                event_start_minutes = int(event[0][11:13]) * 60 + int(event[0][14:16])
                event_end_minutes = int(event[1][11:13]) * 60 + int(event[1][14:16])
                for start, end in unavailable_minutes:
                    if (event_start_minutes >= start and event_start_minutes < end) or \
                            (event_end_minutes > start and event_end_minutes <= end) or \
                            (event_start_minutes < start and event_end_minutes > end):
                        return None
            return all_events
        else:
            reservation_end_time = (datetime.strptime(requested_date + ' ' + reservation_time, '%m/%d/%Y %H:%M') + timedelta(hours=duration)).isoformat() + '+00:00'
            # Check for overlaps again before returning
            all_events = [
                (datetime.strptime(requested_date + ' ' + reservation_time, '%m/%d/%Y %H:%M').isoformat() + '+00:00', reservation_end_time, restaurant_name)
            ]
            for event in all_events:
                event_start_minutes = int(event[0][11:13]) * 60 + int(event[0][14:16])
                event_end_minutes = int(event[1][11:13]) * 60 + int(event[1][14:16])
                for start, end in unavailable_minutes:
                    if (event_start_minutes >= start and event_start_minutes < end) or \
                            (event_end_minutes > start and event_end_minutes <= end) or \
                            (event_start_minutes < start and event_end_minutes > end):
                        return None
            return all_events
    else:
        return None


def extract_military_time(time_range):
    start_time_str, end_time_str, _ = time_range

    # Extract the time part from the strings
    start_time = start_time_str[11:16]
    end_time = end_time_str[11:16]

    return start_time, end_time

def generate_random_requests(restaurants):
    requests = []
    for restaurant in restaurants:
        for _ in range(3):  # Generate 10 requests per restaurant
            request = {
                "date": "06/17/2024",
                "seats": random.randint(1, 3),
                "restaurant": restaurant,
                "city": 'austin-tx',
                "time-zone": 'America/Chicago'
            }

            # Generate a random reservation time
            time_slots = ["11:00", "11:30", "12:00", "12:30", "13:00", "13:30", "14:00", "14:30", "17:00", "17:30", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30"]
            request["time"] = random.choice(time_slots)

            # Generate a random duration
            duration_slots = [0.5, 1, 1.5, 2, 2.5, 3]
            request["duration"] = random.choice(duration_slots)

            # Set a random travel buffer
            request["travel-buffer"] = 0.15

            requests.append(request)

    return requests



if __name__ == "__main__":
    asyncio.run(main())