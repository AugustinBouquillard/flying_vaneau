import cv2
import matplotlib.pyplot as plt
from ultralytics import YOLO
import numpy
import PIL


def detect_objects(model, img: PIL.Image, DEBUG=False):
    # Load model
    # model = YOLO("./best.pt")

    # Run inference
    results = model(img)

    open_cv_image = cv2.cvtColor(numpy.array(img), cv2.COLOR_RGB2BGR)
    # Convert RGB to BGR

    # Copy original image for drawing
    # img = results[0].orig_img.copy()

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
        if DEBUG:
            # Draw center point
            #Circle = cv2.circle(open_cv_image, (int(X), int(Y)), 5, (255, 255, 0), -1)
            cv2.drawMarker(open_cv_image, (int(X), int(Y)),(255,0,0),cv2.MARKER_TRIANGLE_DOWN,5,2,1)
            # Label center coordinates (needs int()!)
            text = f"({int(X)}, {int(Y)} : {conf:.2f})"
            cv2.putText(
                open_cv_image, text,
                (int(X) - 20, int(Y) - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (255, 0, 0), 1, cv2.LINE_AA
            )

    # Convert BGR (OpenCV) → RGB (Matplotlib)
    if DEBUG:
        img_rgb = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2RGB)
        cv2.imshow("Res", img_rgb)
    # Show result
    """plt.figure(figsize=(10, 10))
    plt.imshow(img_rgb)
    plt.axis("off")
    plt.show()"""

    return detections


if __name__ == "__main__":
    print(detect_objects())