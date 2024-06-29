import os

from seleniumbase import SB
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def click_time_button(target_time, url, type):
    with SB(uc=True, demo=False) as sb:
        # Open the URL
        sb.open(url)

        # Sleep to ensure the page loads completely
        sb.sleep(1)

        # Click the login button
        sb.click('button.Button--login')

        # Locate the "Use Email and Password instead" button by its text and click it
        sb.click('button:contains("Use Email and Password instead")')

        # Fill in the login form fields
        sb.type('#email', os.getenv('RESY_EMAIL'))
        sb.type('#password', os.getenv('RESY_PASSWORD'))

        # Submit the form
        sb.click('button.Button--primary.Button--lg')

        sb.sleep(3)
        sb.refresh()

        sb.sleep(1)

        # Locate all reservation buttons
        buttons = sb.find_elements(By.CSS_SELECTOR, "button.ReservationButton")

        print(f"Found {len(buttons)} buttons")
        print(f"Looking for {target_time} and {type}")

        # Loop through each button and find the one with the matching time
        for button in buttons:
            time_element = button.find_element(By.CSS_SELECTOR, "div.ReservationButton__time")
            type_element = button.find_element(By.CSS_SELECTOR, "div.ReservationButton__type")
            button_time = time_element.text.strip()
            reservation_type = type_element.text.strip()

            print(button_time + " " + reservation_type)

            # Convert button_time to military format for comparison
            button_time_military = convert_to_military(button_time)

            if button_time_military == target_time:
                if reservation_type != type and type != '':
                    continue

                # Scroll the button into view
                sb.execute_script("arguments[0].scrollIntoView();", button)

                # Add a small delay before clicking
                sb.sleep(1)

                # Click the button using JavaScript to ensure it's clicked correctly
                sb.execute_script("arguments[0].click();", button)

                print(f"Clicked on the button with time: {button_time} and type: {reservation_type}")
                break
        else:
            print(f"No button found with the time: {target_time}")

        sb.sleep(10)

def convert_to_military(time_str):
    import datetime
    # Convert time string (e.g., "5:00 PM") to military time (e.g., "17:00:00")
    dt = datetime.datetime.strptime(time_str, "%I:%M %p")
    return dt.strftime("%H:%M:%S")

# Example usage:
# click_time_button("17:00:00", "https://resy.com/cities/austin-tx/venues/odd-duck?date=2024-06-25&seats=2", "Dining Room")