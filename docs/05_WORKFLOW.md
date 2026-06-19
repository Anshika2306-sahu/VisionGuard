# 05 — End-to-End Workflow

> How a pixel becomes a challan. Read alongside [04_LLD.md](04_LLD.md).

## 1. The master pipeline (one image → outcomes)

```mermaid
flowchart TD
    A["Image arrives\n(upload / RTSP frame / batch)"] --> B["Create Job\n(camera_id, captured_at)"]
    B --> C["Enqueue job (Redis)"]
    C --> D["Preprocess\nenhance + quality_score"]
    D -->|quality too low| Z1["status=unusable\n(no fine)"]
    D --> E["Detect\nvehicles + persons + plates (UVH-26 YOLO)"]
    E --> F["Attribute models\nhelmet / seatbelt on crops"]
    E --> G["ANPR\nplate crop -> OCR -> KA01AB1234"]
    F --> H["Violation Reasoning Engine\n(detections + camera ROI)"]
    G --> H
    H --> I{"Per violation"}
    I -->|finable & conf>=thr| J["Auto-issue challan\n+ e-notice (72h)"]
    I -->|finable & conf<thr| K["Needs-review queue"]
    I -->|safety_alert| L["Zero-fine alert\n(accident / jam)"]
    J --> M["Annotate evidence\nstore image + metadata"]
    K --> M
    L --> M
    M --> N["Update Geo heatmap\n(camera -> latlng, severity)"]
    N --> O["Push to Command Center\n(WebSocket live event)"]
    J --> P["Visible in Citizen Portal\n(owner's challan list)"]
```

## 2. Sequence — single image upload (Command Center)

```mermaid
sequenceDiagram
    participant UI as Command Center (React)
    participant API as FastAPI
    participant Q as Redis Queue
    participant W as ML Worker
    participant DB as Postgres
    participant S as Object Store
    participant MM as Mappls

    UI->>API: POST /ingest/image (file, camera_id)
    API->>S: save original image
    API->>DB: insert Job(status=queued)
    API->>Q: enqueue job_id
    API-->>UI: 202 {job_id, status:queued}

    W->>Q: pull job_id
    W->>S: load original
    W->>W: preprocess -> detect -> helmet/anpr
    W->>W: violation_engine(detections, ROI)
    W->>S: save annotated evidence + crops
    W->>DB: write detections, violations
    alt finable & confident
        W->>DB: create challan + e-notice (due=+72h)
    end
    W->>MM: reverse-geocode camera latlng (cache)
    W->>DB: upsert camera.address, heatmap point
    W-->>API: job done (via DB/WS)
    API-->>UI: WS push {violations, evidence_uri}
    UI->>API: GET /jobs/{id}
    API-->>UI: full result -> render evidence + cards
```

## 3. Sequence — citizen checking their challans

```mermaid
sequenceDiagram
    participant C as Citizen Portal
    participant API as FastAPI
    participant DB as Postgres
    participant MM as Mappls

    C->>API: GET /citizen/challans?plate=KA01AB1234 (citizen JWT)
    API->>DB: select challans where plate=... (own only)
    API-->>C: list (type, fine, status, evidence-thumb, location)
    C->>API: GET /citizen/alerts?lat&lng&radius
    API->>DB: nearby safety alerts (accidents/jams)
    API-->>C: alerts
    C->>MM: render local Mappls map + alert markers
```

## 4. Challan lifecycle (state machine)

```mermaid
stateDiagram-v2
    [*] --> issued: violation confirmed (auto or officer)
    issued --> notified: e-notice generated/sent
    notified --> paid: payment received (gateway stub)
    notified --> contested: citizen disputes
    contested --> dismissed: review upholds dispute
    contested --> notified: dispute rejected
    notified --> expired: due_at passed, unpaid
    paid --> [*]
    dismissed --> [*]
    expired --> escalated: hand to recovery (future)
```

## 5. Job status lifecycle

```mermaid
stateDiagram-v2
    [*] --> queued
    queued --> processing
    processing --> done
    processing --> failed: exception (retry x3)
    processing --> unusable: quality below floor
    failed --> queued: retry
    done --> [*]
```

## 6. Violation decision flow (the engine, expanded)

```mermaid
flowchart TD
    D["Detections + ROI config"] --> Q{quality ok?}
    Q -->|no| SA["only safety alerts allowed"]
    Q -->|yes| R1["attribute rules:\nhelmet, triple-riding, seatbelt"]
    Q -->|yes| R2["geometry rules:\nstop-line, red-light, wrong-side, parking"]
    R2 --> FP{illegal_parking?}
    FP -->|person near vehicle| SUP["suppress (occupied heuristic)"]
    FP -->|no person| KEEP["keep"]
    R1 --> CG{conf >= threshold?}
    KEEP --> CG
    CG -->|yes| AUTO["auto_issued -> challan"]
    CG -->|no| REV["needs_review"]
    SA --> ALERT["zero-fine alert -> heatmap"]
```

## 7. Camera onboarding workflow (one-time per camera)

```mermaid
flowchart LR
    A["Admin adds camera\n(name, code, lat, lng, source)"] --> B["Mappls reverse-geocode\n-> address, zone"]
    B --> C["Operator draws ROIs\nstop-line / no-parking / lane-dir / signal-lamp"]
    C --> D["Calibrate density threshold\n(for jam alert)"]
    D --> E["Camera = LIVE\n(jobs can now be enforced)"]
```

> Until ROIs are configured, that camera only emits **attribute violations** (helmet, triple-riding) +
> **safety alerts**; geometry violations stay in review. This keeps the system honest per-camera.

## 8. Daily operations loop (Command Center)

1. Live map shows incoming violations/alerts (WebSocket).
2. KPI cards refresh (challans today, active cameras, accident alerts, jam zones).
3. Officer works the **needs-review** queue: confirm → challan, or dismiss → reason logged (audit).
4. Heatmap reveals hotspots → patrol/infrastructure decisions.
5. Reports exported for the day/zone.

## 9. Batch / historical analysis workflow

- Drop a folder/zip of historical Safe City frames → `/ingest/batch` → workers fan out → analytics
  populate trends → identify chronic hotspots and peak-violation hours. (This is the offline mirror of
  the live loop and is how we'd "replay" ASTraM's archived footage.)
