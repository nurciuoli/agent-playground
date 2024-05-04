import base64
import json
import time
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
import os
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO
from agents.myLlama import generate
from agents.myLlama import Agent as LAgent
from agents.myGemini import Agent as GAgent

# Initialize OpenAI client using the API key from .env file
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()


# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
  

  # Custom function to request help on multiple tasks
# Args:
# worker - The worker instance tied to the current task
# tasks - A list of tasks to get help with
def get_help(task):
    try:
        agi = LAgent()
        help_response = generate(task['instructions'])
        #print(help_response)
        full_filepath = 'sandbox/' + task['output_file']
        with open(full_filepath, "w") as file:  # Use "w" for writing only
            file.write(help_response)  # Write the string directly
    except Exception as e:
        print(e)
def get_review(files):
    try:
        agi = GAgent()
        response = agi.review_content(files)
        return response
    except Exception as e:
        print(e)
    

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
def go_through_tool_actions(tool_calls, run_id, thread_id):
    tool_output_list = []
    for tool_call in tool_calls:
        function_name = json.loads(tool_call.json())['function']['name']
        print('...')
        print(function_name)
        print('...')
        #print(json.loads(json.loads(tool_call.json())['function']['arguments']))
        if function_name == 'plan_and_execute':
            tasks =json.loads(json.loads(tool_call.json())['function']['arguments'])['tasks']
            for task in tasks:
                print(task['instructions'])
                print(task['output_file'])
                get_help(task)
            tool_output_list.append({"tool_call_id": tool_call.id,"output": "it is done"})

        elif function_name=='get_review':
            files = json.loads(json.loads(tool_call.json())['function']['arguments'])['files']
            contents=[]
            for filep in files:
                full_path = 'sandbox/'+filep['file_name_with_ext']
                with open(full_path, "r") as file:
                    content = file.read()
                    full_content = "You are a helpful peer reviewer, look through the following comments and files and offer your feedback"+filep['content']+content
                    contents.append({filep['file_name_with_ext']:full_content})
            response =get_review(str(contents))
            tool_output_list.append({"tool_call_id": tool_call.id,"output": response})

        elif function_name=='get_second_opinion':
            args = json.loads(json.loads(tool_call.json())['function']['arguments'])
            print(args)
            tool_output_list.append({"tool_call_id": tool_call.id,"output": "yep, rip it"})
            
    # Submit the collected tool outputs and return the run object
    run = client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id, run_id=run_id, tool_outputs=tool_output_list)
    return run