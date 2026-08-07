import cv2
import numpy as np
import openvino as ov

CONF_THRESHOLD = 0.5
NMS_IOU_THRESHOLD = 0.45    # 어느 정도 box가 겹칠 때 제거할 것인가
NUM_CLASSES = 80    # 객체 클래스 종류 개수

class Detector:
    def __init__(self, ir_xml_path: str, device: str="CPU"):
        core = ov.Core()
        model = core.read_model(ir_xml_path)

        # 객체 생성할 때 컴파일 한 번만(프레임마다 반복 X)
        self.compiled_model = core.compile_model(model, device)
        # 모델 출력은 항상 첫 번째 포트(0)를 가리키도록
        self.output_layer = self.compiled_model.output(0)


    def infer(self, input_tensor: np.ndarray) -> np.ndarray:
        result = self.compiled_model([input_tensor])[self.output_layer]
        return result


def postprocess(
    raw_output: np.ndarray,
    scale: float,
    pad: tuple[int, int],
) -> list[dict]:
    predictions = raw_output[0].T   # 0번째 batch의 (84, N)의 전치 -> (N, 84)

    boxes_xywh = predictions[:, :4]
    class_scores = predictions[:, 4:]
    class_ids = np.argmax(class_scores, axis=1)
    confidences = np.max(class_scores, axis=1)

    keep = confidences >= CONF_THRESHOLD
    boxes_xywh, confidences, class_ids = boxes_xywh[keep], confidences[keep], class_ids[keep]

    # NMS는 (x, y, w, h) 형태(좌상단 기준)
    # cx,cy,w,h -> x,y,w,h 변환
    boxes_xywh_topleft = boxes_xywh.copy()
    boxes_xywh_topleft[:, 0] = boxes_xywh[:, 0] - boxes_xywh[:, 2] / 2
    boxes_xywh_topleft[:, 1] = boxes_xywh[:, 1] - boxes_xywh[:, 3] / 2

    indices = cv2.dnn.NMSBoxes(
        boxes_xywh_topleft.tolist(), confidences.tolist(), CONF_THRESHOLD, NMS_IOU_THRESHOLD
    )

    pad_x, pad_y = pad
    detections = []
    for i in np.array(indices).flatten():
        x, y, w, h = boxes_xywh_topleft[i]
        # letterbox 역변환: 416 좌표계 -> 원본 좌표계
        x1 = (x - pad_x) / scale
        y1 = (y - pad_y) / scale
        x2 = (x + w - pad_x) / scale
        y2 = (y + h - pad_y) / scale
        detections.append(
            {
                "bbox": [float(x1), float(y1), float(x2), float(y2)],
                "confidence": float(confidences[i]),
                "class_id": int(class_ids[i]),
            }
        )
    return detections


if __name__ == "__main__":
    import sys
    from video_reader import read_frames
    from preprocess import preprocess

    detector = Detector(sys.argv[1])

    for frame_id, frame in read_frames(sys.argv[2]):
        tensor, scale, pad = preprocess(frame)
        raw_output = detector.infer(tensor)
        print("raw output shape:", raw_output.shape)  # (1, 84, N) 확인

        detections = postprocess(raw_output, scale, pad)
        print("detections:", detections)
        break