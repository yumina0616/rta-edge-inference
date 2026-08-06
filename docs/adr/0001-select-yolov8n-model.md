# ADR-0001: 객체 탐지 모델로 YOLOv8n을 사용한다

## Status

Accepted — 2026-08-05

## Context

이 프로젝트는 두 단계로 나뉜다. **Phase 1**은 Intel CPU + OpenVINO 기준 호스트 프로토타입(필수 목표, MVP)이고, **Phase 2**는 Phase 1을 완료한 뒤 진행하는 확장 목표로 실제 NVIDIA Jetson 임베디드 하드웨어에서 TensorRT로 실측하는 단계다(범위 정의는 README 3장 참고). 이 ADR은 Phase 1단계의 모델 선정을 다룬다.

Phase 1은 결국 Phase 2(자원 제약이 훨씬 뚜렷한 Jetson)로 이어지는 것을 염두에 두고 실시간 추론 파이프라인을 구축하는 것이 목표다. 자원 제약 하에서 실시간성을 확보해야 하므로, 파라미터 수가 적어 연산량이 작은 모델이 유리하다.

검토한 대안:

- **YOLOv8s/m/l/x**: 같은 계열의 상위 변형. 크기가 커질수록(s->m->l->x) 정확도(mAP)는 높지만 파라미터·연산량이 크기 때문에 "자원 제약 하 실시간성 확보"라는 프로젝트 목표와 어긋난다고 판단.
- **YOLO-World 등 open-vocabulary 계열**: 임의의 텍스트 프롬프트로 클래스를 지정할 수
  있어 유연하지만, ONNX/INT8 변환 경로가 표준 YOLOv8 대비 덜 검증되어 있어 변환 리스크가 큼.

결론: 이 프로젝트의 핵심은 모델 자체의 정확도를 연구하는 것이 아니라, 주어진 모델을 자원 제약 환경에서 실시간으로 운용하고 감시하는 파이프라인을 만드는 것이다.

## Decision

Phase 1의 객체 탐지 모델로 **YOLOv8n**(Ultralytics, COCO pretrained)을 사용한다.

## Consequences

긍정적인 영향:

- YOLOv8 계열 중 파라미터 수가 가장 적어 자원 제약 환경에 가장 유리하다.
- anchor-free 구조라 후처리(NMS 등)가 비교적 단순하다.
- Ultralytics 공식 export 경로가 잘 정비되어 있어 ONNX/OpenVINO 변환 리스크가 낮다.

부정적인 영향:

- 상위 변형(s/m/l/x) 대비 정확도(mAP)가 낮다 — 이 프로젝트는 정확도 최적화가 목표라기보다는, 제한적인 환경에서 정확도와 더불어 속도, 실시간성을 모두 다루어야한다. 따라서 정확도는 감수 가능한 트레이드오프로 판단된다.
- COCO 80개 클래스 밖의 객체는 탐지할 수 없다 (open-vocabulary가 아님).

후속 작업:

- 입력 해상도 확정 → [ADR-0002](0002-fix-input-resolution.md)
- ONNX/OpenVINO IR 변환 검증

## Related Artifacts

- `models/model_manifest.md`
- `README.md` 3장 (프로젝트 범위, Phase 1/Phase 2 정의)
