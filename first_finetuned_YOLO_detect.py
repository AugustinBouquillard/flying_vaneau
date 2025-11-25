import cv2
import matplotlib.pyplot as plt
from ultralytics import YOLO

def detect_objects(image_path="WhatsApp_Image_2025-11-25_at_20.51.47.jpeg"):
    model = YOLO("runs_finetune_1/yolov8n_finetune2/weights/best.pt")
    results = model(image_path)

    L = []
    img = results[0].orig_img.copy()

    for box in results[0].boxes:
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        xyxy = box.xyxy[0].tolist()
        #object center coordinates
        X = (xyxy[0] + xyxy[2]) / 2
        Y = (xyxy[1] + xyxy[3]) / 2
        L.append({"Class": model.names[cls], "Confidence": conf, "Center": (X, Y)})

        #center point display
        cv2.circle(img, (int(X), int(Y)), radius=5, color=(0, 255, 0), thickness=-1)
        text = f"({X}, {Y})"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        color = (0, 255, 0)
        thickness = 1
        cv2.putText(img, text, (X - 20, Y - 10), font, font_scale, color, thickness, cv2.LINE_AA)

    # Convert BGR to RGB for matplotlib
    #img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    plt.figure(figsize=(10, 10))
    plt.imshow(cv2)
    plt.axis("off")
    plt.show()

    return L


print(detect_objects())
