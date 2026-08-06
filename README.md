# 프로젝트 기획서

## Real-Time and Fault-Aware Edge AI Inference on Resource-Constrained Hardware
### 자원 제약 임베디드 시스템을 위한 실시간·고장 대응형 엣지 AI 추론 시스템

작성일: 2026-08-05
프로젝트 성격: **개인 프로젝트** (팀 캡스톤과 무관, 독립 진행)

---

## 0. 프로젝트 개요

본 프로젝트는 자원이 제한된 임베디드 하드웨어(NVIDIA Jetson)에서 사전학습된 객체 인식 모델을
실시간으로 실행하기 위한 엣지 AI 추론 시스템을 설계하고 검증한다.

동일한 원본 모델을 대상으로 **OpenVINO NNCF**와 **TensorRT** 기반의 독립적인 양자화·최적화
경로를 각각 구축하고, 정확도, 지연시간, deadline miss ratio, 메모리 사용량, 전력 및 열적 조건에
따른 성능 변화를 측정한다.

또한 추론 결과의 confidence, timestamp, latency, 연속성 및 heartbeat를 감시하는 **C++ Safety
Supervisor**를 구현하여 정상, 성능 저하, 정지 요청, 고장 상태를 출력한다. 이 구조는 자율/안전critical
시스템 분야의 **Runtime Assurance (RTA)** 아키텍처 패턴, 그중에서도 **Simplex Architecture**의
기본 아이디어를 참고했다 (단, 실제 안전 컨트롤러로의 전환 메커니즘은 구현하지 않으므로
"RTA/Simplex-inspired"로 표현한다 — 4장 참고). 요구사항, 설계, 단위시험, 고장 주입(fault injection)
시험 및 측정 결과를 추적 가능한 형태로 문서화함으로써, 항공 임베디드 소프트웨어의 요구사항 기반
개발(requirements-based development)과 요구사항-설계-시험 추적성(traceability) 개념을 축소 적용한다.

> **한계 명시**: 본 프로젝트는 실제 비행 안전성이나 항공 인증(DO-178C 등) 준수를 주장하지 않으며,
> AI 추론 모듈과 결정론적 안전 감시 소프트웨어를 통합하고 그 성능과 한계를 실험적으로 검증하는
> 독립형 학습·포트폴리오 프로젝트다.

---

## 1. 배경 및 동기

### 1.1 커리어 배경
- 목표 직무: Flight Control Systems / Avionics Integration Engineer
- 목표 분야: 민항기 GNC/비행제어 소프트웨어, 항공 임베디드 시스템 통합
- 대학원 진학 목표: ISAE-SUPAERO 등 해외 항공 특화 프로그램

### 1.2 이 프로젝트가 필요한 이유
- 항공 임베디드 소프트웨어 직무는 실시간성·자원 제약 환경에서 소프트웨어를 최적화해 돌리는
  역량을 요구함 (RTOS, ARINC 653 파티셔닝 등). 이 문제는 항공·방위산업 전반에서
  **SWaP-C (Size, Weight, Power, and Cost)** 제약이라는 이름으로 정식화되어 다뤄짐
- OpenVINO DevCon 2026을 개인적으로 수강했고, 학습한 내용(양자화/quantization, NNCF, 모델
  압축/model compression)을 단순 수료로 끝내지 않고 실제 엔지니어링 산출물로 전환하고자 함
- **EASA Artificial Intelligence Concept Paper**, **FAA Roadmap for Artificial Intelligence
  Safety Assurance** 등 항공 분야의 AI 도입 흐름은 "모델이 얼마나 빠른가"보다 "모델이 언제
  실패하고, 실패를 어떻게 감지하며, 실패해도 시스템이 안전한가"를 중시하며, 이는 공학적으로
  **Runtime Assurance (RTA)** 개념과 연결됨 — 이 프로젝트는 이 관점을 직접 실습하는 것을 목표로 함

