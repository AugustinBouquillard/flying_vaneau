from ultralytics import YOLO
import cv2
from matplotlib import pyplot as plt

# ---------------------------------------------------
# Load your fine-tuned model
# ---------------------------------------------------
model = YOLO("runs_finetune_1/yolov8n_finetune2/weights/best.pt")

# ---------------------------------------------------
# Path to the image you want to test
# ---------------------------------------------------
image_path = "WhatsApp_Image_2025-11-25_at_20.51.47.jpeg"

# ---------------------------------------------------
# Run inference
# ---------------------------------------------------
results = model(image_path)

# ---------------------------------------------------
# Display annotated image
# ---------------------------------------------------
result_img = results[0].plot()   # Draw bounding boxes on the image

plt.figure(figsize=(10, 10))
plt.imshow(result_img)
plt.axis("off")
plt.show()

# ---------------------------------------------------
# Print detections
# ---------------------------------------------------
print("\nDetections:")
for box in results[0].boxes:
    cls = int(box.cls[0])
    conf = float(box.conf[0])
    xyxy = box.xyxy[0].tolist()

    print(f"- Class: {model.names[cls]}, Confidence: {conf:.2f}, BBox (xyxy): {xyxy}")

plt.savefig("taraget_detected"+image_path+".jpeg")
