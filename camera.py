import numpy as np
import cv2


def delete_subs(name, app, video_service):
    all_subscribers = video_service.getSubscribers()
    sub_to_delete = [subscriber for subscriber in all_subscribers if name in str(subscriber)] # type: ignore
    for sub in sub_to_delete:
        app.session.service("ALVideoDevice").unsubscribe(sub)

    return video_service


def draw_angle_markers(image, center_angle=0):
    """Draw angle markers on the bottom of the image showing camera field of view"""
    image_height, image_width = image.shape[:2]

    # Calculate visible angles based on center_angle
    visible_range = 35  # 35 degrees each side
    min_angle = center_angle - visible_range
    max_angle = center_angle + visible_range

    # Generate angle markers within visible range, with 5-degree margins
    angles = []
    current = min_angle + 5  # Start 5 degrees from edge
    while current <= max_angle - 5:  # End 5 degrees from edge
        angles.append(current)
        current += 10

    # Calculate y position for markers (closer to bottom to take less photo space)
    y_position = image_height - 25

    # Yellow color in BGR format
    yellow_color = (0, 255, 255)

    # Draw horizontal line
    cv2.line(image, (0, y_position), (image_width, y_position), yellow_color, 2)

    # Draw markers
    for angle in angles:
        # Map angle to x position within the visible range
        x_position = int((angle - min_angle) / (max_angle - min_angle) * image_width)

        # Draw vertical tick mark
        cv2.line(image, (x_position, y_position - 10), (x_position, y_position + 10), yellow_color, 2)

        # Add angle text above the line
        cv2.putText(image, f"{angle}deg", (x_position - 15, y_position - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, yellow_color, 2)

    return image


def take_picture(video_service, video_handle, center_angle=0):
    frame_data = video_service.getImageRemote(video_handle)  # get frame
    width = frame_data[0]
    height = frame_data[1]
    raw_bytes = frame_data[6]  # Could be a list of ints

    image_buffer = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((height, width, 3))
    image_buffer = cv2.cvtColor(image_buffer, cv2.COLOR_RGB2BGR)
    image_buffer = draw_angle_markers(image_buffer, center_angle)

    cv2.imwrite(f"pepper_image_{center_angle}.png", image_buffer)

    _, buffer = cv2.imencode('.jpg', image_buffer)
    return buffer.tobytes()