### 1.3 캡스톤 프로젝트와의 관계
- 팀 캡스톤(VLA-inspired 드론 자율 미션 시스템)은 **이 기획과 무관하게 원안 그대로 진행**
- 본 프로젝트는 캡스톤에서 다루는 문제의식(자원 제약 하 실시간 비전 추론)을 **개인 프로젝트로
  독립적으로 재구성**한 것이며, 결과물이 성숙하면 캡스톤에 참고자료로 역으로 활용될 수 있음
  (역방향 의존성은 없음)

---

## 2. 프로젝트 목표

### 2.1 핵심 정체성
> AI 모델 연구 프로젝트가 아니라, **자원 제약 환경에서 AI 추론 시스템을 배포하고, 성능·고장
> 대응·검증 근거까지 만드는 임베디드 소프트웨어 프로젝트**

### 2.2 최종적으로 남기고자 하는 것

**Phase 1 완료 시 (필수 확보)**
1. AI 모델 최적화(양자화) 실험 경험과 정량 데이터 (Intel CPU/OpenVINO 기준)
2. C++ 안전 감시 소프트웨어(Safety Supervisor) 구현 경험
3. 요구사항 기반 개발·검증·문서화 경험
4. GitHub 저장소 + 결과 정리 글(README/블로그) — 이력서·포트폴리오·대학원 지원서에 활용 가능한 형태

**Phase 2까지 완료 시 (추가 확보)**
5. NVIDIA Jetson 임베디드 타깃 배포 및 실측 경험 (TensorRT 포함)

> 주의: "Jetson 임베디드 배포 경험"은 Phase 2(E1)가 완료되어야 확보되는 결과다. Phase 1만
> 완료한 상태에서는 이 항목을 이력서·README에 기재하지 않는다. Phase 1은 Intel CPU 환경
> 기준의 **호스트 프로토타입(host prototype)**이며, 이 자체로도 독립적으로 완결된 결과물이다.

---

## 3. 범위 정의 (필수 목표 → 확장 목표 순차 진행)

> **진행 원칙**: 아래 "3.1 필수 목표(MVP)"를 전부 완료하고 동작을 확인한 뒤에만
> "3.2 확장 목표"로 넘어간다. 필수 목표가 끝나지 않은 상태에서 확장 목표 항목에 손대지 않는다.
> 이는 개인 프로젝트가 환경 구축만 하다 끝나는 것을 방지하기 위한 핵심 원칙이다.

### 3.1 필수 목표 (Phase 1 — MVP)

| # | 항목 | 완료 기준 |
|---|---|---|
| M1 | 표준 소형 모델(YOLOv8n 등) 하나 선정, 고정 입력 해상도 확정 | 모델·해상도 확정 및 `model_manifest.md` 작성 |
| M2 | 저장 영상(사전 녹화) 기반 추론 파이프라인 구축 (실시간 카메라 아님) | 저장 영상 입력 → 추론 결과 출력까지 동작 |
| M3 | OpenVINO NNCF로 FP32 대비 INT8 **Post-Training Quantization (PTQ)** 적용 및 정확도·latency 비교 | 동일 validation set에서 두 결과 수치 확보 |
| M4 | 벤치마크 자동화 스크립트 (mean/median/p95/p99/observed max, deadline miss ratio — **Empirical Timing Characterization**) | 스크립트 실행 시 결과 CSV 자동 생성 |
| M5 | C++ Safety Supervisor 최소 버전 구현 (상태: NORMAL / HOLD_REQUEST 2개만) — **Runtime Assurance (RTA) monitor**의 축소형 | confidence 임계값 + timeout 조건으로 상태 전이 동작 |
| M6 | Fault injection 테스트 최소 2종 (confidence 저하, 결과 중단) 자동화 | pytest 또는 C++ 단위테스트로 재현 가능 |
| M7 | 요구사항 문서 초안 (OBJ-*, SWR-* 5개 내외, **EARS (Easy Approach to Requirements Syntax)** 패턴 적용) + 추적표(**traceability matrix**) | `software_requirements.md`, `traceability_matrix.csv` 작성 |
| M8 | 결과 및 한계 문서 (`limitations.md`) | 무엇을 검증했고 무엇을 검증하지 않았는지 명시 |

