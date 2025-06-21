import asyncio
import qi
import sys
from SoundReciver import SoundReceiverModule
from LLM_and_saying import LLMAndSaying
from robot_auth import AuthenticatorFactory
from camera import delete_subs
from robot_action_logic import execute_robot_task
from time import sleep

# inne parametry dla nao i peppera, sprawdzić w developer guidzie
CAMERA_INDEX = 0
RESOLUTION_INDEX = 3
COLORSPACE_INDEX = 11
FRAMERATE = 5

LANGUAGE = "Polski"
#LANGUAGE = "English"

app = qi.Application(sys.argv, url="tcps://192.168.1.110:9503")  # Pepper
# app = qi.Application(sys.argv, url="tcps://192.168.1.104:9503")    # Nao

logins = ("nao", "nao")
factory = AuthenticatorFactory(*logins)
app.session.setClientAuthenticatorFactory(factory)
app.start()

# app.session.service("ALAutonomousLife").setState("disabled")  # Disable autonomous life to prevent interruptions
# sleep(3)  # Wait for the service to be ready
app.session.service("ALMotion").wakeUp()  # Wake up the robot
app.session.service("ALRobotPosture").goToPosture("StandInit", 0.5)  # Set initial posture

if LANGUAGE == "Polski":
    app.session.service("ALTextToSpeech").setLanguage("Polish")
elif LANGUAGE == "English":
    app.session.service("ALTextToSpeech").setLanguage("English")
tts = app.session.service("ALAnimatedSpeech")
motion_service = app.session.service("ALMotion")
video_service = app.session.service("ALVideoDevice")

video_service = delete_subs("kamera", app, video_service)  # needed for camera initialization
vid_handle = video_service.subscribeCamera(
    "kamera",
    CAMERA_INDEX,
    RESOLUTION_INDEX,
    COLORSPACE_INDEX,
    FRAMERATE

)

sound_module_instance = SoundReceiverModule(app.session, name="SoundProcessingModule", thresholdRMSEnergy=0.04)
app.session.registerService("SoundProcessingModule", sound_module_instance)
sleep(1)  # Give some time for the module to register
sound_module_instance.start()

agent_service = LLMAndSaying(motion_service, video_service, vid_handle, language=LANGUAGE)


async def main():
    print("Start")
    sound_module_instance.setListening()

    current_robot_task = None

    # Main command loop
    while True:
        # Accept new command only when no task is running
        if current_robot_task is None or current_robot_task.done():
            while sound_module_instance.stt_output is None:
                await asyncio.sleep(0.1)

            # Get command and clear buffer
            command = sound_module_instance.stt_output
            sound_module_instance.stt_output = None

            # Create robot task
            current_robot_task = asyncio.create_task(
                execute_robot_task(
                    command, sound_module_instance, agent_service,
                    tts, video_service, vid_handle
                )
            )
        else:
            # Wait before checking again
            await asyncio.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(main())