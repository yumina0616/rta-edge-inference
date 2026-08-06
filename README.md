# Real-Time and Fault-Aware Edge AI Inference on Resource-Constrained Hardware
## 자원 제약 임베디드 시스템을 위한 실시간·고장 대응형 엣지 AI 추론 시스템

---

## 개요

자원이 제한된 임베디드 하드웨어(NVIDIA Jetson)를 타깃으로, 사전학습된 객체 인식 모델을 실시간
추론하고 그 결과를 감시하는 엣지 AI 시스템을 설계·검증하는 프로젝트다.

동일한 모델을 대상으로 OpenVINO NNCF 기반 FP32 → INT8 Post-Training Quantization을 적용해
정확도와 지연시간 변화를 정량 비교하고, 추론 결과의 confidence·timestamp·연속성을 감시하는
**C++ Safety Supervisor**를 구현해 NORMAL / HOLD_REQUEST 상태를 판단한다. 이 감시 구조는
자율·안전critical 시스템의 **Runtime Assurance(RTA)** 개념, 그중 Simplex Architecture의
아이디어를 참고했다.

요구사항 정의(EARS 패턴), 설계 결정(ADR), 고장 주입(fault injection) 시험, 요구사항-시험
추적성(traceability)까지 문서화해 항공 임베디드 소프트웨어의 요구사항 기반 개발 방식을 학습
목적으로 축소 적용했다.

> 본 프로젝트는 실제 비행 안전성이나 항공 인증(DO-178C 등)을 주장하지 않는다. AI 추론 모듈과
> 결정론적 안전 감시 소프트웨어를 통합하고, 그 성능과 한계를 실험적으로 검증하는 학습·포트폴리오
> 프로젝트다.

---

## 아키텍처

```text
[저장 영상] → [Inference Node (Python, OpenVINO)] → JSONL 스트림 → [Safety Supervisor (C++)] → [Benchmark & Logging (Python)]
```

Python Inference Node와 C++ Safety Supervisor는 JSON Lines 스트림으로 통신한다:

```json
{"frame_id": 184, "timestamp_ms": 1785910200351, "confidence": 0.72,
 "bbox": [101, 84, 202, 190], "inference_latency_ms": 37.2, "valid": true}
```

Safety Supervisor는 confidence, freshness(timeout), 상태 히스테리시스를 판단해 상태를 출력하고,
모든 상태 전이를 timestamp·원인과 함께 로깅한다. RTA/Simplex Architecture에서 아이디어를 가져온
감시 구조이며, 실제 안전 컨트롤러로의 전환 메커니즘은 구현하지 않는다.

---

## 범위

**Phase 1 — MVP (Intel CPU/OpenVINO 기준 호스트 프로토타입)**

| 영역 | 내용 |
|---|---|
| 모델 | 표준 소형 모델(YOLOv8n) 선정 및 고정 해상도 추론 파이프라인 |
| 양자화 | OpenVINO NNCF FP32 → INT8 Post-Training Quantization, 정확도·지연시간 비교 |
| 벤치마크 | 지연시간 분포(mean/median/p95/p99, deadline miss ratio) 자동화 측정 |
| Safety Supervisor | C++ 최소 버전 (NORMAL/HOLD_REQUEST, 히스테리시스 포함) |
| 검증 | Fault injection 2종 자동화 시험 |
| 문서화 | EARS 기반 요구사항 문서 + 추적표(traceability matrix) |

**Phase 2 — 확장 목표 (Jetson 타깃, 여력이 될 때만)**

| 영역 | 내용 |
|---|---|
| 양자화/실측 | TensorRT 기반 FP16/INT8 엔진, Jetson 실측 |
| Safety Supervisor | 4-state 확장 (DEGRADED/FAULT 추가) |
| 검증 | Fault injection 7종으로 확장, 발열·동시부하 시험 |
| 입력/인터페이스 | 실시간 카메라 입력, ROS 2 인터페이스 |

Phase 1을 완결한 뒤에만 Phase 2로 진행하며, Phase 1만으로도 독립적으로 완결된 결과물로 취급한다.

---

## 검증 방식

- **요구사항**: EARS(Easy Approach to Requirements Syntax) 패턴으로 작성(`requirements/software_requirements.md`), 각 요구사항을 테스트·`traceability_matrix.csv`와 연결
- **설계 결정**: 모델 선정, 양자화 방식, 임계값 근거 등 주요 판단을 ADR(Architecture Decision Record)로 기록(`docs/adr/`)
- **Fault Injection**: 낮은 confidence, 결과 스트림 중단 등 결함을 의도적으로 주입해 Safety Supervisor의 상태 전환 로직을 검증
- **벤치마크**: 동일 플랫폼 내부 비교(FP32 vs INT8)를 원칙으로 latency 분포와 deadline miss ratio를 측정 — WCET 증명이 아닌 경험적 실행시간 특성화(Empirical Timing Characterization)

---

## 저장소 구조

```text
rta-edge-inference/
├── README.md
├── requirements/
│   ├── software_requirements.md
│   └── traceability_matrix.csv
├── models/
│   └── model_manifest.md
├── src/
│   ├── inference_python/
│   ├── safety_supervisor_cpp/
│   └── common_interfaces/
├── benchmark/
│   ├── openvino/
│   ├── tensorrt/          # Phase 2
│   ├── end_to_end/
│   └── analyze_results.py
├── tests/
│   ├── unit/
│   └── fault_injection/
├── configs/
├── results/
│   ├── raw/
│   ├── figures/
│   └── summary.csv
└── docs/
    ├── architecture.md
    ├── test_plan.md
    ├── verification_report.md
    ├── limitations.md
    └── adr/
```

---

## 한계

본 프로젝트는 항공 인증 또는 DO-178C 준수를 주장하지 않으며, 항공 소프트웨어의 요구사항 기반
개발·검증 개념을 학습 목적으로 축소 적용한 프로토타입이다. Safety Supervisor는 실제 비행제어를
수행하지 않으며, 상위 시스템이 참고할 수 있는 안전 상태 요청(HOLD_REQUEST 등)을 출력하는 데
그친다.
