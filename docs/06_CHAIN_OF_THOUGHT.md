# 06 — Chain of Thought (every decision + why)

> This is the "defend the design" doc. For each fork in the road: the options, what we chose, and why.
> Use it to answer judge/reviewer questions without hesitation.

## 1. Framing: build vs. reuse

**Decision:** Reuse India's proven enforcement stack (MLFF/FASTag/ANPR/multi-angle evidence/e-notice) and
Bengaluru's existing Safe City cameras + Mappls, rather than inventing a novel pipeline.

**Why:**
- The hard parts (plate reading at speed, evidence capture, e-notice issuance, owner resolution) are
  *already solved and trusted* nationally. Reusing them = credibility + speed + lower risk.
- The sponsors literally provide the two missing pieces: ASTraM gives cameras+data, Mappls gives maps.
- "We extended a working system" is a stronger, more honest story than "we built magic from scratch."

**Rejected:** a from-scratch bespoke system — slower, less credible, ignores free national infrastructure.

## 2. Dataset choice

**Decision:** UVH-26 (primary) + BMD-45 (scale) as core; Roboflow helmet/plate sets for attributes; IDD as
secondary context; PaddleOCR/EasyOCR for OCR.

**Why:**
- UVH-26/BMD-45 are **literally Bengaluru Safe City CCTV** → zero domain gap with the deployment target.
- Free (CC BY 4.0) and ship **pretrained models** → we get a strong baseline on day one without GPUs.
- Indian 14-class taxonomy (auto-rickshaw, tempo-traveller, LCV) → correct for local traffic.
- The BMD-45 paper proves **ego-view (IDD) transfers poorly to CCTV** → so we use IDD only as secondary,
  not primary. (This is a defensible, evidence-backed call.)

**Rejected:** COCO-only (foreign distribution), DataCluster full plate set (commercial), training from
scratch (no time, no GPU budget).

## 3. Why a separate Violation Reasoning Engine (not "one big model")

**Decision:** Detectors output *facts* (boxes, classes, attributes); a separate **rule engine** turns facts
into *violations*.

**Why:**
- Many violations are **not visible from pixels alone** (stop-line, red-light, wrong-side need scene
  context/geometry). A monolithic classifier can't encode "this lane only allows northbound."
- Rules are **explainable** → every challan carries a `rationale` (which rule fired, with inputs). Crucial
  for contestability + officer trust + legal defensibility.
- Rules are **testable** (pure functions) and **tunable per camera** without retraining.
- Lets us **mix** learned attributes (helmet) with deterministic geometry (ROI crossing).

**Rejected:** end-to-end "violation classifier" — opaque, un-tunable, can't do geometry, hard to defend.

## 4. Per-camera ROI configuration tool

**Decision:** Operators draw stop-line / no-parking / lane-direction / signal-lamp regions once per camera.

**Why:**
- This is **exactly how real red-light/ATCS systems work** — context is configured, not guessed.
- Converts "impossible from a single image" into "trivial geometry."
- Keeps the system **honest per camera**: geometry violations only auto-issue where context exists.

**Rejected:** trying to infer stop-lines/lanes automatically everywhere — unreliable, would create unfair
fines.

## 5. Two output classes: finable vs. safety alert

**Decision:** Accidents and jams are **zero-fine alerts**, not challans.

**Why:** fining an accident victim or a car stuck in a jam is absurd. But that data is still gold for
patrol routing and infra planning → keep it as a safety signal on the heatmap.

## 6. False-positive controls (occupied-vehicle heuristic, confidence gating, review queue)

**Decision:** Add domain heuristics + confidence thresholds + human-in-the-loop review before auto-fining.

**Why:**
- An unfair automated fine destroys public trust faster than a missed violation.
- Confidence gating + a **needs-review queue** means low-certainty cases get a human, not a fine.
- The occupied-vehicle heuristic encodes real human judgment ("someone's standing there, it's not
  abandoned parking").

**Trade-off accepted:** slightly lower recall on borderline cases in exchange for much higher precision on
issued challans — the right trade for enforcement.

## 7. Tech stack choices

| Choice | Alternative considered | Why we chose it |
|---|---|---|
| **FastAPI** | Flask, Django | async, auto OpenAPI docs, Pydantic typing, fast, tiny |
| **Postgres (+PostGIS at scale)** | MongoDB, MySQL | relational fits challans/audit; PostGIS = native geo heatmaps |
| **Redis + Celery** | RabbitMQ, SQS | simplest free queue; same primitive scales to many workers |
| **Ultralytics YOLO (v8/v11)** | Detectron2, raw PyTorch | UVH-26 ships YOLO weights; simplest train/infer/export path |
| **PaddleOCR / EasyOCR** | Tesseract | far better on noisy real-world plates than Tesseract |
| **React + Vite + Tailwind** | Next.js, Angular | fast SPA, great for dashboards, free |
| **Mappls Web SDK** | Google Maps, Leaflet/OSM | sponsor requirement + India-accurate + free dev tier |
| **Docker Compose → k8s** | bare metal | one-command prototype; clean path to scale |
| **Object storage interface (FS→S3)** | hardcode FS | lets prototype↔scale swap without code change |

## 8. Why CPU-first prototype

**Decision:** Prototype must run on a laptop CPU (≤2s/image), GPU optional.

**Why:** judges/teammates may not have GPUs; "it runs on my machine" must be true. We export to ONNX and
use small models (YOLOv11s) for CPU; GPU/TensorRT is a scale optimisation, not a requirement to demo.

## 9. Why design-for-scale now, deploy-small now

**Decision:** Use scalable primitives (queue, stateless workers, storage interface, Postgres) in the
prototype even though we run one node.

**Why:** the extended brief demands "scalable, handles future load." If we hardcode single-machine
assumptions, scaling = rewrite. By building on the right primitives, scaling = **replicas + infra swap**
(documented in [07](07_SCALABILITY_ROADMAP.md)). This is the cheapest insurance against the brief.

## 10. Privacy & ethics by design

**Decision:** RBAC + audit log + person/face blur on citizen-facing evidence + access-controlled plate data.

**Why:** plate + face data is sensitive PII. Citizen-facing images must blur third parties; every
plate/challan access is audit-logged. UVH-26/BMD-45 are already anonymised — we keep that discipline in
deployment. This is both ethical and a strong slide for judges.

## 11. Known hard problems (honest list) + our stance

| Hard problem | Honest status | Our stance |
|---|---|---|
| Seatbelt from CCTV (glare/angle) | hard with free data | ship as **beta**, roadmap to fine-tune |
| Wrong-side from a single image | needs motion/heading | use **clip mode** (2+ frames) or per-lane config; image-mode = lower confidence → review |
| Red-light signal state | needs signal feed/lamp ROI | lamp-colour classifier now; integrate signal-controller feed at scale |
| Accident detection | rare, varied | heuristic + review now; train a classifier when labelled data available |
| OCR on dirty/oblique plates | imperfect | normalise + confidence; "UNREADABLE" → review (mirrors MLFF "unidentified") |

> Naming the hard parts honestly (and showing a credible plan) reads as **engineering maturity**, not
> weakness. Don't hide them.

## 12. What we explicitly did NOT do (and why)

- **No live payment integration** — out of scope/legal; we stub the gateway with a clean interface.
- **No real VAHAN access** — we stub owner lookup; the integration point is defined in LLD.
- **No claim of 99% accuracy** — we report honest metrics from the eval harness ([11](11_PERFORMANCE_EVALUATION.md)).
- **No dependency on any paid dataset/API** — everything has a free path.
