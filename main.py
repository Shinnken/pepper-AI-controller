from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
import asyncio
import qi
import sys
import random


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


app = qi.Application(sys.argv, url="tcps://192.168.1.110:9503")
logins = ("nao", "nao")
factory = AuthenticatorFactory(*logins)
app.session.setClientAuthenticatorFactory(factory)
app.start()

# tts = app.session.service("ALTextToSpeech")
# tts.setLanguage("Polish")

tts = app.session.service("ALAnimatedSpeech")
motion_service = app.session.service("ALMotion")
posture_service = app.session.service("ALRobotPosture")


animations = [
    "^start(animations/Stand/Gestures/Hey_1)",
    "^start(animations/Stand/Gestures/Hey_2)",
    "^start(animations/Stand/Gestures/Hey_3)",
    "^start(animations/Stand/Gestures/Enthusiastic_1)",
    "^start(animations/Stand/Gestures/Enthusiastic_2)",
    "^start(animations/Stand/Gestures/Enthusiastic_3)",
    "^start(animations/Stand/Gestures/Enthusiastic_4)",
    "^start(animations/Stand/Gestures/BodyTalk_1)",
    "^start(animations/Stand/Gestures/BodyTalk_2)",
    "^start(animations/Stand/Gestures/BodyTalk_3)",
    "^start(animations/Stand/Gestures/BodyTalk_4)",
]
def load_system_message():
    """Load system message from .prompt file"""
    with open('system_message.prompt', 'r', encoding='utf-8') as f:
        return f.read().strip()


def trim_history(messages, max_size=6):
    """Keep system message + last max_size conversation messages"""
    if len(messages) <= max_size:
        return messages

    # Zachowaj pierwszą wiadomość (zawiera system prompt) + ostatnie (max_size-1) wiadomości
    return [messages[0]] + messages[-(max_size - 1):]


def moveHands(motion_service):
    # Arms motion from user have always the priority than walk arms motion
    JointNames = ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "RShoulderPitch"]
    deg_to_rad = 0.017453
    Arm1 = [40, 25, -35, -40, 80]
    Arm1 = [x * deg_to_rad for x in Arm1]

    Arm2 = [-10, 50, -80, -80, 10]
    Arm2 = [x * deg_to_rad for x in Arm2]

    pFractionMaxSpeed = 0.5

    motion_service.angleInterpolationWithSpeed(JointNames, Arm1, pFractionMaxSpeed)
    motion_service.angleInterpolationWithSpeed(JointNames, Arm2, pFractionMaxSpeed)
    motion_service.angleInterpolationWithSpeed(JointNames, Arm1, pFractionMaxSpeed)


def moveFingers(motion_service):
    # Arms motion from user have always the priority than walk arms motion
    JointNames = ["LHand", "RHand", "LWristYaw", "RWristYaw"]
    deg_to_rad = 0.017453
    Arm1 = [0, 0, 0, 0]
    Arm1 = [x * deg_to_rad for x in Arm1]

    Arm2 = [50, 50, 0, 0]
    Arm2 = [x * deg_to_rad for x in Arm2]

    pFractionMaxSpeed = 0.8

    motion_service.angleInterpolationWithSpeed(JointNames, Arm1, pFractionMaxSpeed)
    motion_service.angleInterpolationWithSpeed(JointNames, Arm2, pFractionMaxSpeed)
    motion_service.angleInterpolationWithSpeed(JointNames, Arm1, pFractionMaxSpeed)


async def main():
    print("zaczynamy")
    # Wake up robot
    # motion_service.wakeUp()

    # motion_service.rest()

    # Load system prompt from file
    system_prompt = load_system_message()

    ollama_model = OpenAIModel(
        model_name='SpeakLeash/bielik-11b-v2.3-instruct:Q4_K_M',
        provider=OpenAIProvider(base_url='http://localhost:11434/v1')
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

        # Stream response
        tts.say(random.choice(animations))
        full_response = ""
        word_buffer = ""

        async with agent.run_stream(user_input, message_history=message_history) as result:
            async for token in result.stream_text(delta=True):
                print(token, end='', flush=True)
                full_response += token
                word_buffer += token
                
                if ' ' in token or '\n' in token or any(char in token for char in '.,!?;:'):
                    if word_buffer.strip():
                        tts.say(word_buffer.strip())
                    word_buffer = ""

            # Handle remaining word in buffer
            if word_buffer.strip():
                tts.say(word_buffer.strip())

            print()  # Add newline after streaming
            message_history.extend(result.new_messages())


if __name__ == "__main__":
    asyncio.run(main())