**Phase 1 완료 정의(Definition of Done)**: M1~M8이 모두 재현 가능한 스크립트/코드로 존재하고,
README에서 "python run_pipeline.py" 한 번으로 전체 흐름(추론 → 양자화 비교 → 상태 판단 → 결과 저장)이
재현될 것.

### 3.2 확장 목표 (Phase 2 — 여력이 될 때만 진행)

| # | 항목 | 선행 조건 |
|---|---|---|
| E1 | TensorRT FP16/INT8 엔진 구축, Jetson 실측 (동일 ONNX·calibration·validation 기준 유지) | Phase 1 완료 |
| E2 | Safety Supervisor 상태 확장 (NORMAL/DEGRADED/HOLD_REQUEST/FAULT 4단계), Persistence/Freshness/Plausibility/Heartbeat 판단 조건 추가 — **Perception Simplex Architecture** 개념에 더 근접하게 심화 | E1 또는 Phase 1 완료 |
| E3 | Fault injection 시험 세트 확장 (7종: confidence 저하, 결과 중단, heartbeat 중단, 오래된 timestamp, deadline 초과, bbox 급변, 정상 복귀) | E2 |
| E4 | 발열·동시 부하 시험 (NVIDIA `tegrastats` 로깅, power mode별 비교, 장시간 반복 추론) — **SWaP-C** 중 Power/Thermal 축 실측 | E1 |
| E5 | 실시간 카메라(USB/CSI) 입력으로 전환 | Phase 1 완료 |
| E6 | YOLO-World로 모델 확장 (reparameterized 버전, bbox_decoder 제외 export 등 사전 위험요소 대응) | Phase 1, E1 완료 |
| E7 | ROS 2 통신 인터페이스 추가 | Phase 1 완료, 필요시에만 |
| E8 | Docker 기반 재현 가능한 개발 환경 | 아무 때나 병행 가능 (선택) |

**중요**: E1~E8은 우선순위가 아니라 "완료 시 가산점"에 가까운 항목들이다. 시간이 부족하면
Phase 1만으로 프로젝트를 마무리하고 README에 "Future Work"로 E1~E8을 남기는 것으로 충분하다.
Phase 1만 완결도 있게 끝내는 것이 Phase 1+2를 어설프게 걸치는 것보다 포트폴리오 가치가 높다.

---

## 4. 시스템 아키텍처

```text
[저장 영상 / (Phase 2: 실시간 카메라)]
        │
        ▼
[Inference Node — Python]
   - 모델: YOLOv8n 등 (Phase 2: YOLO-World)
   - 런타임: OpenVINO(CPU) / (Phase 2: TensorRT on Jetson)
   - 출력: bbox, confidence, timestamp, inference latency
        │
        ▼
[Safety Supervisor — C++]
   - 입력: 추론 결과 스트림 + heartbeat
   - 판단: confidence, freshness, timing, (Phase 2: persistence, plausibility)
   - 출력 상태: NORMAL / HOLD_REQUEST / (Phase 2: DEGRADED / FAULT)
   - 모든 상태 전이는 timestamp, 이전상태, 다음상태, 전이 원인과 함께 로깅
        │
        ▼
[Benchmark & Logging — Python]
   - latency 분포(mean/median/p95/p99/observed max)
   - deadline miss ratio
   - (Phase 2: 온도, 전력, 클럭 시계열)
```

