import sys, os, json, time
import cv2
import numpy as np
from ultralytics import YOLO
from pathlib import Path

parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from camera import take_picture


# === PARAMS ===
MIN_CONFIDENCE         = 0.25
MIN_HEIGHT_RATIO       = 0.03  # if bottle <3% of frame height → too far

# Placeholder robot API functions (implement these)
def turn_robot(angle_degrees, motion_service):
    print(f"[ROBOT] turn_robot({angle_degrees:.1f}°)")  # + = left, – = right
    radians = angle_degrees * 0.01745
    motion_service.wakeUp()
    motion_service.moveTo(0.0, 0.0, radians)

def move_robot_forward(motion_service):
    print("[ROBOT] move_robot_forward()")
    motion_service.wakeUp()
    motion_service.moveTo(0.5, 0.0, 0.0)

def tilt_arm(angle_degrees, motion_service):
    print(f"[ROBOT] tilt_robot({angle_degrees:.1f}°)")  # + = up, – = down
    JointNames = ["RElbowYaw", "HeadPitch"]
    positions = [angle_degrees, angle_degrees]
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

    # Calculate pixel thresholds based on angle threshold
    horizontal_threshold = 3
    vertical_threshold = 3

    # Actions_array: arr[0] = horizontal_rotation, arr[1] = too_far, arr[2] = vertical_rotation, arr[3] = shoot_flag
    actions_array = np.zeros(4, dtype=np.float32)

    # Check horizontal position
    if center_x < frame_center_x - horizontal_threshold:
        # turn right
        actions_array[0] = -3
    elif center_x > frame_center_x + horizontal_threshold:
        # turn left
        actions_array[0] = 3

    # Check if too far
    height_ratio = box_height / frame_height
    too_far = (height_ratio < MIN_HEIGHT_RATIO)
    if too_far:
        # Move forward
        actions_array[1] = 1

    # Check vertical position
    if center_y < frame_center_y - vertical_threshold:
        # tilt down
        actions_array[2] = -3
    elif center_y > frame_center_y + vertical_threshold:
        # tilt up
        actions_array[2] = 3

    # Check if ready to shoot
    if np.all(actions_array == 0):
        actions_array[3] = 1

    return actions_array

def read_robot_state():
    # Return a NumPy float32 array of shape (S,)
    # e.g. [heading_deg, pitch_deg, position_m]
    return np.array([0.0, 0.0, 0.0], dtype=np.float32)


def write_modality_json(episode_dir):
    # Describe your modalities once per folder
    # Adjust S (#state dims) and A (#action dims) accordingly
    H,W,_  = cv2.imread(next(os.scandir(episode_dir)).path).shape
    SAMPLE = np.load(os.path.join(episode_dir,
              os.listdir(episode_dir)[0]))
    S = SAMPLE["state"].shape[1]
    A = SAMPLE["action"].shape[1]
    mod = {
      "rgb":    {"type":"video",  "shape":[None,H,W,3],"dtype":"uint8"},
      "state":  {"type":"tensor", "shape":[None,S],   "dtype":"float32"},
      "action": {"type":"tensor", "shape":[None,A],   "dtype":"float32"}
    }
    with open(os.path.join(episode_dir,"modality.json"),"w") as f:
        json.dump(mod, f, indent=2)


def collect_episode(episode_idx, video_service, vid_handle, motion_service):
    episode_dir = "training_data"
    os.makedirs(episode_dir, exist_ok=True)

    frames = []  # list of uint8 arrays [H,W,3]
    states = []  # list of float32 arrays [S,]
    actions = []  # list of float32 arrays [A,]
    while True:
        # Capture image
        frame = take_picture(video_service, vid_handle)
        frame_height, frame_width = frame.shape[:2]

        state_vec = read_robot_state()

        # Detect bottle
        best_box = detect_bottle(frame)
        if not best_box:
            print("No bottle detected.")
            break

        # Check bottle position
        action_vec = choose_actions(best_box, frame_height, frame_width)

        frames.append(frame)
        states.append(state_vec)
        actions.append(action_vec)

        # Execute discrete control actions
        # horizontal rotation
        if action_vec[0]:
            turn_robot(action_vec[0], motion_service)
        # move forward
        if action_vec[1]:
            move_robot_forward(motion_service)
        # vertical rotation
        if action_vec[2]:
            tilt_arm(action_vec[2], motion_service)
        # shoot
        if action_vec[3]:
            shoot()
            break

    # convert lists → arrays
    frames_arr = np.stack(frames, axis=0)          # [T,H,W,3], uint8
    states_arr = np.stack(states, axis=0)          # [T,S],    float32
    actions_arr= np.stack(actions,axis=0)          # [T,A],    float32

    # save .npz
    npz_path = os.path.join(episode_dir,
               f"episode_{episode_idx:03d}.npz")
    np.savez_compressed(npz_path,
                        rgb=frames_arr,
                        state=states_arr,
                        action=actions_arr)
