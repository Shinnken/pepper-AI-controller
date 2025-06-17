import sys
import os
import json
import cv2
from ultralytics import YOLO

def main():
    image_path = "images/bottle1.jpg"
    base_name = os.path.splitext(os.path.basename(image_path))[0]

    img = cv2.imread(image_path)
    if img is None:
        print("Invalid image path")
        sys.exit(1)

    model = YOLO("yolov8n.pt")
    results = model(img)[0]

    accepted = []
    for box, conf, cls in zip(results.boxes.xyxy, results.boxes.conf, results.boxes.cls):
        class_id = int(cls)
        if class_id != 39:
            continue
        x1, y1, x2, y2 = map(int, box)
        width = x2 - x1
        height = y2 - y1
        if height <= width:
            continue
        if float(conf) < 0.25:
            continue
        detection_dict = {
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "confidence": round(float(conf), 4),
            "class": "bottle"
        }
        accepted.append(detection_dict)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, f"bottle {float(conf):.2f}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    output_image_path = f"{base_name}_detected.jpg"
    output_json_path = f"{base_name}_coordinates.json"
    cv2.imwrite(output_image_path, img)
    with open(output_json_path, "w") as f:
        json.dump(accepted, f)

    print(f"Total bottles: {len(accepted)}")
    for d in accepted:
        print(f"{d['confidence']:.2f}")


if __name__ == "__main__":
    main()