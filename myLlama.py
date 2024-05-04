import ollama as o
import base64
#chat func
def chat(user_msg,stream=True):
    messages = [
    {
        'role': 'user',
        'content': user_msg,
    },
    ]

    for part in o.chat('llama3', messages=messages, stream=stream):
        print(part['message']['content'], end='', flush=True)

    # end with a newline
    print()

#generate func
def generate(prompt,stream=True,format=None):
    if format is None:
        for part in o.generate('llama3', prompt, stream=stream):
            print(part['response'], end='', flush=True)
    else:
        response=o.generate('llama3', prompt, stream=stream,format=format)
        print(response['response'])

#generate with image func
def generate_w_images(prompt,images,stream=True):
    for response in o.generate('llava', prompt, images=images, stream=stream):
        print(response['response'], end='', flush=True)
    print()

# agent class framework
class Agent:
    def __init__(self,system_prompt = 'You are a helpful chat based assistant'):
        self.system_prompt = system_prompt
        self.messages=[
    {
        'role': 'system',
        'content': system_prompt,
    },
    ]
    #chat with agent and continue conversation
    def chat(self,user_msg,stream=True):
        self.messages.append(
        {
            'role': 'user',
            'content': user_msg,
        })
        msg_temp=''
        for part in o.chat('llama3', messages=self.messages, stream=stream):
            print(part['message']['content'], end='', flush=True)
            msg_temp+=part['message']['content']

        # end with a newline
        print()

        self.messages.append(
            {
            'role': 'assistant',
            'content': msg_temp,
        })
