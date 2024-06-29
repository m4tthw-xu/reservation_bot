import asyncio
import random
import sys
from datetime import datetime, timedelta
import gcal_parse
import resy_scraper
import tagging_gpt
import db_manager
import restaurant_graph_visual
import request_gpt
import sb as sb

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox, \
    QFormLayout, QSpacerItem, QSizePolicy, QProgressBar
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer


class Worker(QObject):
    status_update = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    finished = pyqtSignal(object)
    browser_task = pyqtSignal(str)

    def __init__(self, requests):
        super().__init__()
        self.requests = requests

    def run(self):
        asyncio.run(self.process_requests())

    async def process_requests(self):
        total_steps = 8  # Define the total number of steps in your process
        current_step = 0

        for request in self.requests:
            current_step += 1
            self.status_update.emit(f'''Okay! I will look for {request['restaurant']} reservations at {request['time']}''')
            self.progress_update.emit(int(current_step / total_steps * 100))
            print(request)

            venue = db_manager.get_restaurant(request['restaurant'])
            if venue is None:
                raise ValueError(f"I'm sorry, but I can't find '{request['restaurant']}' in my database :(")

            current_step += 1
            self.status_update.emit(
                f"I'm now looking for the available reservation times at {request['restaurant']}...")
            self.progress_update.emit(int(current_step / total_steps * 100))

            link = venue['link']
            link = resy_scraper.update_url(link, request['date'], request['seats'])

            current_step += 1
            self.browser_task.emit(link)
            while not hasattr(self, 'times'):
                await asyncio.sleep(0.1)
            self.progress_update.emit(int(current_step / total_steps * 100))

            times = self.times
            del self.times

            date = request['date'].split('/')

            current_step += 1
            self.status_update.emit(f"I'm now looking at your calendar for a free spot...")
            unavailable_times = gcal_parse.get_events_on_day(
                int(date[2]), int(date[0]), int(date[1]), request['time-zone'])
            self.progress_update.emit(int(current_step / total_steps * 100))

            current_step += 1
            self.status_update.emit('''\n----------------------------\nPlease click on the "Reserve Now" button to confirm the reservation!!!\n----------------------------\n''')
            self.progress_update.emit(int(current_step / total_steps * 100))

            try:
                closest_reservation = find_closest_reservation(
                    request['date'], request['time'], float(request['duration']),
                    float(request['travel-buffer']), times, unavailable_times, request['restaurant'])

                times = extract_military_time(closest_reservation[len(closest_reservation) // 2])
                sb.click_time_button(times[0] + ":00", link, '')

                offset = timedelta(hours=5)

                adjusted_events = []
                for event in closest_reservation:
                    start_time = datetime.strptime(event[0], '%Y-%m-%dT%H:%M:%S%z') + offset
                    end_time = datetime.strptime(event[1], '%Y-%m-%dT%H:%M:%S%z') + offset
                    adjusted_events.append((start_time.isoformat(), end_time.isoformat(), event[2]))

                self.status_update.emit("Waiting for user confirmation...")
                current_step += 1
                self.progress_update.emit(int(current_step / total_steps * 100))

                self.finished.emit(adjusted_events)

                return

            except Exception as e:
                self.status_update.emit(f"An error occurred: {e}")
                print(f"An error occurred: {e}")
                self.finished.emit(None)
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

class ReservationApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Set a modern font
        font = QFont('Arial', 12)

        # Form layout to arrange input fields
        form_layout = QFormLayout()

        self.prompt_label = QLabel('''Hi! I'm your personal RESY assistant. How can I help?''')
        self.prompt_label.setFont(font)
        self.prompt_input = QTextEdit(self)  # Using QTextEdit instead of QLineEdit
        self.prompt_input.setFont(font)
        self.prompt_input.setFixedHeight(100)  # Set a fixed height for the text area

        form_layout.addRow(self.prompt_label)
        form_layout.addRow(self.prompt_input)

        layout.addLayout(form_layout)

        # Spacer item for spacing
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.status_label = QLabel('Status:')
        self.status_label.setFont(font)
        self.status_text = QTextEdit(self)
        self.status_text.setFont(font)
        self.status_text.setFixedHeight(150)
        self.status_text.setReadOnly(True)

        layout.addWidget(self.status_label)
        layout.addWidget(self.status_text)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.submit_button = QPushButton('Submit', self)
        self.submit_button.setFont(font)
        self.submit_button.setStyleSheet("QPushButton { padding: 10px 20px; }")
        self.submit_button.clicked.connect(self.on_submit)

        layout.addWidget(self.submit_button)

        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.setLayout(layout)
        self.setWindowTitle('Restaurant Reservation')
        self.setGeometry(100, 100, 400, 400)  # Adjust window size to accommodate larger text area and status window
        self.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress_bar)

    def on_submit(self):
        prompt = self.prompt_input.toPlainText()
        if not prompt.strip():
            QMessageBox.critical(self, 'Error', 'Prompt cannot be empty!')
            return

        self.status_text.clear()
        self.progress_bar.setValue(0)

        try:
            self.update_status("I am currently interpreting your request...\n")
            request = request_gpt.get_request(prompt)

            self.thread = QThread()
            self.worker = Worker([request])
            self.worker.moveToThread(self.thread)

            self.thread.started.connect(self.worker.run)
            self.worker.status_update.connect(self.update_status)
            self.worker.progress_update.connect(self.update_progress)
            self.worker.finished.connect(self.handle_confirmation)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.browser_task.connect(self.handle_browser_task)

            self.thread.start()

        except ValueError as ve:
            QMessageBox.critical(self, 'Error', str(ve))
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to process request: {str(e)}')
            return

    def handle_browser_task(self, link):
        # Run browser task in the main thread
        asyncio.run(self.perform_browser_task(link))

    async def perform_browser_task(self, link):
        times = await resy_scraper.scrape_reservation_buttons(link)
        self.worker.times = times

    def handle_confirmation(self, adjusted_events):
        if adjusted_events:
            reply = QMessageBox.question(self, 'Confirmation', 'Did you successfully make the reservation?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                gcal_parse.add_events_to_calendar(adjusted_events)
                self.update_status("Reservation added to calendar")
                self.update_progress(100)  # Ensure progress bar reaches 100%
                QMessageBox.information(self, 'Success', 'Reservation request processed!')
            else:
                self.update_status("Reservation was not successful.")
                QMessageBox.information(self, 'Info', 'Please try again.')
        else:
            self.update_status("No valid reservation found.")
            self.update_progress(100)  # Ensure progress bar reaches 100%

    def update_status(self, message):
        self.status_text.append(message)

    def update_progress(self, value):
        self.target_progress = value
        self.timer.start(10)  # Update progress bar every 10 ms

    def update_progress_bar(self):
        current_value = self.progress_bar.value()
        if current_value < self.target_progress:
            self.progress_bar.setValue(current_value + 1)
        else:
            self.timer.stop()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ReservationApp()
    sys.exit(app.exec_())