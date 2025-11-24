import cv2
from ultralytics import YOLO

# Load the ONNX or TensorRT model
# Use "best.engine" for tensorRT OR "best.onnx" for ONNXRuntime
model = YOLO("best.onnx")  # or "best.engine"

# Open camera/stream
# For DJI drone: use your HDMI/USB capture device
# Or RTSP stream if available
cap = cv2.VideoCapture(0)  # Replace with your capture device or RTSP URL

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Run inference (very light on Jetson Nano with YOLO-nano)
    results = model(frame, imgsz=640, conf=0.25)

    # Draw results
    annotated = results[0].plot()

    # Display (optional onboard)
    cv2.imshow("Jetson YOLO Inference", annotated)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
