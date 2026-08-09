import json
import sys
import time

from video_reader import read_frames
from preprocess import preprocess
from infer import Detector, postprocess

IR_MODEL_PATH = "models/openvino/fp32/yolov8n_416.xml"

def run(video_path: str) -> None:
    detector = Detector(IR_MODEL_PATH)

    for frame_id, frame in read_frames(video_path): # 프레임마다
        tensor, scale, pad = preprocess(frame)

        infer_start = time.perf_counter()
        raw_output = detector.infer(tensor)
        infer_latency_ms = (time.perf_counter() - infer_start) * 1000

        detections = postprocess(raw_output, scale, pad)
        timestamp_ms = int(time.time() * 1000)

        record = build_record(frame_id, timestamp_ms, infer_latency_ms, detections)
        print(json.dumps(record))
        sys.stdout.flush()  # C++가 줄 단위로 바로 읽을 수 있게 내보내기


def build_record(
    frame_id: int, timestamp_ms: int, infer_latency_ms: float, detections: list[dict]
) -> dict:
    if not detections:
        return {
            "frame_id": frame_id,
            "timestamp_ms": timestamp_ms,
            "confidence": 0.0,
            "bbox": None,
            "inference_latency_ms": round(infer_latency_ms, 2),
            "valid": False,
        }

    best = max(detections, key=lambda d: d["confidence"])
    return {
        "frame_id": frame_id,
        "timestamp_ms": timestamp_ms,
        "confidence": round(best["confidence"], 4),
        "bbox": [round(v, 1) for v in best["bbox"]],
        "inference_latency_ms": round(infer_latency_ms, 2),
        "valid": True,
    }

if __name__ == "__main__":
    run(sys.argv[1])