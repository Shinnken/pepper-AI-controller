from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
import logfire
import qi
import sys
from SoundReciver import SoundReceiverModule
from audio_soundprocessing import SoundProcessingModule
import speech_recognition as sr
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

r = sr.Recognizer() 


# Connect to the robot fails at app.start() => RuntimeError: disconnected
app = qi.Application(sys.argv, url="tcps://192.168.1.110:9503")
logins = ("nao", "nao")
factory = AuthenticatorFactory(*logins)
app.session.setClientAuthenticatorFactory(factory)
app.start()
print("started")



module_name = "SoundReceiverModule"
sound_module_instance = SoundReceiverModule(app.session, name=module_name)


service_id = app.session.registerService(module_name, sound_module_instance)
print(f"SoundReceiver module registered with ID: {service_id}")

print("Services available:")
txt = app.session.services()
with open("demofile.txt", "w") as f:
    for service in txt:
        # print(service)
        f.write(str(service) + "\n")


sound_module_instance.start()
print("SoundReceiver module started.")



tts = app.session.service("ALTextToSpeech")


tts.setLanguage("Polish")


def main():

    sleep(2)  # Allow some time for the module to start
    print("Robot: ", type(sound_module_instance.getBuffer()))
    print("Robot: ", sound_module_instance.buffer)
    tts.say("Cześć, jestem robotem!")



if __name__ == "__main__":
    main()