핵심 설계 원칙:
- 모델 준비·변환·양자화는 Python 툴체인(OpenVINO/TensorRT 공식 API) 그대로 사용
- 실시간성·안전 판단이 중요한 Safety Supervisor는 **처음부터 C++로 설계**
- 두 모듈 간 인터페이스(추론 결과 스키마, heartbeat 프로토콜)를 명확히 문서화

### 4.1 Python-C++ 인터페이스 (Phase 1: JSON Lines, Phase 2: ROS 2로 전환 가능)

Phase 1에서는 ROS 2 없이 **JSON Lines(JSONL) 스트림**으로 두 모듈을 연결한다. Python
Inference Node가 결과를 stdout 또는 파일로 한 줄씩 출력하고, C++ Safety Supervisor가 이를
읽는 구조다.

```json
{"frame_id": 184, "timestamp_ms": 1785910200351, "confidence": 0.72,
 "bbox": [101, 84, 202, 190], "inference_latency_ms": 37.2, "valid": true}
```

장점: ROS 2 의존성 없이 스코프 관리 가능, 기록된 결과를 반복 재생(replay) 가능해 fault
injection이 쉬움, C++ 쪽만 독립적으로 단위시험 가능, 인터페이스 스키마가 파일 하나로 명확히
문서화됨. Phase 2에서 필요해지면 이 스키마를 ROS 2 메시지로 그대로 옮긴다(E7).

**아키텍처-개념 매핑**: 위 구조에서 [Inference Node]가 "검증되지 않은 고성능 컴포넌트(unverified
advanced component)", [Safety Supervisor]가 "검증된 런타임 모니터(verified runtime monitor)"에
해당하며, 이 둘의 조합은 **Runtime Assurance (RTA)** 아키텍처 패턴, 그중에서도 **Simplex
Architecture**의 기본 아이디어를 참고한 것이다.

> **정확한 표현 주의**: 고전적인 Simplex/Perception Simplex 구조는 이상 감지 시 검증된 안전
> 컨트롤러(또는 fallback perception)로 **실제 제어권을 전환하는 메커니즘**까지 포함한다. 본
> 프로젝트는 이상을 감지해 `HOLD_REQUEST` 등 상태를 **출력**하는 데 그치고, 실제 전환 메커니즘은
> 구현하지 않는다. 따라서 "Simplex Architecture를 구현했다"고 쓰지 않고, **"RTA-inspired
> Safety Supervisor"** 또는 **"Simplex-inspired runtime monitoring structure"**로 표현한다.
> Phase 2에서 실제 fallback(예: 경량 baseline 모델로 전환)을 추가하면 Simplex 구조에 더 가까워진다.

---

## 5. 요구사항 (Phase 1 기준 초안)

> 설계 목표(OBJ-*)는 프로젝트 내부에서 임의로 선정한 실험 목표이며, 소프트웨어 요구사항(SWR-*)은
> 실제 테스트로 검증 가능한 항목이다. 실제 임무·기체가 없으므로 이 둘을 구분해서 표기한다.
>
> **정확한 표현 주의**: 항공 시스템 개발에서 System Requirements는 **ARP4754A**(항공기→시스템
> →아이템 수준 요구사항 배분을 다루는 시스템 개발 지침)의 영역이고, **DO-178C**는 그렇게 배분된
> 시스템 요구사항을 소프트웨어 High-Level Requirements(HLR)로 정의하고 이를 구현 가능한
> Low-Level Requirements(LLR)로 분해하는 소프트웨어 생명주기를 다룬다. 이 2단 구조(OBJ-*/SWR-*)는
> "DO-178C가 System→High-Level→Low-Level을 계층화한다"는 부정확한 설명이 아니라, **"ARP4754A의
> 시스템 요구사항 배분 개념과 DO-178C의 요구사항-설계-코드-시험 추적성(traceability) 개념을 학습
> 목적으로 축소 적용한 것"**으로 표현한다.

### 5.1 작성 표준 — EARS (Easy Approach to Requirements Syntax)

