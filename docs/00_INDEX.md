# VisionGuard AI — Documentation Index

This folder is the **single source of truth** for the entire project: the idea, the design,
the datasets, the build, and the path to city-scale. Read in the order below.

## Reading order

| # | Doc | What you get | Audience |
|---|---|---|---|
| 01 | [Problem & Vision](01_PROBLEM_AND_VISION.md) | The challenge, our "reuse existing tech" thesis, how we honour MapMyIndia + ASTraM | Everyone / judges |
| 02 | [Datasets](02_DATASETS.md) | Every free dataset, Bengaluru-first, exact download steps, licenses | ML engineer |
| 03 | [High-Level Design (HLD)](03_HLD.md) | System architecture, layers, components, C4 + flow diagrams | Architects / judges |
| 04 | [Low-Level Design (LLD)](04_LLD.md) | DB schema, API contracts, model I/O, violation rules, module breakdown | Developers |
| 05 | [Workflow](05_WORKFLOW.md) | End-to-end data flow, sequence diagrams, state machines | Developers |
| 06 | [Chain of Thought](06_CHAIN_OF_THOUGHT.md) | Every key decision and the reasoning behind it | Anyone defending the design |
| 07 | [Scalability Roadmap](07_SCALABILITY_ROADMAP.md) | Prototype → whole-city: HLD + LLD of the scaled system | Architects / judges |
| 08 | [Tech Stack](08_TECH_STACK.md) | Every tool, with the **free** option at every stage | Everyone |
| 11 | [Performance Evaluation](11_PERFORMANCE_EVALUATION.md) | Metrics plan: Accuracy/Precision/Recall/F1/mAP + latency/throughput | ML engineer / judges |

## The one-paragraph summary (for when you forget everything)

> VisionGuard ingests traffic images/CCTV frames, **enhances** them (low-light, blur, rain),
> **detects** vehicles + riders + pedestrians + plates using models **pre-trained on Bengaluru's own
> Safe City cameras (UVH-26/BMD-45)**, runs **attribute models** (helmet/seatbelt) and **ANPR (plate → OCR)**,
> then a **violation reasoning engine** turns detections into violations with confidence scores. Finable
> violations become **auto-challans with e-notices** (mirroring India's MLFF tolling loop); accidents and
> jams become **zero-fine safety alerts**. Everything is geotagged onto a **MapMyIndia/Mappls heatmap**,
> reviewed in a **Command Center** dashboard, and exposed to citizens via a read-only **Citizen Portal**.
> The prototype runs on a laptop with Docker; the same architecture scales to the whole city via queues,
> object storage, GPU inference servers, and edge deployment.

## Glossary (fast reference)

| Term | Meaning |
|---|---|
| **ASTraM** | Bengaluru Traffic Police's Actionable Intelligence for Sustainable Traffic Management unit (hackathon partner) |
| **MLFF** | Multi-Lane Free-Flow tolling — barrier-less tolling using RFID + ANPR (the tech we reuse) |
| **ANPR** | Automatic Number Plate Recognition (detect plate → OCR the text) |
| **UVH-26 / BMD-45** | IISc open datasets from Bengaluru Safe City CCTV (our primary training/eval data) |
| **IDD** | India Driving Dataset (IIIT-H) — ego-centric Indian roads, secondary data |
| **Challan** | A traffic fine / ticket |
| **e-notice** | Electronic violation notice sent to the owner (payable within 72h, as in MLFF) |
| **Command Center** | The police/admin city-wide enforcement dashboard |
| **Citizen Portal** | The read-only citizen view (own challans + local safety alerts) |
| **HLD / LLD** | High-Level / Low-Level Design |
| **mAP** | mean Average Precision (object-detection accuracy metric) |
