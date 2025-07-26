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
    visible_range = 28  # 28 degrees each side
    min_angle = center_angle - visible_range
    max_angle = center_angle + visible_range

    # Generate angle markers every 5 degrees
    angles = []
    start_angle = int((min_angle + 4) // 5) * 5  # Round up to nearest multiple of 5
    end_angle = int(max_angle // 5) * 5  # Round down to nearest multiple of 5
    for angle in range(start_angle, end_angle + 1, 5):
        angles.append(angle)

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
        cv2.putText(image, f"{angle}", (x_position - 10, y_position - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, yellow_color, 2)

    return image


def draw_vertical_angle_grid(image):
    """Draw VERTICAL angle markers on the middle of the image."""
    image_height, image_width = image.shape[:2]
    green_color = (0, 255, 0)  # BGR
    x_position = image_width // 2  # Center of the image

    # Draw the main vertical line
    cv2.line(image, (x_position, 0), (x_position, image_height), green_color, 2)

    # V-FOV is approx +/- 22 deg. Add markers from +20 to -20 degrees every 5 degrees.
    vertical_fov_range = 22
    for angle in range(20, -21, -5):
        y_pos = int((image_height / 2) * (1 - angle / vertical_fov_range))
        # Draw horizontal tick mark
        cv2.line(image, (x_position - 10, y_pos), (x_position + 10, y_pos), green_color, 2)
        # Add angle text
        cv2.putText(image, f"{angle}", (x_position + 15, y_pos + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, green_color, 2)

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


def take_gun_camera_photo():
    pass


def draw_gun_camera_crosshair(image):
    """Draw crosshair grid with angle markers for gun camera images."""
    image_height, image_width = image.shape[:2]
    
    # RPi Camera V2 field of view
    horizontal_fov = 62
    vertical_fov = 49
    
    # Center coordinates
    center_x = image_width // 2
    center_y = image_height // 2
    
    # Red color in BGR format
    red_color = (0, 0, 0)
    
    # Draw main crosshair lines
    cv2.line(image, (center_x, 0), (center_x, image_height), red_color, 2)
    cv2.line(image, (0, center_y), (image_width, center_y), red_color, 2)
    
    # Draw vertical angle markers
    for angle in range(-20, 21):
        y_pos = int(center_y * (1 - angle / (vertical_fov/2)))
        if angle == 0 or angle % 5 == 0:
            if angle % 5 == 0:
                # Draw longer tick for 5-degree marks
                cv2.line(image, (center_x - 20, y_pos), (center_x + 20, y_pos), red_color, 2)
                cv2.putText(image, str(angle), (center_x + 25, y_pos),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, red_color, 2)
        else:
            # Draw shorter tick for 1-degree marks near center
            if abs(angle) <= 15:
                cv2.line(image, (center_x - 10, y_pos), (center_x + 10, y_pos), red_color, 1)

    # Draw horizontal angle markers
    for angle in range(-30, 31):
        x_pos = int(center_x * (1 - angle / (horizontal_fov/2)))
        if angle == 0 or angle % 5 == 0:
            if angle % 5 == 0:
                # Draw longer tick for 5-degree marks
                cv2.line(image, (x_pos, center_y - 20), (x_pos, center_y + 20), red_color, 2)
                cv2.putText(image, str(angle), (x_pos - 10, center_y - 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, red_color, 2)
        else:
            # Draw shorter tick for 1-degree marks near center
            if abs(angle) <= 15:
                cv2.line(image, (x_pos, center_y - 10), (x_pos, center_y + 10), red_color, 1)

    return image