모든 SWR-* 요구사항은 **EARS**(Rolls-Royce 개발, Airbus/NASA/Honeywell/Intel 등 채택)의 문장
패턴을 따라 작성한다. 대표 패턴:
- **State-driven**: "While [상태], the system shall [동작]"
- **Unwanted behavior**: "If [조건], then the system shall [동작]"
- **Event-driven**: "When [트리거], the system shall [동작]"

예: SWR-SAF-002 → *"While the Safety Supervisor is in NORMAL state, if no valid detection is
received for 1000 ms, then the Safety Supervisor shall transition to HOLD_REQUEST state."*

| ID | 내용 | 유형 |
|---|---|---|
| OBJ-PER-001 | 시스템은 10Hz 입력 스트림 처리를 성능 목표로 한다 | 설계 목표 |
| SWR-PER-001 | 지정된 Phase 1 시험 환경에서 Safety Supervisor의 관측된 상태 출력 지연시간은 모든 시험 샘플에서 5ms 이하이어야 한다 | 검증 가능 요구사항 (EARS: Event-driven) |
| SWR-SAF-001 | confidence가 설정 임계값 미만인 결과는 valid detection으로 처리하지 않는다 | 검증 가능 요구사항 (EARS: Unwanted behavior) |
| SWR-SAF-002 | While NORMAL 상태에서 1.0초 이상 valid detection이 수신되지 않으면 HOLD_REQUEST 상태를 출력해야 한다 | 검증 가능 요구사항 (EARS: State-driven) |
| SWR-SAF-002b | While HOLD_REQUEST 상태에서 valid detection이 연속 3회 수신되면 NORMAL 상태로 복귀해야 한다 | 검증 가능 요구사항 (EARS: State-driven, hysteresis) |
| SWR-LOG-001 | 모든 상태 전이는 timestamp, 이전 상태, 다음 상태, 전이 원인과 함께 기록되어야 한다 | 검증 가능 요구사항 (EARS: Ubiquitous) |
| SWR-SAF-003 (Phase 2) | 500ms 이상 heartbeat 미수신 시 FAULT 상태를 출력해야 한다 | 검증 가능 요구사항 (EARS: State-driven) |
| SWR-SAF-004 (Phase 2) | NORMAL 복귀를 위해서는 연속 10프레임 중 8개 이상 valid detection이 필요하다 | 검증 가능 요구사항 (EARS: State-driven) |

> **정확한 표현 주의**: 일반 Linux 환경(RTOS 아님)에서는 실시간 스케줄링 보장이 없으므로
> "5ms 이내에 생성해야 한다"는 형식적 보장으로 읽히지 않도록, SWR-PER-001을 "지정된 시험
> 환경에서 관측된 지연시간이 5ms 이하였다"는 **실험 결과 기반 요구사항**으로 명시한다.

각 요구사항은 `traceability_matrix.csv`에서 대응 테스트 ID와 PASS/FAIL 결과로 연결한다
(**requirements-to-test traceability** — 안전critical 소프트웨어 검증에서 널리 쓰이는 개념이며,
DO-178C를 포함한 여러 표준에서 유사한 형태로 요구된다. "DO-178C가 이 방식을 요구한다"는 인증
주장이 아니라, 그 개념을 학습 목적으로 참고했다는 의미로만 사용한다).

---

## 6. 상태머신 (Phase 1: 2-state / Phase 2: 4-state로 확장)

> 이 상태머신은 **Runtime Assurance (RTA)** 아키텍처에서 모니터가 "정상 동작 → 안전 상태로 전환
> (switch)"을 결정하는 로직의 축소판이다. Phase 2에서 상태를 4단계로 확장하는 것은 Simplex
> Architecture 계열 연구(예: Control Simplex, Perception Simplex)에서 다루는 전환 조건의
> 세분화 방향과 일치한다.

