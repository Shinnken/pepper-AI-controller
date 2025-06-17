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


#app = qi.Application(sys.argv, url="tcps://192.168.242.133:9503")
app = qi.Application(sys.argv, url="tcps://192.168.1.110:9503")
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

speech_service = app.session.service("ALTextToSpeech")
speech_service.setLanguage("Polish")
speech_service.setParameter("speed", 200)
tts = app.session.service("ALAnimatedSpeech")
motion_service = app.session.service("ALMotion")

sound_module_instance = SoundReceiverModule(app.session, name="SoundProcessingModule", thresholdRMSEnergy = 0.03)
service_id = app.session.registerService("SoundProcessingModule", sound_module_instance)
sleep(1)  # Give some time for the module to register

sound_module_instance.start()

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


def delete_subs(name):
    all_subscribers = app.session.service("ALVideoDevice").getSubscribers()
    sub_to_delete = [subscriber for subscriber in all_subscribers if unicode(name, "utf-8") in unicode(subscriber, "utf-8")] # type: ignore
    for sub in sub_to_delete:
        app.session.service("ALVideoDevice").unsubscribe(sub)


async def main():
    print("Start")
    #motion_service.moveTo(0.5, 0.0, 0.0)  # move forward 0.5 m
    motion_service.moveTo(0.0, 0.0, 1.5708)  # rotate 1.5708 rad (≈90°)
    #frame_data = self.session.service("ALVideoDevice").getImageRemote(self.vid_handle) # get frame

    agent = init_agent(motion_service)

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

        llm_response = await generate_and_say_response(agent, user_input, message_history, tts)

        print()  # Add newline after streaming
        message_history.extend(llm_response)


if __name__ == "__main__":
    asyncio.run(main())
