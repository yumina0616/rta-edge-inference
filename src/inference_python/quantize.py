from pathlib import Path

import nncf
import openvino as ov

from calibration_dataset import build_calibration_dataset

FP32_IR_PATH = Path("models/openvino/fp32/yolov8n_416.xml")
INT8_IR_DIR = Path("models/openvino/int8")

def quantize() -> ov.Model:
    core = ov.Core()
    fp32_model = core.read_model(FP32_IR_PATH)

    calibration_dataset = build_calibration_dataset()
    int8_model = nncf.quantize(fp32_model, calibration_dataset)

    return int8_model

def save(int8_model: ov.Model) -> None:
    INT8_IR_DIR.mkdir(parents=True, exist_ok=True)
    ov.save_model(int8_model, str(INT8_IR_DIR / "yolov8n_416.xml"))

def verify() -> None:
    core = ov.Core()
    model = core.read_model(INT8_IR_DIR / "yolov8n_416.xml")
    print("input shape:", model.input(0).shape)
    print("output shape:", model.output(0).shape)

if __name__ == "__main__":
    int8_model = quantize()
    save(int8_model)
    verify()