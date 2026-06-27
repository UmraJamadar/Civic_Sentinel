from ultralytics import YOLO

model = YOLO('AI/best.pt')

results = model.predict(
    source='AI/test.jpg',
    conf=0.3,        # lowered from 0.5 to detect more
    save=True
)

print(f"Total detections: {len(results[0].boxes)}")

for r in results:
    for box in r.boxes:
        cls = int(box.cls[0])
        name = model.names[cls]
        conf = float(box.conf[0])
        print(f"Detected: {name} — Confidence: {conf:.2f}")

if len(results[0].boxes) == 0:
    print("No detections found — try different image!")