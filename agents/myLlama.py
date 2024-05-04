import ollama as o
import base64
#chat func
def chat(user_msg):
    messages = [
    {
        'role': 'user',
        'content': user_msg,
    },
    ]

    response=o.chat('llama3', messages=messages, stream=False)
    return response

#generate func
def generate(prompt,format=None):
    response = o.generate('llama3', prompt, stream=False)
    return response['response']

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
    def chat(self,user_msg):
        self.messages.append(
        {
            'role': 'user',
            'content': user_msg,
        })
        response=o.chat('llama3', messages=self.messages, stream=False)
        return response['message']['content']