**Phase 1 최소 버전 (히스테리시스 포함)**
```text
NORMAL ──(1.0초 이상 무검출)──> HOLD_REQUEST
HOLD_REQUEST ──(valid detection 연속 3회 수신)──> NORMAL
```

> **수정 사유**: 정상 결과 "1회"만으로 즉시 NORMAL 복귀하면, confidence가 임계값 근처에서
> 흔들릴 때 NORMAL↔HOLD_REQUEST가 계속 진동(oscillation)할 수 있다. 연속 3회 수신 조건은
> 최소한의 히스테리시스(hysteresis)로, 구현 비용은 거의 늘지 않으면서 안전 로직의 안정성을
> 크게 높인다. (대응 요구사항: SWR-SAF-002b)

**Phase 2 확장 버전**
```text
INIT → NORMAL
NORMAL → DEGRADED (confidence 저하 / deadline miss 반복)
NORMAL → FAULT (heartbeat 중단)
DEGRADED → NORMAL (정상 결과 연속 수신)
DEGRADED → HOLD_REQUEST (결과 timeout 지속)
DEGRADED → FAULT (heartbeat 중단)
HOLD_REQUEST → NORMAL (정상 조건 회복 + 유지시간 경과)
HOLD_REQUEST → FAULT (시스템 오류 확인)
```

로그 예시:
```text
[13:42:10.351] NORMAL -> HOLD_REQUEST
Reason: No valid detection for 1.0 s
```

---

## 7. 벤치마크 방법론

### 7.1 지연시간 3종 구분 (Phase 2에서 전부 구현, Phase 1은 ②까지)
1. 순수 추론 지연시간 — **inference latency** (모델 입력 텐서 준비 완료 → 출력 반환)
2. 처리 파이프라인 지연시간 — **pipeline latency** (이미지 수신 → 전처리 → 추론 → 후처리)
3. 안전 로직 포함 end-to-end 지연시간 — **end-to-end latency / deadline compliance**
   (프레임 timestamp → Safety Supervisor 최종 상태 출력)

### 7.2 측정 지표
mean, median, p95, p99, p99.9, observed maximum, deadline miss ratio, FPS/처리량,
cold-start latency, warm latency

> 명칭 주의: 위 측정은 **WCET(Worst-Case Execution Time) 증명이 아니다.** 정확한 명칭은
> "Empirical Timing Characterization and Deadline-Miss Analysis(경험적 실행시간 특성화 및
> 데드라인 미준수 분석)"이며, 보고서/README에도 이 표현을 사용한다.

### 7.3 비교의 공정성 원칙
- **동일 플랫폼 내부 비교**만 "성능 비교"로 표현한다
  - Intel 플랫폼: OpenVINO FP32 vs INT8
  - Jetson 플랫폼(Phase 2): TensorRT FP32 vs FP16 vs INT8
- **플랫폼 간 비교**(Intel+OpenVINO vs Jetson+TensorRT)는 "시스템 수준 비교"로 별도 표기하며,
  처리속도 외에 메모리, 전력, 개발 복잡도, 지원 연산자, 정확도 변화까지 함께 제시한다
- "A가 B보다 빠르다"는 단정 대신 "어떤 하드웨어·런타임 조합이 주어진 제약을 가장 잘 만족하는가"로
  질문을 재구성한다

### 7.4 재현성 기록 항목 (Phase 2, Jetson 관련)
Jetson model, JetPack 버전, TensorRT 버전, power mode, 입력 해상도, batch size, warm-up 횟수,
추론 횟수, 동시 부하 조건

> **정확한 표현 주의**: 위 항목은 SWaP-C 전체(Size/Weight/Power/Cost)를 측정하는 것이 아니라
> **Power 및 compute-resource 측면 중심의 SWaP-C-informed evaluation**이다. 실제 크기·무게·
> 가격(BOM)은 측정하지 않으므로 "SWaP-C를 실증했다"고 쓰지 않는다. 온도·클럭 스로틀링은 SWaP-C
> 항목에 직접 포함되지 않으며, 전력·성능에 영향을 주는 운용 조건으로 별도 분석한다.

