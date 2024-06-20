import json
import os
import time

from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Access environment variables
API_KEY = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=API_KEY)

ASSISTANT_ID = os.getenv('REQUEST_ASSISTANT_ID')

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
    run = submit_message(ASSISTANT_ID, thread, user_input)
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

def get_request(desc):
    current_date = datetime.now().strftime("%B %d, %Y")
    # Create the string
    prompt = desc + f" Today is {current_date}"

    # Emulating concurrent user requests
    thread1, run1 = create_thread_and_run(f'''{prompt}''')

    # Now all Runs are executing...

    run1 = wait_on_run(run1, thread1)
    response = get_response(thread1)

    return json.loads(pretty_print(response))




prompt = "Can you reserve a dinner spot at Odd Duck for me an my wife on Saturday? I would like to spend an hour and a half there."

# print(get_request(prompt))