import asyncio
import qi
import sys
import random
from SoundReciver import SoundReceiverModule
from LLM_and_saying import generate_and_say_response, trim_history, init_agent
from time import sleep


# inne parametry dla nao i peppera, sprawdzić w developer guidzie
CAMERA_INDEX = 0
RESOLUTION_INDEX = 2
COLORSPACE_INDEX = 11
FRAMERATE = 15
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


#app = qi.Application(sys.argv, url="tcps://192.168.1.110:9503")    # Pepper
app = qi.Application(sys.argv, url="tcps://192.168.1.104:9503")    # Nao
# delete_subs("kamera") # needed for camera initialization
# self.vid_handle = self.session.service("ALVideoDevice").subscribeCamera(
#     "kamera",
#     CAMERA_INDEX,
#     RESOLUTION_INDEX,
#     COLORSPACE_INDEX,
#     FRAMERATE
#
# )
logins = ("nao", "nao")
factory = AuthenticatorFactory(*logins)
app.session.setClientAuthenticatorFactory(factory)
app.start()

app.session.service("ALTextToSpeech").setLanguage("Polish")
tts = app.session.service("ALAnimatedSpeech")
motion_service = app.session.service("ALMotion")
posture_service = app.session.service("ALRobotPosture")

sound_module_instance = SoundReceiverModule(app.session, name="SoundProcessingModule", thresholdRMSEnergy = 0.03)
app.session.registerService("SoundProcessingModule", sound_module_instance)
sleep(1)  # Give some time for the module to register
sound_module_instance.start()

def delete_subs(name):
    all_subscribers = app.session.service("ALVideoDevice").getSubscribers()
    sub_to_delete = [subscriber for subscriber in all_subscribers if unicode(name, "utf-8") in unicode(subscriber, "utf-8")] # type: ignore
    for sub in sub_to_delete:
        app.session.service("ALVideoDevice").unsubscribe(sub)


async def main():
    print("Start")
    agent = init_agent(motion_service, video_service=None, video_handle=None, prompt_name="Tarnowski", language="Polski")

    # Initialize message history
    message_history = []

    # Main chat loop
    while True:
        # Listening
        sound_module_instance.setListening()
        if sound_module_instance.stt_output:
            user_input = sound_module_instance.stt_output
            sound_module_instance.stt_output = None
            sound_module_instance.setNotListening()
        else:
            continue

        # Trim history to keep only last 8 messages
        message_history = trim_history(message_history)

        llm_response = await generate_and_say_response(agent, user_input, message_history, tts, sound_module_instance)

        print()  # Add newline after streaming
        message_history.extend(llm_response)


if __name__ == "__main__":
    asyncio.run(main())