---

## 8. Fault Injection 테스트 (Phase 1: 2종 / Phase 2: 7종)

> **Fault Injection**은 안전critical 소프트웨어의 robustness testing 및 고장 대응 검증에
> 널리 사용되는 시험 기법으로, 정상 입력만으로는 드러나지 않는 결함 대응 로직을 의도적인 고장
> 주입을 통해 검증한다. 여기서는 Safety Supervisor(=RTA-inspired monitor)의 전환 로직을
> 검증하는 데 사용한다.
>
> **정확한 표현 주의**: "DO-178C에서 fault injection을 요구한다"거나 "fault injection을
> 했으므로 DO-178C식 검증이다"라고 쓰지 않는다. Fault injection은 DO-178C에 국한되지 않는
> 범용 검증 기법이며, 본 프로젝트가 DO-178C 절차를 따랐다는 뜻이 아니다.

| Fault injection | 기대 상태 | Phase |
|---|---|---|
| 낮은 confidence 결과 연속 입력 | HOLD_REQUEST (Phase1) / DEGRADED (Phase2) | 1 |
| 결과 메시지 1초간 중단 | HOLD_REQUEST | 1 |
| heartbeat 중단 | FAULT | 2 |
| timestamp가 오래된 결과 입력 | 결과 폐기 | 2 |
| latency가 deadline 초과 | invalid 또는 DEGRADED | 2 |
| bounding box 급변 | plausibility failure | 2 |
| 정상 결과 재수신 | 조건 충족 후 NORMAL 복귀 | 1 |

테스트 예시 형식:
```text
TEST-SAF-002
Given: Supervisor state = NORMAL, No valid detection for 1000ms
Expected: State = HOLD_REQUEST, Transition reason = DETECTION_TIMEOUT
```

---

## 9. 저장소 구조

```text
edge-ai-safety-supervisor/
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
│   ├── thresholds.yaml
│   └── benchmark_conditions.yaml
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
        ├── 0001-select-yolov8n-model.md
        ├── 0002-fix-input-resolution.md
        └── ...
```

`docs/adr/`에는 Architecture Decision Record(ADR) 형식으로 주요 기술적 판단을 하나의 결정당
파일 하나로 기록한다: 모델 선정 이유, PTQ 선택 이유, FP16/INT8 선택 근거, Safety Supervisor
임계값 근거, 충족하지 못한 요구사항 등 변경 비용이 크거나 이후 단계에 영향을 주는 결정들.

---

## 10. 일정 (예시, 실제 가용 시간에 맞춰 조정)

| 주차 | 목표 |
|---|---|
| 1주 | M1, M2 — 모델 선정, 저장영상 기반 파이프라인 |
| 2주 | M3, M4 — OpenVINO INT8 양자화, 벤치마크 자동화 |
| 3주 | M5, M6 — Safety Supervisor 최소버전, fault injection 2종 |
| 4주 | M7, M8 — 요구사항/추적표/한계 문서, Phase 1 마무리 및 README 정리 |
| 5주~ | (여력 시) Phase 2 E1부터 순차 진행 |

---

## 11. 성공 기준 체크리스트

- [ ] 측정 조건이 재현 가능한가 (스크립트 한 번 실행으로 결과 재현)
- [ ] 실패 조건을 의도적으로 만들고 검증했는가 (fault injection)
- [ ] 안전 로직이 요구사항과 자동시험으로 연결되는가 (traceability matrix)
- [ ] 구현하지 않은 안전성·인증 수준을 과장하지 않았는가 (limitations.md 명시)
- [ ] Phase 1만으로도 독립적으로 완결된 결과물인가

---

## 12. 알려진 리스크 및 대응

