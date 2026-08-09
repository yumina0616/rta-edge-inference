# ADR-0003: Python 추론 노드의 출력을 JSON Lines 스키마로 고정한다

## Status

Accepted — 2026-08-09

## Context

[ADR-0001](0001-select-yolov8n-model.md)/[ADR-0002](0002-fix-input-resolution.md)에서 모델과 입력 해상도를 확정했고, 이번 주(M2, README 3장의 Phase 1 필수 목표 범위)에는 영상 읽기 → 전처리 → OpenVINO 추론 → 후처리(confidence threshold + NMS + 좌표 역변환)까지 이어지는 Python
추론 파이프라인을 구현했다.(`src/inference_python/run_pipeline.py`)

이 파이프라인의 출력은 C++ Safety Supervisor가 그대로 파싱해서 상태 판단 (NORMAL/HOLD_REQUEST)에 쓰는 **프로세스 간 인터페이스 계약**이다. 한번 C++ 쪽 구현이 이 스키마에 의존하기 시작하면, 필드를 바꾸는 비용이 Python 쪽만 고치는 것보다 훨씬 커지기 때문에 지금 시점에 스키마를 명시적으로 고정해 둘 필요가 있다.

검토한 대안:

- **JSON 배열 한 번에 출력**: 전체 영상을 다 처리한 뒤 `[{...}, {...}]` 형태로 한 번에 출력. 구현은 단순하지만, 스트리밍이 안 되어 C++가 실시간으로 한 프레임씩 읽어들이는 구조와 맞지 않는다.
- **JSON Lines(JSONL), 프레임당 탐지 전체 배열 포함**: 한 줄에 하나의 프레임, 그 프레임의 모든 탐지 결과를 배열로 포함. Safety Supervisor 입장에서는 프레임당 값 하나(대표 confidence)만 필요한데, 매번 배열을 순회해야 해서 파싱이 불필요하게 복잡해진다.
- **JSON Lines(JSONL), 프레임당 최고 confidence 탐지 하나만 대표값으로 사용**: 채택안.

## Decision

Python 추론 노드는 프레임마다 아래 스키마의 JSON 객체 하나를 stdout에 한 줄씩 출력한다. 여러 탐지가 있으면 confidence가 가장 높은 것 하나만 대표값으로 싣는다.

```json
{"frame_id": 184, "timestamp_ms": 1785910200351, "confidence": 0.72,
 "bbox": [101, 84, 202, 190], "inference_latency_ms": 37.2, "valid": true}
```

- `frame_id`: 프레임 순번 (0부터 증가)
- `timestamp_ms`: 결과 생성 시각, epoch 기준 밀리초 (`time.time()`)
- `confidence`: 이 프레임의 최고 confidence 탐지값 (탐지가 없으면 `0.0`)
- `bbox`: 원본 이미지 좌표계 기준 `[x1, y1, x2, y2]` (탐지가 없으면 `null`)
- `inference_latency_ms`: 순수 추론 소요 시간, 구간 측정이므로 `time.perf_counter()` 사용
- `valid`: 유효한 탐지가 하나라도 있었는지 여부

각 줄 출력 직후 `sys.stdout.flush()`를 호출해 버퍼링 없이 즉시 내보낸다.

## Consequences

긍정적인 영향:

- 스트리밍 구조라 C++ Safety Supervisor가 파일 전체를 기다리지 않고 한 줄씩 실시간으로 소비할 수 있다.
- 저장해 둔 JSONL을 그대로 재생하면 5주차 fault injection 시험에서 동일 입력을 반복 재사용할 수 있다.
- Safety Supervisor는 탐지 배열을 순회할 필요 없이 `confidence` 필드 하나만 보면 되어 상태 판단 로직이 단순해진다.

부정적인 영향:

- 프레임에 탐지가 여러 개 있어도 최고 confidence 하나만 남김 -> 프레임 내 다중 객체 정보는 이 스트림만으로는 복원할 수 없다 (Phase 1 목표가 "여러 객체 각각을 추적"이 아니라 "이 프레임을 신뢰할 수 있는 상태로 볼 것인가"이므로 현재 범위에서는 허용 가능한 손실로 판단).
- 이후 필드를 추가/변경하려면 Python 출력과 C++ 파서 양쪽을 함께 수정해야 한다 — 인터페이스 계약이므로 임의로 변경하지 않는다.

## Related Artifacts

- `src/inference_python/run_pipeline.py`
- `README.md` 4장 (아키텍처, JSONL 인터페이스)
