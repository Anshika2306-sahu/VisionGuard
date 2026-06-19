# 01 — Problem & Vision

## 1. The challenge (as stated)

Traffic surveillance cameras generate huge volumes of images daily. Manual inspection to find
violations is slow, expensive, and inconsistent. We must build a **computer-vision system** that
automatically:

1. **Preprocesses** images (low light, rain, shadows, motion blur).
2. **Detects** vehicles + road users (riders, drivers, pedestrians) and classifies vehicle types.
3. **Detects violations**: helmet non-compliance, seatbelt non-compliance, triple riding,
   wrong-side driving, stop-line violation, red-light violation, illegal parking.
4. **Classifies** violations into predefined classes with **confidence scores**.
5. **Recognises license plates** (detect + OCR).
6. **Generates evidence** (annotated images + metadata + timestamps).
7. **Provides analytics & reporting** (stats, trends, searchable records).
8. **Is evaluated** on Accuracy, Precision, Recall, F1, mAP, plus efficiency & scalability.

**Expected outcome:** a scalable AI system that auto-identifies, classifies, and documents traffic
violations from photos, reducing manual effort and improving enforcement.

## 2. Our core thesis: *reuse what India already proved works*

The single biggest differentiator in our submission is honesty + leverage:
**India already runs world-class automated traffic enforcement** — we are not inventing it from zero.

### 2.1 What already exists (MLFF tolling — the proof)

India's **Multi-Lane Free-Flow (MLFF)** tolling system already does, at highway speed and at national
scale, almost every hard thing this problem asks for:

| Step in MLFF tolling | Tech used | The same capability our problem needs |
|---|---|---|
| Identify the vehicle without stopping it | **RFID / FASTag** scan | Primary vehicle identity |
| Fallback when tag is missing/hidden | **ANPR cameras** read the plate | **Task 5: License Plate Recognition** |
| Catch plate-hiding cheats | **LIDAR + radar** → speed + 3D vehicle shape | **Task 2: vehicle category** (car/truck/bus) + speed |
| Collect proof | **High-speed cameras** capture multi-angle photos/video | **Task 6: Evidence Generation** |
| Decide + act | System **flags violator / unidentified vehicle**, issues **e-notice payable in 72h** | **Tasks 3,4: detect+classify violation → enforce** |
| Investigate later | Toll authority reviews flagged cases | **Task 7: review workflow / analytics** |

> **The narrative for judges:** "Every component this problem asks for is already deployed and trusted on
> Indian highways through MLFF/FASTag. VisionGuard's innovation is **transplanting that proven enforcement
> loop from tolling onto city traffic-rule enforcement**, and doing it on cameras the city *already owns*."

### 2.2 What we reuse from each partner

**Bengaluru Traffic Police (ASTraM):**
- The **Safe City CCTV network** (2,800–3,600 cameras) is our *deployment substrate* — no new hardware
  needed to scale city-wide.
- The **UVH-26** and **BMD-45** open datasets are literally frames from *these cameras*, so our models are
  trained/evaluated on the **exact distribution they will run on in production** (same angles, same
  lighting, same Indian vehicle mix). This is the strongest possible domain match.
- We mirror the real **Indian fine schedule** so output is enforcement-ready.

**MapMyIndia / Mappls:**
- **Map + tiles**: every camera, violation, accident, and jam is plotted on Mappls maps.
- **Reverse geocoding (eLoc)**: convert camera lat/long → human-readable Bengaluru addresses on challans.
- **Routing / traffic**: power "nearby safety alerts" for citizens and patrol-route planning for police.
- We respect Mappls branding/attribution terms (logo + copyright stay visible).

### 2.3 Why "reuse" beats "build from scratch" (and how to say it)

- **Faster to real impact** — works on existing cameras + existing maps.
- **Trustworthy** — mirrors an enforcement loop citizens already accept (FASTag e-notices).
- **Domain-correct** — Bengaluru data → Bengaluru deployment, no domain gap.
- **Honest** — we explicitly credit MLFF, ASTraM cameras, and Mappls instead of pretending novelty.

## 3. The product vision

VisionGuard is **two products on one engine**:

1. **Command Center (Police / ASTraM):** city-wide enforcement + safety dashboard. Upload/stream images,
   review annotated evidence, manage challans, watch the live safety heatmap, run analytics.
2. **Citizen Portal (Public):** read-only. A citizen sees **their own challan history + payment status**
   and **safety alerts near them** (accident-prone zones, jams) on a locally-scoped Mappls map. No upload,
   no enforcement tools.

### 3.1 Two output classes (a key design idea)

Not every detection is a fine. We split outputs into:

- **Finable violations** → produce a **challan** (helmet, triple riding, red-light, stop-line,
  wrong-side, illegal parking, seatbelt) with a defined penalty + e-notice.
- **Safety alerts (zero fine)** → **accidents** and **traffic jams / overcrowding** generate warnings and
  update the heatmap, but never a fine. They drive patrol + infrastructure decisions.

### 3.2 Smarter, fairer enforcement (false-positive reduction)

We add domain reasoning so we don't fine people unfairly, e.g.:
- **Occupied-vehicle heuristic:** a "parked" car with a person standing next to/overlapping it is treated
  as *temporarily stopped*, not illegally parked → suppress the challan.
- **Confidence gating:** below a per-violation confidence threshold → send to **human review queue**, not
  straight to a challan.
- **Multi-evidence requirement** for high-value fines (e.g. red-light needs both the signal-state cue and
  the stop-line crossing) before auto-issuing.

## 4. Scope for the hackathon (extended brief)

We must deliver an **end-to-end working prototype** that is **architected to scale to the whole city**.

- **Now (prototype):** runs on a laptop via Docker; processes uploaded images and short clips; full
  detect → violate → challan → map → analytics loop; dual UI.
- **Designed for (scale):** the *same* code paths fan out via queues, object storage, GPU inference
  servers, and edge devices to ingest thousands of live camera streams. The roadmap to get there is
  fully specified in [07_SCALABILITY_ROADMAP.md](07_SCALABILITY_ROADMAP.md) — we build the prototype on
  scalable primitives so "scale" is a deployment change, not a rewrite.

## 5. Success criteria

| Dimension | Prototype target | Scaled target |
|---|---|---|
| Vehicle detection mAP@50 (Bengaluru CCTV) | ≥ 0.70 using UVH-26 pretrained | ≥ 0.85 fine-tuned |
| Helmet / no-helmet F1 | ≥ 0.85 | ≥ 0.92 |
| ANPR exact-string accuracy | ≥ 0.70 on clear plates | ≥ 0.90 |
| End-to-end latency / image | ≤ 2 s on CPU laptop | ≤ 200 ms on GPU |
| Throughput | 1 image at a time (demo) | 1000s of cameras via horizontal workers |
| Manual effort reduction | demonstrable on sample set | city-wide |

These map directly to [11_PERFORMANCE_EVALUATION.md](11_PERFORMANCE_EVALUATION.md).
