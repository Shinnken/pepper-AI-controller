import numpy as np
import cv2


def delete_subs(name, app, video_service):
    all_subscribers = video_service.getSubscribers()
    sub_to_delete = [subscriber for subscriber in all_subscribers if name in str(subscriber)] # type: ignore
    for sub in sub_to_delete:
        app.session.service("ALVideoDevice").unsubscribe(sub)

    return video_service


def draw_horizontal_angle_grid(image, center_angle=0):
    """Draw HORIZONTAL angle markers on the bottom of the image."""
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
        x_position = int((max_angle - angle) / (max_angle - min_angle) * image_width)

        # Draw vertical tick mark
        cv2.line(image, (x_position, y_position - 10), (x_position, y_position + 10), yellow_color, 2)

        # Add angle text above the line
        cv2.putText(image, f"{angle}deg", (x_position - 15, y_position - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, yellow_color, 2)

    return image


def draw_vertical_angle_grid(image):
    """Draw VERTICAL angle markers on the left side of the image."""
    image_height, _ = image.shape[:2]
    yellow_color = (0, 255, 255)  # BGR for yellow
    x_position = 30  # pixels from left edge

    # Draw the main vertical line
    cv2.line(image, (x_position, 0), (x_position, image_height), yellow_color, 2)

    # V-FOV is approx +/- 25 deg. Add markers from +20 to -20 degrees.
    vertical_fov_range = 25
    for angle in range(20, -21, -10):
        # Map angle to y-coordinate. Positive angle is up (lower y-value).
        y_pos = int((image_height / 2) * (1 - angle / vertical_fov_range))

        # Draw horizontal tick mark
        cv2.line(image, (x_position - 10, y_pos), (x_position + 10, y_pos), yellow_color, 2)

        # Add angle text
        cv2.putText(image, f"{angle}deg", (x_position + 15, y_pos + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, yellow_color, 2)
    return image


def take_picture(video_service, video_handle, center_angle=0, add_vertical_grid=False):
    frame_data = video_service.getImageRemote(video_handle)  # get frame
    width = frame_data[0]
    height = frame_data[1]
    raw_bytes = frame_data[6]  # Could be a list of ints

    image_buffer = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((height, width, 3))
    image_buffer = cv2.cvtColor(image_buffer, cv2.COLOR_RGB2BGR)
    image_buffer = draw_horizontal_angle_grid(image_buffer, center_angle)

    if add_vertical_grid:
        image_buffer = draw_vertical_angle_grid(image_buffer)


    return image_buffer
