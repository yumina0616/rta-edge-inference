# Model Manifest

## 선정 모델

- **모델**: YOLOv8n (Ultralytics)
- **사전학습 가중치**: COCO 데이터셋 기준 공식 pretrained weights
- **선정 이유**: YOLOv8 계열 중 파라미터 수가 가장 적은 변형(n)으로, 자원 제약 엣지 환경(Jetson
  등)을 다루는 이 프로젝트의 취지에 부합. anchor-free 구조로 후처리가 비교적 단순함.

## 입력 사양

- **입력 해상도**: 416×416 (고정)
  - 640×640(정확도 우선) 대비 연산량 약 42% 수준, 320×320(속도 우선) 대비는 정확도 손실이 적다. 자원 제약과 탐지 정확도 사이의 절충점으로 채택.
  - 이후의 모든 단계도 이 해상도로 통일한다.
- **입력 포맷**: RGB, letterbox resize(원본 비율 유지 + 여백 패딩)로 416×416에 맞춘 뒤 0~1 정규화
- **입력 텐서 shape**: `[1, 3, 416, 416]` (NCHW)

## 출력 사양

- **원시 출력**: 후보 bbox별 (cx, cy, w, h, class confidence×N) — anchor-free
- **후처리**: confidence threshold 필터링 → NMS(Non-Max Suppression)로 중복 박스 제거
- **최종 출력 필드**: `bbox`(x1, y1, x2, y2), `confidence`, `class_id`

## 변환 경로

```
PyTorch(.pt) --export--> ONNX(.onnx) --OpenVINO Model Conversion--> OpenVINO IR(.xml + .bin)
```

- 변환 시 입력 shape을 동적(dynamic)이 아닌 고정값(416×416)으로 export할 것

## 파일 위치

| 파일 | 경로 | 비고 |
|---|---|---|
| PyTorch 원본 가중치 | `models/yolov8n.pt` | Ultralytics 공식 배포본 |
| ONNX 변환본 | `models/yolov8n_416.onnx` | 입력 shape 고정 |
| OpenVINO IR (FP32) | `models/openvino/fp32/yolov8n_416.xml` (+ `.bin`) | M2 추론 파이프라인에서 사용 |
| OpenVINO IR (INT8) | `models/openvino/int8/yolov8n_416.xml` (+ `.bin`) | M3에서 NNCF PTQ로 생성 |

## INT8 양자화 (M3)

- **방법**: NNCF(Neural Network Compression Framework) Post-Training Quantization(PTQ),
  재학습 없이 FP32 IR의 활성값 분포만 관찰해 quantization scale을 계산 (`nncf.quantize()`).
- **Calibration 데이터**: 저고도 oblique(비스듬한 각도) 드론 영상에서 균등 간격으로 샘플링한
  300프레임. 배포 시 마주칠 입력 분포와 유사한 소스를 쓰는 것이 원칙이며, 초기의 도메인
  갭이 컸던 수직(top-down) 항공뷰 영상은 calibration 소스로 쓰지 않았다.
- **구조 확인**: 입력/출력 텐서 shape이 FP32와 동일(`[1,3,416,416]` → `[1,84,3549]`) — 구조
  변경 없이 가중치/활성값 표현 방식만 바뀌었음을 확인했고,  `Detector`/
  `postprocess()`를 코드 수정 없이 그대로 재사용할 수 있다.
- **정확도 비교 방법**: 정답 라벨링 데이터셋이 없으므로 mAP는 측정하지 않았다. 대신 같은
  프레임에서 FP32/INT8 각각의 최고 confidence 탐지를 비교해 IoU≥0.5 + class_id 일치 여부를
  "결과 일치"로 판단하는 **탐지 결과 일치도** 지표를 사용했다 (`results/raw/fp32_vs_int8_detection_agreement.csv`).
  100프레임 기준 일치율 79.0%, 매칭된 프레임의 평균 confidence 차이(FP32−INT8) -0.0281.
- **Latency 비교**: warm-up 10회 + 측정 100회 평균 (`results/raw/fp32_vs_int8_latency.csv`).
  본 개발 환경(Intel CPU)에서 INT8이 FP32 대비 약 50~68% 낮은 평균 latency를 보였다 — 정식
  percentile/deadline-miss 분석은 M4에서 다룬다.

## 라이선스

- YOLOv8 코드/가중치: AGPL-3.0 (Ultralytics) — 개인 학습·포트폴리오 목적 사용, 배포 시 라이선스
  조건 확인 필요.
