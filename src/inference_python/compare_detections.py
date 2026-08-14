from video_reader import read_frames
from preprocess import preprocess
from infer import Detector, postprocess

FP32_IR_PATH = "models/openvino/fp32/yolov8n_416.xml"
INT8_IR_PATH = "models/openvino/int8/yolov8n_416.xml"
COMPARE_VIDEO = "data/videos/14468440_2160_3840_30fps.mp4"
IOU_MATCH_THRESHOLD = 0.5
SAMPLE_FRAME_COUNT = 100

def iou(box_a: list[float], box_b: list[float]) -> float:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    inter_x1, inter_y1 = max(ax1, bx1), max(ay1, by1)
    inter_x2, inter_y2 = min(ax2, bx2), min(ay2, by2)
    inter_area = max(0.0, inter_x2 - inter_x1) * max(0.0, inter_y2 - inter_y1)

    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    union_area = area_a + area_b - inter_area

    return inter_area / union_area if union_area > 0 else 0.0


def best_detection(detections: list[dict]) -> dict | None:
    if not detections:
        return None
    return max(detections, key=lambda d: d["confidence"])


def compare() -> None:
    fp32_detector = Detector(FP32_IR_PATH)
    int8_detector = Detector(INT8_IR_PATH)

    matched, compared, confidence_diffs = 0, 0, []

    for frame_id, frame in read_frames(COMPARE_VIDEO):
        if frame_id >= SAMPLE_FRAME_COUNT:
            break

        tensor, scale, pad = preprocess(frame)

        fp32_best = best_detection(postprocess(fp32_detector.infer(tensor), scale, pad))
        int8_best = best_detection(postprocess(int8_detector.infer(tensor), scale, pad))

        if fp32_best is None or int8_best is None:
            continue

        compared += 1
        same_class = fp32_best["class_id"] == int8_best["class_id"]
        overlap = iou(fp32_best["bbox"], int8_best["bbox"])

        if same_class and overlap >= IOU_MATCH_THRESHOLD:
            matched += 1
            confidence_diffs.append(fp32_best["confidence"] - int8_best["confidence"])

    match_rate = matched / compared if compared else 0.0
    avg_confidence_diff = sum(confidence_diffs) / len(confidence_diffs) if confidence_diffs else 0.0

    print(f"compared frames: {compared}")
    print(f"matched: {matched} ({match_rate:.1%})")
    print(f"avg confidence diff (fp32 - int8): {avg_confidence_diff:.4f}")

if __name__ == "__main__":
    compare()