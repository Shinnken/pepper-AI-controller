from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
import qi
import sys



# logfire.configure(console=False)
# logfire.instrument_pydantic_ai()


class Authenticator:

    def __init__(self, username, password):
        self.username = username
        self.password = password

    # This method is expected by libqi and must return a dictionary containing
    # login information with the keys 'user' and 'token'.
    def initialAuthData(self):
        return {'user': self.username, 'token': self.password}


class AuthenticatorFactory:

    def __init__(self, username, password):
        self.username = username
        self.password = password

    # This method is expected by libqi and must return an object with at least
    # the `initialAuthData` method.
    def newAuthenticator(self):
        return Authenticator(self.username, self.password)


# Connect to the robot fails at app.start() => RuntimeError: disconnected
app = qi.Application(sys.argv, url="tcps://192.168.1.110:9503")
logins = ("nao", "nao")
factory = AuthenticatorFactory(*logins)
app.session.setClientAuthenticatorFactory(factory)
app.start()


tts = app.session.service("ALTextToSpeech")
motion_service = app.session.service("ALMotion")
posture_service = app.session.service("ALRobotPosture")


tts.setLanguage("Polish")



def load_system_message():
    """Load system message from .prompt file"""
    with open('system_message.prompt', 'r', encoding='utf-8') as f:
        return f.read().strip()

def trim_history(messages, max_size=6):
    """Keep system message + last max_size conversation messages"""
    if len(messages) <= max_size:
        return messages
    
    # Zachowaj pierwszą wiadomość (zawiera system prompt) + ostatnie (max_size-1) wiadomości
    return [messages[0]] + messages[-(max_size-1):]

def main():
    print("zaczynamy")
    # Wake up robot
    motion_service.wakeUp()
    print("idziemy dalej")
    # Send robot to Stand Zero
    posture_service.goToPosture("StandZero", 0.5)
    print("i jeszcze dalej")
    posture_service.goToPosture("StandInit", 0.5)

    tts.say("Witajcie mordeczki!")
    # Load system prompt from file
    system_prompt = load_system_message()

    ollama_model = OpenAIModel(
        model_name='SpeakLeash/bielik-11b-v2.3-instruct:Q4_K_M', provider=OpenAIProvider(base_url='http://localhost:11434/v1')
    )
    # Create agent with Ollama model
    agent = Agent(
        ollama_model,
        system_prompt=system_prompt
    )
    
    # Initialize message history
    message_history = []
    
    print("Chatbot uruchomiony!")
    
    # Main chat loop
    while True:
        user_input = input("Ty: ")
        # Trim history to keep only last 8 messages
        message_history = trim_history(message_history)
        
        # Run agent with current input and history
        result = agent.run_sync(
            user_input,
            message_history=message_history
        )

        # Print bot response
        print("Bot:", result.output)
        tts.say(result.output)
        
        # Add new messages to history
        message_history.extend(result.new_messages())

if __name__ == "__main__":
    main()