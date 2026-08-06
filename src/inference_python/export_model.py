from pathlib import Path

from ultralytics import YOLO
import openvino as ov

INPUT_SIZE = 416
MODELS_DIR = Path("models")
ONNX_PATH = MODELS_DIR / "yolov8n_416.onnx"
IR_DIR = MODELS_DIR / "openvino" / "fp32"

def export_onnx() -> Path:
    model = YOLO(MODELS_DIR / "yolov8n.pt")
    # dynamics = False로 고정 shape
    exported_path = Path(model.export(format="onnx", imgsz=INPUT_SIZE, dynamic=False))
    exported_path.replace(ONNX_PATH)
    return ONNX_PATH

def convert_to_ir(onnx_path: Path) -> None:
    IR_DIR.mkdir(parents=True, exist_ok=True)
    ov_model = ov.convert_model(str(onnx_path))
    ov.save_model(ov_model, str(IR_DIR / "yolov8n_416.xml"))

def verify_ir() -> None:
    core = ov.Core()
    model = core.read_model(IR_DIR / "yolov8n_416.xml")
    print("input shape:", model.input(0).shape)
    print("output shape:", model.output(0).shape)

if __name__ == "__main__":
    onnx_path = export_onnx()
    convert_to_ir(onnx_path)
    verify_ir()