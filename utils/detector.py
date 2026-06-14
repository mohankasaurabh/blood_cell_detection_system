import os
import cv2

from ultralytics import YOLO

MODEL_PATH = "models/best.pt"

model = YOLO(MODEL_PATH)


def run_detection(image_path):

    results = model.predict(
        image_path,
        conf=0.25,
        save=False
    )

    detections = []

    result = results[0]

    names = model.names

    for box in result.boxes:

        class_id = int(box.cls[0])

        confidence = float(box.conf[0])

        x1, y1, x2, y2 = map(
            int,
            box.xyxy[0]
        )

        detections.append({
            "class_id": class_id,
            "class_name": names[class_id],
            "confidence": confidence,
            "bbox": [x1, y1, x2, y2]
        })

    output_path = save_annotated_image(
        image_path,
        detections
    )

    return detections, output_path


def save_annotated_image(
        image_path,
        detections
):

    image = cv2.imread(image_path)

    colors = {
        "RBC": (0, 255, 0),
        "WBC": (255, 0, 0),
        "Platelet": (0, 255, 255),
        "Parasite": (0, 0, 255)
    }

    for detection in detections:

        x1, y1, x2, y2 = detection["bbox"]

        cls_name = detection["class_name"]

        conf = detection["confidence"]

        color = colors.get(
            cls_name,
            (255, 255, 255)
        )

        label = f"{cls_name} {conf:.2f}"

        cv2.rectangle(
            image,
            (x1, y1),
            (x2, y2),
            color,
            2
        )

        cv2.putText(
            image,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2
        )

    filename = os.path.basename(image_path)

    output_path = os.path.join(
        "static/outputs",
        filename
    )

    cv2.imwrite(
        output_path,
        image
    )

    return output_path