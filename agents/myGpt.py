#main worker class

import json
import time
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
import os
from agents.agent_utils import go_through_run_steps,go_through_tool_actions


# Load environment variables
load_dotenv()

# Initialize OpenAI client using the API key from .env file
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()

# Define worker roles and associated contexts and tools
worker_selection = {
    "SoftwareEngineer": {
        "role_context": 'You are a powerful coding assistant',
        "tools": [{"type": "code_interpreter"}]
    },
    "Writer": {
        "role_context": 'You are a insight writing assistant',
        "tools": None
    }
}

# Define models
models = {
    'gpt3': "gpt-3.5-turbo-1106",
    'gpt4': "gpt-4-1106-preview"
}


def show_json(obj):
    # Print the JSON representation of a model
    print(json.loads(obj.model_dump_json()))


# Function to manage file uploads and return the full paths of the uploaded files
# Args:
# files_data - A list of file data dictionaries containing keys 'file_name_with_extension' and 'content'
def file_manager(files_data):
    full_file_paths = []
    for file_data in files_data:
        bin_full_path = 'test/' + file_data['file_name_with_extension']
        with open(bin_full_path, "wb") as file:
            file.write(bytes(file_data['content'], 'utf-8'))
        full_file_paths.append(bin_full_path)
    return add_file_ids(full_file_paths)


# Function to handle waiting for a response from an OpenAI run
# and processing the result
# Args:
# worker - The worker instance tied to the current task
# run - The specific run instance to wait on
# thread_id - The thread ID associated with the run
# print_flag - If True, prints the run steps; defaults to True
def wait_on_run(worker, run, thread_id, print_flag=True):
    while run.status in ["queued", "in_progress"]:
        # Retrieve updated run status
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

        # Handle completed run
        if run.status == 'completed':
            # Retrieve and process the run steps
            worker.run_steps = client.beta.threads.runs.steps.list(thread_id=thread_id, run_id=run.id, order="asc")
            go_through_run_steps(worker.run_steps, thread_id, print_flag)
            break
        # Handle run that requires action
        elif run.status == 'requires_action':
            # Get the tool calls that require action
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            # Process tool actions
            run = go_through_tool_actions(tool_calls, run.id, thread_id)

        # Sleep briefly to avoid spamming the API with requests
        time.sleep(0.1)

    # Update the worker's run attribute
    worker.run = run
    return run

# Function to add a list of file IDs for given file_names
# Args:
# file_names - A list of file names to register with the OpenAI client
def add_file_ids(file_names):
    files = {}
    for file_name in file_names:
        file = client.files.create(file=open(file_name, "rb"), purpose='assistants')
        files[str(file.id)] = file_name
    return files

# Function to retrieve all responses in a thread
# Args:
# thread_id - The thread ID to retrieve messages for
def get_response(thread_id):
    return client.beta.threads.messages.list(thread_id=thread_id, order="asc")



# Worker class definition with methods for interaction and management
class Agent:
    def __init__(self, name='MyAgent', role_context=None, model="gpt-3.5-turbo-1106", **kwargs):
        assistant_kwargs = {
            'name': name,
            'instructions': role_context,
            'model': model
        }
        # Add any additional kwargs passed to the constructor
        assistant_kwargs.update(kwargs)
        # Create an assistant with the specified properties
        self.assistant = client.beta.assistants.create(**assistant_kwargs)
        self.thread = None
        self.run = None
        self.name = name
        self.role_context = role_context
        self.tools = kwargs.get('tools')  # Save tools if provided
        self.model = model
        self.thread_id = ''
        self.uploaded_files = {}  # Initialize an empty dict for uploaded files

    def __str__(self):
        # Represent the Worker as a string
        return f"Worker(Name: {self.name}, Role Context: {self.role_context})"

    def chat(self, user_input):
        # Create a new thread and submit a message
        if self.thread is None:
            self.thread = client.beta.threads.create()
            self.thread_id = self.thread.id
        self.submit_message(self.thread_id, user_input)

    # Internal method for submitting messages, printing prompts, and waiting for responses
    def submit_message(self, thread_id, user_message):
        #print('===============================================================')
        #print('                             PROMPT')
        #print('===============================================================')
        #print(user_message)

        # Create a message and run thread
        client.beta.threads.messages.create(
            thread_id=thread_id, role="user", content=user_message
        )
        self.run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant.id,
        )

        # Wait for the run to complete
        self.run = wait_on_run(self, self.run, thread_id)
        # Retrieve the response
        self.response = get_response(thread_id)

    def upload_file_to_assistant(self, file_names):
        # Upload files to the assistant and update the uploaded files dictionary
        file_ids = add_file_ids(file_names)
        self.uploaded_files.update(file_ids)
        client.beta.assistants.update(self.assistant.id, file_ids=list(file_ids.keys()))