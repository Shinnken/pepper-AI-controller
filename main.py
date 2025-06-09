from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
import logfire
import qi
import sys
from SoundReciver import SoundReceiverModule
from audio_soundprocessing import SoundProcessingModule
import speech_recognition as sr
from time import sleep, time
from threading import Thread



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

r = sr.Recognizer() 


# Connect to the robot fails at app.start() => RuntimeError: disconnected
app = qi.Application(sys.argv, url="tcps://192.168.1.110:9503")
logins = ("nao", "nao")
factory = AuthenticatorFactory(*logins)
app.session.setClientAuthenticatorFactory(factory)
app.start()
print("started")

# Start recording from the robot's microphones
# app.session.service("ALAudioDevice").startMicrophonesRecording("/home/nao/test.wav", "wav", 16000, 0)
# print("Microphone recording started.")
# sleep(3)  # Allow some time for the recording to start
# app.session.service("ALAudioDevice").stopMicrophonesRecording()
# print("Microphone recording stopped.")

module_name = "SoundReceiverModule"
sound_module_instance = SoundReceiverModule(app.session, name=module_name)
sound_processing_instance = SoundProcessingModule(app, name=module_name) 


service_id = app.session.registerService(module_name, sound_processing_instance)
print(f"SoundReceiver module registered with ID: {service_id}")


print("Services available:")
txt = app.session.services()
with open("demofile.txt", "w") as f:
    for service in txt:
        # print(service)
        f.write(str(service) + "\n")


audio_thread = Thread(target=sound_processing_instance.startProcessing)
audio_thread.start()
print("SoundProcessing module started.")



tts = app.session.service("ALTextToSpeech")


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
        sleep(0.5)  # Small delay to avoid busy-waiting
        # Get user input
        audio_bytearray = sound_processing_instance.getBuffer()
        # print("Audio type:", type(audio))

        print("Oczekiwanie na dane audio...")
        print(time())
        # audio = sr.AudioData(audio_bytearray, 16000, 2)

        # user_input = r.recognize_google(audio, language='pl-PL', pfilter=1)

        continue

        # Trim history to keep only last 8 messages
        message_history = trim_history(message_history)
        
        # Run agent with current input and history
        result = agent.run_sync(
            user_input,
            message_history=message_history
        )

        if audio is None:
            print("Brak danych audio. Spróbuj ponownie.")
            continue

        # Print bot response
        print("Bot:", result.output)
        tts.say(result.output)
        
        # Add new messages to history
        message_history.extend(result.new_messages())

if __name__ == "__main__":
    main()