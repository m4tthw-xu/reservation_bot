import os
import time

from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access environment variables
API_KEY = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=API_KEY)

ASSISTANT_ID = os.getenv('ASSISTANT_ID')

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

def get_tags(desc):
    # Emulating concurrent user requests
    thread1, run1 = create_thread_and_run(f'''{desc}''')

    # Now all Runs are executing...

    run1 = wait_on_run(run1, thread1)
    return pretty_print(get_response(thread1))
