#main worker class

import json
import time
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
import os#worker hanlding

import json
import os
import time
from dotenv import load_dotenv
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO


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
            run = go_through_tool_actions(tool_calls, worker, run.id, thread_id, True)

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

# Custom function to request help on multiple tasks
# Args:
# worker - The worker instance tied to the current task
# tasks - A list of tasks to get help with
def get_help(worker, tasks):
    help_responses = worker.submit_messages_multiple(tasks)
    return help_responses

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

# Function to process run steps and handle different types of outputs
# Args:
# run_steps - The run steps to process
# thread_id - The thread ID associated with the run
# print_flag - If True, prints details of the steps; defaults to True
def go_through_run_steps(run_steps, thread_id, print_flag):
    for step in run_steps.data:
        step_details = step.step_details
        # Different output handling based on output type
        if json.loads(step_details.json())['type'] != 'message_creation':
            for toolcalls in json.loads(step_details.json())['tool_calls']:
                if toolcalls['type'] == 'code_interpreter':
                    if print_flag:
                        print('===============================================================')
                        print('                        CODE INTERPRETER')
                        print('===============================================================')
                        print('Input: ' + toolcalls['code_interpreter']['input'])
                        for output in toolcalls['code_interpreter']['outputs']:
                            output_type = output['type']
                            if output_type == 'image':
                                # Display image output
                                file = client.files.content(output[output_type]['file_id'])
                                image_file = BytesIO(file.content)
                                image = Image.open(image_file)
                                plt.imshow(image)
                                plt.show()
                            if output_type == 'logs':
                                # Display logs
                                print(output[output_type])
                        print('\n')
        else:
            try:
                cur_message_id = json.loads(step_details.json())['message_creation']['message_id']
                if(json.loads(client.beta.threads.messages.retrieve(message_id=cur_message_id,thread_id=thread_id).json())['content'][0]['text']['value']!=''):
                    if(print_flag==True):
                        #print('===============================================================')
                        #print('                       ASSISTANT MESSSAGES')
                        #print('===============================================================')
                        print(json.loads(client.beta.threads.messages.retrieve(message_id=cur_message_id,thread_id=thread_id).json())['content'][0]['text']['value'])
                        #print('\n')
            except Exception as e:
                pass

# Function to handle action-required tool calls and return the updated run object
# Args:
# tool_calls - The tool calls that require action
# worker - The worker instance tied to the current task
# run_id - The run ID associated with the tool actions
# thread_id - The thread ID associated with the run
# print_flag - If True, prints details of the tool actions; defaults to True
def go_through_tool_actions(tool_calls, worker, run_id, thread_id, print_flag):
    tool_output_list = []
    for tool_call in tool_calls:
        function_name = json.loads(tool_call.json())['function']['name']
        if function_name == 'get_help':
            if print_flag:
                print('===============================================================')
                print('                         GETTING HELP')
                print('===============================================================')
            tasks =json.loads(json.loads(tool_call.json())['function']['arguments'])['tasks']
            help_resp = get_help(worker, tasks)
            for task in tasks:
                print(task['instructions'])
            tool_output_list.append({"tool_call_id": tool_call.id,"output": str(help_resp)})
        elif function_name == 'file_upload':
            if print_flag:
                print('===============================================================')
                print('                          FILE MANAGER')
                print('===============================================================')
            files =json.loads(json.loads(tool_call.json())['function']['arguments'])['files']
            file_dict = file_manager(files)
            file_ids = list(file_dict.keys())
            client.beta.assistants.update(assistant_id=worker.assistant.id, file_ids=file_ids)
            for file in list(file_dict.values()):
                print('-' + file)
            tool_output_list.append({"tool_call_id": tool_call.id,"output": 'The files have been uploaded and you can access them'})
        elif function_name == 'post_plan':
            tool_output_string = ''
            if print_flag:
                print('===============================================================')
                print('                               PLAN')
                print('===============================================================')
            tasks = json.loads(json.loads(tool_call.json())['function']['arguments'])['tasks']
            for i, task in enumerate(tasks):
                tool_output_string += str(i + 1) + ':'
                tool_output_string += task['details']
                tool_output_string += ' \n'
            print(tool_output_string)
            tool_output_list.append({"tool_call_id": tool_call.id,"output": tool_output_string})
    # Submit the collected tool outputs and return the run object
    run = client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id, run_id=run_id, tool_outputs=tool_output_list)
    return run

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