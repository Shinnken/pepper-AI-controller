import asyncio
import qi
import sys
from robot_auth import AuthenticatorFactory
from camera import delete_subs
from metal_bottle_detector import collect_episode
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from motion import grabGun


# inne parametry dla nao i peppera, sprawdzić w developer guidzie
CAMERA_INDEX = 0
RESOLUTION_INDEX = 3
COLORSPACE_INDEX = 11
FRAMERATE = 5

LANGUAGE = "Polski"
# LANGUAGE = "English"

app = qi.Application(sys.argv, url="tcps://192.168.1.110:9503")  # Pepper
# app = qi.Application(sys.argv, url="tcps://192.168.1.104:9503")    # Nao

logins = ("nao", "nao")
factory = AuthenticatorFactory(*logins)
app.session.setClientAuthenticatorFactory(factory)
app.start()

# app.session.service("ALAutonomousLife").setState("disabled")  # Disable autonomous life to prevent interruptions
app.session.service("ALMotion").wakeUp()  # Wake up the robot
app.session.service("ALRobotPosture").goToPosture("StandInit", 0.5)  # Set initial posture

motion_service = app.session.service("ALMotion")
video_service = app.session.service("ALVideoDevice")

video_service = delete_subs("kamera", app, video_service, motion_service)  # needed for camera initialization
vid_handle = video_service.subscribeCamera(
    "kamera",
    CAMERA_INDEX,
    RESOLUTION_INDEX,
    COLORSPACE_INDEX,
    FRAMERATE

)


async def main():
    print("Start")
    grabGun(motion_service)
    collect_episode(0, video_service, vid_handle)


if __name__ == "__main__":
    asyncio.run(main())