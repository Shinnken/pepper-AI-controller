import asyncio
import qi
import sys
from SoundReciver import SoundReceiverModule
from LLM_and_saying import generate_and_say_response, trim_history, init_agent
from robot_auth import AuthenticatorFactory
from motion import moveFingers, grabGun, lookForward
from camera import take_picture
from time import sleep


# inne parametry dla nao i peppera, sprawdzić w developer guidzie
CAMERA_INDEX = 0
RESOLUTION_INDEX = 3
COLORSPACE_INDEX = 11
FRAMERATE = 5



def delete_subs(name, video_service):
    all_subscribers = video_service.getSubscribers()
    sub_to_delete = [subscriber for subscriber in all_subscribers if name in str(subscriber)] # type: ignore
    for sub in sub_to_delete:
        app.session.service("ALVideoDevice").unsubscribe(sub)

    return video_service


app = qi.Application(sys.argv, url="tcps://192.168.1.110:9503")    # Pepper
#app = qi.Application(sys.argv, url="tcps://192.168.1.104:9503")    # Nao

logins = ("nao", "nao")
factory = AuthenticatorFactory(*logins)
app.session.setClientAuthenticatorFactory(factory)
app.start()

app.session.service("ALTextToSpeech").setLanguage("Polish")
tts = app.session.service("ALAnimatedSpeech")
motion_service = app.session.service("ALMotion")
video_service = app.session.service("ALVideoDevice")

video_service = delete_subs("kamera", video_service) # needed for camera initialization
vid_handle = video_service.subscribeCamera(
    "kamera",
    CAMERA_INDEX,
    RESOLUTION_INDEX,
    COLORSPACE_INDEX,
    FRAMERATE

)

sound_module_instance = SoundReceiverModule(app.session, name="SoundProcessingModule", thresholdRMSEnergy = 0.03)
app.session.registerService("SoundProcessingModule", sound_module_instance)
sleep(1)  # Give some time for the module to register
sound_module_instance.start()




async def main():
    print("Start")

    lookForward(motion_service)


    agent = init_agent(motion_service, prompt_name="Narwicki")

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

        take_picture(video_service, vid_handle)

        # Trim history to keep only last 8 messages
        message_history = trim_history(message_history)

        llm_response = await generate_and_say_response(agent, user_input, message_history, tts)

        print()  # Add newline after streaming
        message_history.extend(llm_response)


if __name__ == "__main__":
    asyncio.run(main())
