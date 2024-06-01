import os
import time

from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access environment variables
API_KEY = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=API_KEY)

MATH_ASSISTANT_ID = "asst_G84aUDrfAoOcU7J1XOI3tco3"  # or a hard-coded ID like "asst-..."

def submit_message(assistant_id, thread, user_message):
    client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=user_message
    )
    return client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
    )

def get_response(thread):
    return client.beta.threads.messages.list(thread_id=thread.id, order="asc")


def create_thread_and_run(user_input):
    thread = client.beta.threads.create()
    run = submit_message(MATH_ASSISTANT_ID, thread, user_input)
    return thread, run

# Pretty printing helper
def pretty_print(messages):
    print("# Response")
    result = ''
    for m in messages:
        if m.role == 'assistant':
            print(f"{m.content[0].text.value}")
            result = m.content[0].text.value
    print()
    return result


# Waiting in a loop
def wait_on_run(run, thread):
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run



# Emulating concurrent user requests
thread1, run1 = create_thread_and_run(
    '''Parking In the Back After 5:30. Make a note of Parking Signs and Times. No Parking in the Sherman Williams portion of the Parking Lot. Alternative Street Parking if the parking lot is full.

For a private room, please send an email to linasianbar.reservations@gmail.com.  Please include your Name, Phone Number, Amount of People, Day, Time, and Occasion.  Lin Asian Bar representative will contact you to assist your request further.  The maximum capacity is 14 people.

CANCELLATION POLICY: While you won't be charged if you need to cancel, we ask that you do so at least 12 hours in advance.  Please consider your schedule carefully and plan accordingly before making a reservation. 

By making a reservation, you agree to abide by these rules.  Thank you for understanding

Reservation times do not equal the time you will be seated.  Seating delays may happen based on table availability.
Read less
About Lin Asian Bar + Dim Sum
At Lin Asian Bar + Dim Sum, chef Ling Qi Wu serves traditional Chinese cuisine, but with a focus on fresh, organic produce. Dim sum is her specialty, the most extensive selection of which is available at Sunday brunch. Her menu extends to appetizers like grilled char siu, entrees like salt-and-pepper double lobster tail, and plenty more. Decked in colorful red lanterns, the restaurant features an open kitchen and a dim sum counter, so guests can interact with the chef while she’s doing her thing.'''
)

# Now all Runs are executing...

run1 = wait_on_run(run1, thread1)
pretty_print(get_response(thread1))
