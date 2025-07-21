import sys
from ultralytics import YOLO
from pathlib import Path

parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from camera import take_picture


# === PARAMS ===
MIN_CONFIDENCE         = 0.25
MIN_HEIGHT_RATIO       = 0.03  # if bottle <3% of frame height → too far
HORIZONTAL_ROTATION_FACTOR = 0.05
VERTICAL_ROTATION_FACTOR   = 0.05

def turn_robot(angle_degrees, motion_service):
    print(f"[ROBOT] turn_robot({angle_degrees:.1f}°)")  # + = left, – = right
    radians = angle_degrees * 0.01745
    motion_service.wakeUp()
    motion_service.moveTo(0.0, 0.0, radians)

def tilt_arm(angle_degrees, motion_service):
    print(f"[ROBOT] tilt_robot({angle_degrees:.1f}°)")  # + = up, – = down
    JointNames = ["RElbowYaw"]
    # 60 to kąt bazowy
    positions = [60 + angle_degrees]
    motion_service.setAngles(JointNames, positions, 1.0)

def shoot():
    print("[ROBOT] shoot()")

def detect_bottle(frame):
    """Detect bottle in frame and return the best bottle box or None"""
    if frame is None:
        return None

    # Run YOLOv8 detector
    model   = YOLO("yolov8n.pt")
    results = model(frame)[0]

    # Find the *closest* upright bottle (largest bbox height)
    best_box       = None
    max_box_height = 0
    for box, confidence, class_id in zip(results.boxes.xyxy,
                                         results.boxes.conf,
                                         results.boxes.cls):
        if int(class_id) != 39 or float(confidence) < MIN_CONFIDENCE:
            continue
        x1, y1, x2, y2 = map(int, box)
        width  = x2 - x1
        height = y2 - y1
        if height <= width:  # require upright shape
            continue
        if height > max_box_height:
            max_box_height = height
            best_box       = (x1, y1, x2, y2)

    return best_box

def choose_actions(bottle_box, frame_height, frame_width):
    """
    Check bottle position and return discrete control decisions:
    - needs_turn_left/right
    - needs_move_forward
    - needs_tilt_up/down
    - ready_to_shoot
    """
    x1, y1, x2, y2 = bottle_box
    box_width   = x2 - x1
    box_height  = y2 - y1
    center_x    = x1 + box_width  * 0.5
    center_y    = y1 + box_height * 0.5

    # Frame center
    frame_center_x = frame_width * 0.5
    frame_center_y = frame_height * 0.5

    actions_dict = {
        'horizontal_turn': -(center_x - frame_center_x) * HORIZONTAL_ROTATION_FACTOR,
        'vertical_turn': (center_y - frame_center_y) * VERTICAL_ROTATION_FACTOR,
        'too_far': (box_height / frame_height) < MIN_HEIGHT_RATIO
    }

    return actions_dict


def target_and_shoot_bottle(video_service, vid_handle, motion_service):
    # Capture image
    frame = take_picture(video_service, vid_handle)
    frame_height, frame_width = frame.shape[:2]

    # Detect bottle
    best_box = detect_bottle(frame)
    if not best_box:
        print("Can't shoot: no bottle detected.")
        return("No bottle detected.")

    # Check bottle position
    actions = choose_actions(best_box, frame_height, frame_width)
    print(f"Actions: {actions}")
    if actions['too_far']:
        return "Can't shoot: bottle is too far. Move closer."
    # Execute discrete control actions
    # horizontal rotation
    turn_robot(actions['horizontal_turn'], motion_service)
    # vertical rotation
    tilt_arm(actions['vertical_turn'], motion_service)
    shoot()
    return "Targeted and shot at the bottle."