| 리스크 | 대응 |
|---|---|
| YOLO-World를 처음부터 사용 시 ONNX/INT8 변환에서 막힐 가능성 | Phase 1은 표준 YOLOv8n 등으로 진행, YOLO-World는 Phase 2 확장 항목(E6)으로 분리 |
| OpenVINO INT8 산출물을 TensorRT에 그대로 재사용 가능하다고 오해 | 문서·코드 주석에 "공통 FP32 ONNX에서 독립된 두 경로로 분기"함을 명시 |
| Jetson 없이 개발 시작 시 Phase 2 지연 | Phase 1은 Intel CPU(OpenVINO)만으로 완결 가능하도록 설계 — Jetson 의존은 Phase 2부터 |
| 스코프 과다로 미완성 위험 | 3장의 Phase 1/2 분리 원칙을 반드시 준수, Phase 1 우선 완결 |

---

## 13. 한계 및 정직성 원칙 (README에 반드시 포함)

> 본 프로젝트는 항공 인증 또는 DO-178C 준수를 주장하지 않으며, 항공 소프트웨어의 요구사항 기반
> 개발 및 검증 개념을 학습 목적으로 축소 적용한 프로토타입이다. Safety Supervisor는 실제
> 비행제어를 수행하지 않으며, 상위 시스템이 참고할 수 있는 안전 상태 요청(HOLD_REQUEST 등)을
> 출력하는 데 그친다.

---

## 부록: 프로젝트 전반에 사용된 실제 개념·용어 정리

| 프로젝트 내 항목 | 실제 개념/용어명 | 출처·분야 |
|---|---|---|
| 자원 제약 환경 최적화 전반 | **SWaP-C** (Size, Weight, Power, and Cost) | 항공·방위산업 임베디드 표준 용어 |
| M3, OpenVINO/TensorRT 양자화 | **Post-Training Quantization (PTQ)**, Model Compression | 딥러닝 배포 표준 기법 |
| M4, 7.2절 latency 측정 | **Empirical Timing Characterization and Deadline-Miss Analysis** (WCET와는 구분) | 실시간시스템 공학 |
| M5, 4장, 6장, Safety Supervisor 전체 | **Runtime Assurance (RTA)**, **Simplex Architecture** — 본 프로젝트는 이 개념을 참고한 **RTA/Simplex-inspired monitor** (실제 전환 메커니즘 미구현) | 자율/안전critical 시스템 학계 (Sha 1998; Mehmood et al.; FAA·NASA 관련 연구) |
| M7, 5장 요구사항 작성 | **EARS** (Easy Approach to Requirements Syntax) | Rolls-Royce 개발, Airbus/NASA/Honeywell/Intel 등 채택 |
| 5장, 요구사항 계층·추적성 | **Requirements Traceability**; 시스템 요구사항 배분은 ARP4754A, 소프트웨어 HLR→LLR 분해·추적성은 DO-178C | ARP4754A (Guidelines for Development of Civil Aircraft and Systems), DO-178C |
| 8장, 고장 대응 검증 | **Fault Injection** | 안전critical 소프트웨어 검증 표준 기법 |
| 1.2절, 항공 AI 도입 배경 | EASA **Artificial Intelligence Concept Paper**, FAA **Roadmap for Artificial Intelligence Safety Assurance** | 유럽/미국 항공 규제기관 |
| 배경, ARINC 653 | **ARINC 653** (파티셔닝 기반 실시간 OS 표준) | 항공 IMA(Integrated Modular Avionics) 표준 |

> 위 개념들은 전부 실제 학술 문헌 또는 산업 표준에 근거한 명칭이며, 이 프로젝트가 그 표준을
> 그대로 준수하거나 인증받았다는 뜻은 아니다. README와 발표 자료에서는 항상 "~개념을 참고/축소
> 적용했다"는 표현을 사용하고, "~표준을 준수한다/인증받았다"는 표현은 사용하지 않는다.
