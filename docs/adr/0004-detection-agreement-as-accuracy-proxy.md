# ADR-0004: FP32 vs INT8 "정확도" 비교를 mAP 대신 탐지 결과 일치도로 정의한다

## Status

Accepted — 2026-08-13

## Context

이번 주(M3, README 3장의 Phase 1 필수 목표 범위)는 NNCF Post-Training Quantization(PTQ)으로
FP32 OpenVINO IR을 INT8로 변환하고, 두 모델의 "정확도"와 latency를 비교하는 것이 목표다.

일반적으로 객체 탐지 모델의 정확도는 mAP(mean Average Precision)로 측정하지만, 이를 계산하려면
정답 bbox(ground truth annotation)가 있는 라벨링된 데이터셋이 필요하다. 이 프로젝트의 Phase 1
범위(M1~M8, README 3장)에는 라벨링 작업이 포함되어 있지 않다. 라벨링 작업을 지금 추가하는 것은
일정과 스코프를 크게 벗어나며, "주어진 pretrained 모델을 자원 제약 환경에 최적화해 배포하는 것"이라는
이 프로젝트의 핵심 목적과도 맞지 않는다.

검토한 대안:

- **소규모 수동 라벨링 후 mAP 계산**: 표준 지표를 쓸 수 있다는 장점이 있으나, 라벨링 자체가
  Phase 1 스코프 밖의 작업을 새로 만드는 것이고, 소규모 라벨로 계산한 mAP는 통계적으로도 신뢰하기
  어렵다.
- **공개 라벨링 데이터셋(COCO val 등)으로 대체 측정**: 이 프로젝트의 실제 배포 시나리오(저고도
  oblique 드론 영상)와 입력 분포가 다르므로, 측정한 mAP가 실제 관심 대상인 "이 프로젝트의 실사용
  조건에서 quantization이 결과를 얼마나 흔드는가"를 반영하지 못한다.
- **FP32 vs INT8 탐지 결과 일치도 비교(채택안)**: 정답 라벨 없이도, 같은 입력에 대해 두 모델이
  얼마나 일관된 결과를 내는지는 직접 측정할 수 있다.

## Decision

정답 라벨이 없는 상태에서 "정확도"라는 표현 대신, 같은 프레임 집합에서 FP32와 INT8이 얼마나
일치하는 탐지 결과를 내는지를 다음 기준으로 정의해 측정한다 (`src/inference_python/compare_detections.py`):

1. 같은 프레임에서 FP32와 INT8 각각의 최고 confidence 탐지 하나씩을 비교 대상으로 삼는다.
2. `class_id`가 같고, bbox IoU가 임계값(0.5) 이상이면 "매칭(결과 일치)"으로 판단한다.
3. 프레임 N개 중 매칭된 비율(매칭률)과, 매칭된 쌍들의 평균 confidence 차이(FP32−INT8)를 함께
   보고한다.

이 지표는 "모델이 정답을 얼마나 맞췄는가"가 아니라 "quantization으로 인해 결과가 얼마나
바뀌었는가"를 보는 지표이며, 모든 문서(README, `docs/`, `models/model_manifest.md`, 커밋 메시지)에서
"mAP를 측정했다"처럼 실제로 하지 않은 것을 한 것처럼 쓰지 않는다 — 이 프로젝트의 정직성 원칙과
직결된다.

## Consequences

긍정적인 영향:

- 라벨링 작업 없이 Phase 1 일정 안에서 quantization의 실질적 영향(결과 안정성)을 측정할 수 있다.
- 실제 배포 시나리오와 동일한 입력 분포(oblique 저고도 영상)에서 측정하므로, 공개 데이터셋 기반
  mAP보다 이 프로젝트의 실사용 조건을 더 잘 반영한다.

부정적인 영향:

- 표준 mAP와 비교 가능한 절대적 정확도 수치는 얻을 수 없다 — "탐지 결과가 안정적이다"와 "탐지가
  실제로 정확하다"는 다른 주장이며, 이 구분을 항상 명시해야 한다.
- 프레임당 최고 confidence 탐지 하나만 비교하므로(ADR-0003의 JSONL 스키마와 동일한 단순화),
  한 프레임에 여러 객체가 있을 때 두 번째 이후 탐지의 변화는 이 지표로 드러나지 않는다.
- 이후 라벨링된 데이터셋이 생기면 이 지표를 mAP 기반 비교로 대체하거나 보완할 수 있으나, 현재
  Phase 1/Phase 2 스코프에는 포함되어 있지 않다.

## Related Artifacts

- `src/inference_python/compare_detections.py`
- `models/model_manifest.md` (INT8 양자화 절)
- `results/raw/fp32_vs_int8_detection_agreement.csv`
