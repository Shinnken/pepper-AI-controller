import numpy as np
import cv2


def take_picture(video_service, video_handle):
    frame_data = video_service.getImageRemote(video_handle)  # get frame
    width = frame_data[0]
    height = frame_data[1]
    raw_bytes = frame_data[6]  # Could be a list of ints

    image_buffer = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((height, width, 3))
    image_buffer = cv2.cvtColor(image_buffer, cv2.COLOR_RGB2BGR)
    cv2.imwrite("pepper_image.png", image_buffer)

