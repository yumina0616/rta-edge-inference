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
| OpenVINO IR (INT8) | `models/openvino/int8/yolov8n_416.xml` (+ `.bin`) | M3에서 생성 예정 |

## 라이선스

- YOLOv8 코드/가중치: AGPL-3.0 (Ultralytics) — 개인 학습·포트폴리오 목적 사용, 배포 시 라이선스
  조건 확인 필요.
