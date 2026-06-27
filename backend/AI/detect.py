from ultralytics import YOLO
from config import MODEL_PATH

model = YOLO(MODEL_PATH)

def detect_issue(image_path):
    results = model(image_path)
    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            return model.names[cls]
    return "Unknown"