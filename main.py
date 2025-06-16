import time

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
import asyncio
import qi
import sys
import random
from SoundReciver import SoundReceiverModule
from time import sleep


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


app = qi.Application(sys.argv, url="tcps://192.168.242.133:9503")
logins = ("nao", "nao")
factory = AuthenticatorFactory(*logins)
app.session.setClientAuthenticatorFactory(factory)
app.start()



tts = app.session.service("ALAnimatedSpeech")
tts.setLanguage("Polish")
motion_service = app.session.service("ALMotion")

module_name = "SoundProcessingModule"
sound_module_instance = SoundReceiverModule(app.session, name=module_name)

service_id = app.session.registerService(module_name, sound_module_instance)
print(f"SoundProcessing module registered with ID: {service_id}")

sleep(1)  # Give some time for the module to register

sound_module_instance.start()
print("SoundProcessing module started.")


# tts = app.session.service("ALTextToSpeech")
# tts.setLanguage("Polish")

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


def grabGun(motion_service):
    # Arms motion from user have always the priority than walk arms motion
    JointNames = ["RShoulderPitch", "RElbowRoll", "RWristYaw", "RHand"]
    deg_to_rad = 0.017453
    Arm1 = [45, 45, 0, 20]
    Arm1 = [x * deg_to_rad for x in Arm1]
    Arm2 = [50, 50, 0, 20]
    Arm2 = [x * deg_to_rad for x in Arm2]

    pFractionMaxSpeed = 1.0

    motion_service.angleInterpolationWithSpeed(JointNames, Arm1, pFractionMaxSpeed)
    motion_service.angleInterpolationWithSpeed(JointNames, Arm2, pFractionMaxSpeed)


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

    # Load system prompt from file
    system_prompt = load_system_message()

    ollama_model = OpenAIModel(
        model_name='SpeakLeash/bielik-11b-v2.1-instruct:Q8_0',
        #model_name='SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0',
        #provider=OpenAIProvider(base_url='http://localhost:11434/v1')
        provider=OpenAIProvider(base_url='https://intent-possum-hardy.ngrok-free.app/v1')
    )
    # Create agent with Ollama model
    agent = Agent(
        ollama_model,
        system_prompt=system_prompt
    )

    # Initialize message history
    message_history = []

    # Main chat loop
    while True:
        # Listening
        sound_module_instance.setListening()
        if len(sound_module_instance.stt_output) > 0:
            user_input = sound_module_instance.stt_output
            sound_module_instance.stt_output = []
            sound_module_instance.setNotListening()
        else:
            continue
        # Trim history to keep only last 8 messages
        message_history = trim_history(message_history)

        # Stream response
        full_response = ""
        word_buffer = ""

        # Generating and saying response
        async with agent.run_stream(user_input, message_history=message_history) as result:
            #tts.say(random.choice(animations))
            async for token in result.stream_text(delta=True):
                print(token, end='', flush=True)
                full_response += token
                
                # If token starts with space and buffer has more than 1 character, speak it
                if token.startswith(' ') and len(word_buffer.strip()) > 1:
                    tts.say(word_buffer.strip())
                    word_buffer = token[1:]  # Start new word without space
                else:
                    word_buffer += token
            # Speak final word if any
            if word_buffer.strip():
                pass
                tts.say(word_buffer.strip())

            print()  # Add newline after streaming
            message_history.extend(result.new_messages())


if __name__ == "__main__":
    asyncio.run(main())
