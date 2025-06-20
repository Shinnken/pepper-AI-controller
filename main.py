import asyncio
import qi
import sys
from SoundReciver import SoundReceiverModule
from LLM_and_saying import generate_and_say_response, trim_history, init_agent
from robot_auth import AuthenticatorFactory
from motion import lookForward
from camera import take_picture, delete_subs
from time import sleep
from pydantic_ai import BinaryContent


# inne parametry dla nao i peppera, sprawdzić w developer guidzie
CAMERA_INDEX = 0
RESOLUTION_INDEX = 3
COLORSPACE_INDEX = 11
FRAMERATE = 5

LANGUAGE = "Polski"
#LANGUAGE = "English"



app = qi.Application(sys.argv, url="tcps://192.168.1.110:9503")    # Pepper
#app = qi.Application(sys.argv, url="tcps://192.168.1.104:9503")    # Nao

logins = ("nao", "nao")
factory = AuthenticatorFactory(*logins)
app.session.setClientAuthenticatorFactory(factory)
app.start()

if LANGUAGE == "Polski":
    app.session.service("ALTextToSpeech").setLanguage("Polish")
elif LANGUAGE == "English":
    app.session.service("ALTextToSpeech").setLanguage("English")
tts = app.session.service("ALAnimatedSpeech")
motion_service = app.session.service("ALMotion")
video_service = app.session.service("ALVideoDevice")

video_service = delete_subs("kamera", app, video_service) # needed for camera initialization
vid_handle = video_service.subscribeCamera(
    "kamera",
    CAMERA_INDEX,
    RESOLUTION_INDEX,
    COLORSPACE_INDEX,
    FRAMERATE

)

sound_module_instance = SoundReceiverModule(app.session, name="SoundProcessingModule", thresholdRMSEnergy = 0.04)
app.session.registerService("SoundProcessingModule", sound_module_instance)
sleep(1)  # Give some time for the module to register
sound_module_instance.start()


async def main():
    print("Start")
    #lookForward(motion_service)

    agent = init_agent(motion_service, video_service, vid_handle, language=LANGUAGE)

    # Initialize message history
    message_history = []
    # Main chat loop
    while True:
        # Listening
        # sound_module_instance.setListening()
        # if len(sound_module_instance.stt_output) > 0:
        #     user_input = sound_module_instance.stt_output
        #     sound_module_instance.stt_output = []
        #     sound_module_instance.setNotListening()
        # else:
        #     continue


        sound_module_instance.setListening()
        # Wait a bit for speech input
        await asyncio.sleep(0.1)

        print(f"During listening or procesing: {sound_module_instance.is_accumulating_or_recognizing_speech}")
        # Do not do anything while listening
        if sound_module_instance.is_accumulating_or_recognizing_speech:
            continue

        # Capture image
        camera_view_bytes = take_picture(video_service, vid_handle)
        image_content = BinaryContent(data=camera_view_bytes, media_type='image/jpeg')

        # Check for speech input
        user_text = ""
        if len(sound_module_instance.stt_output) > 0:
            user_text = sound_module_instance.stt_output
            sound_module_instance.stt_output = []  # Clear the buffer
            sound_module_instance.setNotListening()

        user_input = [
            f"Human voice commend: '{user_text}'.\n\nThat's what you see on the front:" if user_text else "That's what you see on the front:",
            image_content
        ]

        #message_history = trim_history(message_history, max_size=16)

        llm_response = await generate_and_say_response(agent, user_input, message_history, tts, sound_module_instance)

        print()  # Add newline after streaming
        message_history.extend(llm_response)


if __name__ == "__main__":
    asyncio.run(main())
