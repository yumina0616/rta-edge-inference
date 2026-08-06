# Real-Time and Fault-Aware Edge AI Inference on Resource-Constrained Hardware
## 자원 제약 임베디드 시스템을 위한 실시간·고장 대응형 엣지 AI 추론 시스템

---

## 개요

객체 탐지 모델을 OpenVINO로 최적화(FP32/INT8)하고, 그 추론 결과가 멈추거나 신뢰할 수 없는
상태가 됐을 때 이를 감지하는 C++ Safety Supervisor를 구현하는 엣지 AI 소프트웨어 프로젝트다.
자원이 제한된 임베디드 하드웨어(NVIDIA Jetson)를 최종 타깃으로 한다.

**핵심 기능**
- OpenVINO FP32 vs INT8(Post-Training Quantization) 추론 비교
- Latency 분포(mean/median/p95/p99) 및 deadline miss ratio 측정
- Python(추론) ↔ C++(Safety Supervisor) 간 JSONL 인터페이스
- Timeout·confidence 기반 상태 감시 (`NORMAL` / `HOLD_REQUEST`)
- Fault injection 자동 시험
- EARS 기반 요구사항 - 시험 추적성(traceability)

---

## 진행 상황

- [x] YOLOv8n → ONNX export
- [x] ONNX → OpenVINO FP32 IR 변환
- [ ] 저장 영상 기반 추론 파이프라인 (진행 중)
- [ ] INT8 Post-Training Quantization
- [ ] 벤치마크 자동화
- [ ] C++ Safety Supervisor
- [ ] Fault injection 자동 시험
- [ ] 요구사항 문서 + traceability matrix
- [ ] (Phase 2) Jetson/TensorRT 실측

---

## 가정 시나리오

소형 UAV의 카메라 영상에서 사람·차량·자전거와 같은 잠재적 위험 후보 객체를 탐지한다고 가정한다.
본 프로젝트는 거리·상대속도·충돌 가능성을 계산하지 않으며, 탐지 결과는 상위 위험 평가 시스템이
사용할 입력 후보로만 제공한다.

**Safety Supervisor는 탐지 내용이 실제로 맞는지는 보증하지 않는다** — confidence가 높다고 해서
탐지가 항상 옳은 건 아니기 때문이다. Safety Supervisor가 실제로 확인하는 것은:

- 결과 메시지가 제시간에 도착했는가 (freshness)
- 메시지 필드가 정상 형식인가
- confidence가 설정된 임계값을 넘는가
- timestamp가 오래되지 않았는가
- 추론 노드가 살아 있는가 (연속성)

즉 "탐지가 맞다"가 아니라 **"이 인식 스트림을 지금 신뢰할 만한 상태인가"**를 감시한다. 신뢰할
수 없다고 판단되면 `HOLD_REQUEST`를 출력해 상위 비행 제어 시스템이 안전한 대응(정지·호버링·복귀
등)을 하도록 요청한다. Safety Supervisor는 이 상태를 **출력**하는 데 그치고 실제 비행 제어를
수행하지 않는다.

객체 인식 모델은 COCO 사전학습 가중치를 그대로 사용하며, person/car/bicycle 등 일부 클래스를
지상 장애물의 대표 사례로 다룬다. 실제 UAV 안전 시스템이라면 이 클래스 구성을 도메인에 맞게
재구성해야 하지만, 이 프로젝트는 탐지 모델의 정확도 자체보다 **자원 제약 환경에서의 추론
파이프라인과 안전 감시 구조**에 초점을 맞추므로 모델 재학습 없이 COCO pretrained를 그대로
사용한다.

---

## 아키텍처

```text
[저장 영상]
     │
     ▼
[Inference Node — Python, OpenVINO] ──inference metrics──┐
     │ JSONL                                              │
     ▼                                                     ▼
[Safety Supervisor — C++] ──state transition logs──▶ [Benchmark & Logging — Python]
     │
     ▼
NORMAL / HOLD_REQUEST
```

Python Inference Node와 C++ Safety Supervisor는 JSON Lines 스트림으로 통신한다:

```json
{"frame_id": 184, "timestamp_ms": 1785910200351, "confidence": 0.72,
 "bbox": [101, 84, 202, 190], "inference_latency_ms": 37.2, "valid": true}
```

Benchmark & Logging은 Safety Supervisor의 출력만 받는 게 아니라, Inference Node의 latency
지표와 Safety Supervisor의 상태 전이 로그를 각각 수집해 분석한다 — Supervisor 뒤에 일렬로
연결된 마지막 단계가 아니라, 두 모듈을 함께 관찰하는 별도 수집기다.

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

이 프로젝트를 통해 실제로 연습해보고 싶었던 항공 소프트웨어 분야 개념들이 검증 방식 곳곳에
들어가 있다:

- **Runtime Assurance (RTA) / Simplex Architecture-inspired 감시 구조** — 정확도를 형식적으로
  증명할 수 없는 AI 컴포넌트를 안전critical 루프에 넣을 때, 그 출력을 계속 신뢰해도 되는지
  별도의 검증된 모니터가 감시하는 아키텍처 패턴 → C++ Safety Supervisor
- **EARS 기반 요구사항 작성 + Traceability** — 요구사항을 표준 문장 패턴(EARS)으로 쓰고, 각
  요구사항을 테스트 결과와 연결 → `requirements/software_requirements.md`,
  `traceability_matrix.csv`
- **ADR (Architecture Decision Record)** — 모델 선정, 양자화 방식, 임계값 근거 같은 주요
  기술적 판단을 맥락·대안·근거와 함께 기록 → `docs/adr/`
- **Fault Injection** — 낮은 confidence, 결과 스트림 중단 등 결함을 의도적으로 주입해 Safety
  Supervisor의 상태 전환 로직을 검증
- **Empirical Timing Characterization** — "빠르다/느리다"가 아니라 p95/p99/deadline miss
  ratio 같은 정량 지표로 실시간성을 분석 (WCET 증명은 아님)
- **SWaP-C를 의식한 모델 최적화** — FP32 → INT8 양자화로 정확도·지연시간·자원 사용량 사이의
  트레이드오프를 정량적으로 실험

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

## 결과

Phase 1 완료 후 채워질 예정.

| 모델 | mAP | Median latency | p99 latency | Deadline miss ratio |
|---|---|---|---|---|
| FP32 | TBD | TBD | TBD | TBD |
| INT8 | TBD | TBD | TBD | TBD |

---

## 실행 방법

현재까지 동작이 확인된 건 모델 export까지다. 전체 파이프라인 재현 커맨드는 M2(저장 영상 추론
파이프라인) 완료 후 이 섹션에 추가된다.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install ultralytics openvino

python src/inference_python/export_model.py
```

---

## 한계

본 프로젝트는 항공 인증 또는 DO-178C 준수를 주장하지 않으며, 항공 소프트웨어의 요구사항 기반
개발·검증 개념을 학습 목적으로 축소 적용한 프로토타입이다. Safety Supervisor는 실제 비행제어를
수행하지 않으며, 상위 시스템이 참고할 수 있는 안전 상태 요청(HOLD_REQUEST 등)을 출력하는 데
그친다.
