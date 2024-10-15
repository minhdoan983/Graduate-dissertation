from ultralytics import YOLO

# Load a model

model = YOLO("yolov8n.pt")  # load a pretrained model (recommended for training)
# Use the model
model.train(data="data.yaml", epochs=20, device='cpu')

