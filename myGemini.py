import google.generativeai as genai
# agent class framework
class Agent:
    def __init__(self,model='gemini-1.0-pro-latest',tools=None):
        self.response=None
        self.messages=None
        self.tools=tools
        try:
            if self.tools is not None:
                self.model=genai.GenerativeModel(model,tools=tools)
            else:
                self.model=genai.GenerativeModel(model)
        except:
            print('nope')

    def generate(self,user_msg):
        self.response = self.model.generate_content(user_msg)
        print(self.response.text)

    def chat(self,user_msg,auto_funct_call=False):
        if self.messages is None:
            self.messages=[]
            self.thread=self.model.start_chat(history=self.messages,enable_automatic_function_calling=auto_funct_call)
        self.response=self.thread.send_message([user_msg])
        print(self.response.text)
    