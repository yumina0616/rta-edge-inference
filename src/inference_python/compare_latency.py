import csv
import time
from pathlib import Path

from video_reader import read_frames
from preprocess import preprocess
from infer import Detector

FP32_IR_PATH = "models/openvino/fp32/yolov8n_416.xml"
INT8_IR_PATH = "models/openvino/int8/yolov8n_416.xml"
LATENCY_VIDEO = "data/videos/14468440_2160_3840_30fps.mp4"
WARMUP_RUNS = 10
MEASURE_RUNS = 100
LATENCY_CSV_PATH = "results/raw/fp32_vs_int8_latency.csv"


def write_csv(rows: list[dict], path: str) -> None:
    if not rows:
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

def _collect_tensors(video_path: str, count: int) -> list:
    tensors = []
    for frame_id, frame in read_frames(video_path):
        tensor, _, _ = preprocess(frame)
        tensors.append(tensor)
        if len(tensors) >= count:
            break
    return tensors

def measure_latency(detector: Detector, tensors: list) -> tuple[float, list[float]]:
    for tensor in tensors[:WARMUP_RUNS]:
        detector.infer(tensor)

    latencies_ms = []
    for tensor in tensors[:MEASURE_RUNS]:
        start = time.perf_counter()
        detector.infer(tensor)
        latencies_ms.append((time.perf_counter() - start) * 1000)

    return sum(latencies_ms) / len(latencies_ms), latencies_ms

def compare() -> None:
    tensors = _collect_tensors(LATENCY_VIDEO, WARMUP_RUNS + MEASURE_RUNS)

    fp32_detector = Detector(FP32_IR_PATH)
    int8_detector = Detector(INT8_IR_PATH)

    fp32_avg, fp32_latencies = measure_latency(fp32_detector, tensors)
    int8_avg, int8_latencies = measure_latency(int8_detector, tensors)

    speedup = (fp32_avg - int8_avg) / fp32_avg * 100

    print(f"FP32 avg latency: {fp32_avg:.2f} ms")
    print(f"INT8 avg latency: {int8_avg:.2f} ms")
    print(f"speedup: {speedup:.1f}%")

    rows = [
        {"frame_id": i, "fp32_latency_ms": fp32_ms, "int8_latency_ms": int8_ms}
        for i, (fp32_ms, int8_ms) in enumerate(zip(fp32_latencies, int8_latencies))
    ]
    write_csv(rows, LATENCY_CSV_PATH)


if __name__ == "__main__":
    compare()