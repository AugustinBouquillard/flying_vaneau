#!/usr/bin/env python3

"""
train_yolov8_nano.py

Fine-tunes YOLOv8-nano on a single YOLO-format dataset.

Usage:
    python train_yolov8_nano.py \
        --data dataset/data.yaml \
        --epochs 50 \
        --imgsz 640 \
        --batch 16
"""

import argparse
import subprocess
import shutil

!pip install roboflow
from roboflow import Roboflow
rf = Roboflow(api_key="01ul0nibjpXa8YbgircG")
project = rf.workspace("huyen-dinh").project("military-vehicle-rstvv")
version = project.version(2)
dataset = version.download("coco")

try:
    from ultralytics import YOLO
except ImportError:
    pip = shutil.which("pip") or "pip"
    subprocess.check_call([pip, "install", "ultralytics"])
    from ultralytics import YOLO


def train_model(data, epochs, imgsz, batch, lr, pretrained):
    print("Loading model:", pretrained)
    model = YOLO(pretrained)

    print("Starting training…")
    model.train(
        data=data,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        lr0=lr,
        name="yolov8n_finetune",
        project="runs_finetune",
        pretrained=True,
        device=0
    )

    print("Training complete.")
    print("Best weights saved at: runs_finetune/yolov8n_finetune/weights/best.pt")
    return "runs_finetune/yolov8n_finetune/weights/best.pt"


def export_formats(weight_path, imgsz=640):
    print("Exporting:", weight_path)
    model = YOLO(weight_path)

    model.export(format="onnx", imgsz=imgsz)
    model.export(format="torchscript", imgsz=imgsz)

    print("Exports saved in same folder as weights.")


#def parse():
#    a = argparse.ArgumentParser()
#    a.add_argument("--data", required=True, help="Path to data.yaml")
#    a.add_argument("--epochs", type=int, default=50)
#    a.add_argument("--imgsz", type=int, default=640)
#    a.add_argument("--batch", type=int, default=16)
#    a.add_argument("--lr", type=float, default=0.01)
#    a.add_argument("--pretrained", type=str, default="yolov8n.pt")
#    return a.parse_args()


#if __name__ == "__main__":
#    args = parse()
#    best = train_model(
#        data=args.data,
#        epochs=args.epochs,
#        imgsz=args.imgsz,
#        batch=args.batch,
#        lr=args.lr,
#        pretrained=args.pretrained
#    )
#    export_formats(best)

import os

data_yaml_path = os.path.join(dataset.location, "data.yaml")

best = train_model(
    data=data_yaml_path,
    epochs=50,
    imgsz=640,
    batch=16,
    lr=0.01,
    pretrained="yolov8n.pt"
)


