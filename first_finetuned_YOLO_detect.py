import cv2
import matplotlib.pyplot as plt
from ultralytics import YOLO

def detect_objects(image_path="WhatsApp_Image_2025-11-25_at_20.51.47.jpeg"):
    # Load model
    model = YOLO("runs_finetune_1/yolov8n_finetune2/weights/best.pt")

    # Run inference
    results = model(image_path)

    # Copy original image for drawing
    img = results[0].orig_img.copy()

    detections = []

    for box in results[0].boxes:
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        xyxy = box.xyxy[0].tolist()

        # Compute center of bounding box
        X = (xyxy[0] + xyxy[2]) / 2
        Y = (xyxy[1] + xyxy[3]) / 2

        detections.append({
            "Class": model.names[cls],
            "Confidence": conf,
            "Center": (X, Y)
        })

        # Draw center point
        cv2.circle(img, (int(X), int(Y)), 5, (0, 255, 0), -1)

        # Label center coordinates (needs int()!)
        text = f"({int(X)}, {int(Y)})"
        cv2.putText(
            img, text,
            (int(X) - 20, int(Y) - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5, (0, 255, 0), 1, cv2.LINE_AA
        )


    # Convert BGR (OpenCV) → RGB (Matplotlib)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Show result
    plt.figure(figsize=(10, 10))
    plt.imshow(img_rgb)
    plt.axis("off")
    plt.show()

    return detections



print(detect_objects())
