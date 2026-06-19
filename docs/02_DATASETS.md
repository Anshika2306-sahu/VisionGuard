# 02 — Datasets (free, Bengaluru-first)

> Principle: **prioritise Bengaluru → then any Indian city → then generic.** Every dataset below is
> free for our use. Commercial-only datasets are listed but marked, and we never depend on them.

## 0. TL;DR — what to actually download

| Need | Primary (use this) | License | Why |
|---|---|---|---|
| Vehicle detection (CCTV) | **UVH-26** (IISc) + its pretrained YOLOv11 | CC BY 4.0 / Apache-2.0 | **Bengaluru Safe City cameras**, 14 Indian classes, models included |
| Vehicle detection (bigger) | **BMD-45** (IISc) | CC BY 4.0 | 45K imgs, 3,679 Bengaluru cameras, CVPR'26 |
| Helmet / no-helmet + plate | **Roboflow Helmet+Number-Plate** sets | Open (Roboflow Universe) | Ready helmet & rider labels |
| ANPR plate detect | Roboflow **Indian Number Plates** (YOLO export) | Open | Free YOLO-format plate boxes |
| Plate OCR | **PaddleOCR / EasyOCR** pretrained + synthetic plates | Apache/MIT | No training data needed to start |
| Driving scenes (context) | **IDD** (IIIT-H) | Research license (free signup) | Indian ego-view, 34 classes |

You can build the **entire prototype** from the rows marked "use this" — all free.

---

## 1. PRIMARY — UVH-26 (the headliner)

- **What:** 26,646 high-res (1080p) images from **~2,800 Bengaluru Safe City CCTV cameras**, with
  **~1.8M bounding boxes across 14 India-specific vehicle classes**. Annotated by 565 students in a
  national hackathon; consensus via Majority Voting + STAPLE.
- **Why it's perfect:** it is *the same camera network ASTraM runs*. Models trained on it show up to
  **+31.5% mAP@50:95 vs COCO-trained baselines** on Indian traffic. **Pretrained models are released too.**
- **License:** Dataset **CC BY 4.0**; Models **Apache 2.0** (some variants AGPL-3.0 — check per-model).
- **Where:**
  - Dataset: `https://huggingface.co/datasets/iisc-aim/UVH-26`
  - Models: `https://huggingface.co/iisc-aim/UVH-26`
  - Paper: arXiv `2511.02563`
- **14-class taxonomy (fine → coarse):**
  `Bicycle | Two-Wheeler (Motorbike) | Three-Wheeler (Auto-rickshaw) | Car (Hatchback/Sedan/SUV/MUV) |
  Bus (Bus/Mini-Bus) | Van | Commercial Vehicle (LCV/Tempo-Traveller) | Truck | Other`.

### Download (free, requires a free HF account)
```bash
pip install -U "huggingface_hub[cli]" datasets
huggingface-cli login            # paste a free read token from huggingface.co/settings/tokens

# option A: dataset
huggingface-cli download iisc-aim/UVH-26 --repo-type dataset --local-dir data/raw/uvh26

# option B: a pretrained model (e.g., YOLOv11)
huggingface-cli download iisc-aim/UVH-26 --include "*yolov11*" --local-dir ml/weights/uvh26
```
> If a specific model repo path differs, browse the HF model page and copy the exact file paths.

---

## 2. PRIMARY (scale-up) — BMD-45 (Bengaluru Mobility Dataset)

- **What:** ~45,986 images (1920×1080) from **3,679 Bengaluru Safe City cameras**, ~482K consensus boxes,
  same **14-class** taxonomy. Accepted at **CVPR 2026** findings.
- **Why:** bigger, harder test split, explicitly designed for **city-scale CCTV ITS**. Use it to push
  accuracy and to demonstrate scalability claims.
- **License:** CC BY 4.0. Test labels withheld (COCO-style) — use train/val.
- **Where:** `https://huggingface.co/datasets/iisc-aim/BMD-45` (paper: arXiv `2604.24419`).

```bash
huggingface-cli download iisc-aim/BMD-45 --repo-type dataset --local-dir data/raw/bmd45
```

---

## 3. Violation-specific datasets

These cover what UVH-26/BMD-45 (vehicle-only) don't: helmet, plate text, etc.

### 3.1 Helmet + Number Plate (motorbike safety) — Roboflow Universe
- Classes typically: `helmet`, `no-helmet`/`without-helmet`, `rider`, `number-plate`.
- Free to download in **YOLOv8/v11 format** from Roboflow Universe.
- Search Roboflow Universe for: *"Helmet and Number Plate Detection for Motorbike Safety"* and
  *"Motorcycle Helmet Dataset"*. Export → YOLOv11 → copy the `curl` snippet they generate.
```bash
# Roboflow gives you an exact curl command after you click "Download Dataset → YOLOv11"
# It looks like:
#   curl -L "https://universe.roboflow.com/ds/XXXX?key=YYYY" > roboflow.zip
unzip roboflow.zip -d data/raw/helmet
```

### 3.2 Indian Number Plates (detection) — Roboflow Universe (free mirrors)
- Several community mirrors of "Indian Number Plates" exist in **YOLO format, free**. Use these for the
  **plate-localisation** model (then OCR the crop).
- Note: the original **DataCluster Labs** 20K set is **commercial-only** for the full version (free sample
  ~200 imgs on HF: `Dataclusterlabspvtltd/indian-number-plates-dataset`). We **do not** depend on the paid set.

### 3.3 Triple riding / rider count
- Derive from helmet/rider datasets + **person-on-two-wheeler counting** (count `person` boxes whose
  centroids fall inside a `motorbike` box). RideSafe-style dashcam sets on Roboflow also include
  passenger-count labels — optional fine-tune source.

### 3.4 Seatbelt
- Hardest class with free data. Options: Roboflow "seatbelt detection" community sets (windshield-crop
  classification). Treat as a **fine-tune-later / roadmap** class; prototype can ship it as "beta".

---

## 4. Context / secondary

### 4.1 IDD — India Driving Dataset (IIIT Hyderabad)
- **What:** 10K finely-annotated (34 classes) + ~46K detection images, Indian roads (Hyderabad +
  **Bengaluru**), ego-centric (dashcam). Free with registration.
- **Use:** augmentation, robustness, "Indian-ness" of context. Note **viewpoint gap** — ego-view ≠
  CCTV pole-view; don't expect ego-trained models to transfer cleanly to CCTV (the BMD-45 paper proves
  this). So IDD is **supplementary**, not primary.
- **Where:** `https://idd.insaan.iiit.ac.in/`

### 4.2 Kaggle Indian license plates (with labels)
- `kaggle datasets download -d kedarsai/indian-license-plates-with-labels` (free Kaggle account).
- Small, but useful for OCR sanity checks on Indian fonts/HSRP plates.

---

## 5. Red-light / stop-line / wrong-side — the "context" violations

These **cannot** be learned from a single image of a vehicle alone; they need **scene context**
(signal state, stop-line position, lane direction). Our approach (detailed in LLD):

| Violation | What extra context is needed | Prototype strategy |
|---|---|---|
| **Stop-line** | A per-camera **stop-line polygon** + vehicle bbox crossing it | Operator draws the line once per camera (stored as ROI); geometry check |
| **Red-light** | **Signal state** (red/green) + stop-line crossing during red | Detect signal lamp colour (small classifier/HSV on signal ROI) OR ingest signal-controller feed; combine with stop-line |
| **Wrong-side** | **Allowed direction** per lane + vehicle **heading** | Per-camera lane direction config + motion vector across 2+ frames (clip mode) or orientation heuristic (single image) |
| **Illegal parking** | **No-parking zone** polygon + dwell + occupied-vehicle heuristic | Operator marks no-parking ROI; vehicle inside ROI + (clip) dwell time + no nearby person |

> **Key design move:** ship a **Camera Configuration tool** in the Command Center where an operator draws
> ROIs (stop-line, no-parking zone, lane direction arrows) **once per camera**. This turns
> "impossible from one image" into "simple geometry", and is exactly how real ATCS/red-light systems work.

---

## 6. Licensing & ethics cheat-sheet

| Dataset | License | Commercial OK? | Attribution required |
|---|---|---|---|
| UVH-26 (data) | CC BY 4.0 | ✅ | ✅ cite IISc UVH paper |
| UVH-26 (models) | Apache-2.0 / AGPL-3.0 | ✅ (check variant) | ✅ |
| BMD-45 | CC BY 4.0 | ✅ | ✅ cite BMD-45 |
| IDD | Research license | ⚠️ check | ✅ |
| Roboflow community sets | varies (often CC BY 4.0) | usually ✅ | ✅ |
| DataCluster full | Commercial license | ❌ free tier | n/a (don't use) |

**Privacy note for the deck:** UVH-26/BMD-45 are **anonymised** (filenames obfuscated, no location leak).
For real deployment, faces/persons should be blurred in any citizen-facing image, and plate data access
must be access-controlled + audit-logged. We bake this into the LLD (RBAC + audit log + face/person blur
on citizen-facing evidence).

## 7. Citations to keep handy (put in slides)

- *The Urban Vision Hackathon Dataset and Models (UVH-26)*, IISc, arXiv:2511.02563, Nov 2025.
- *BMD-45: A Large-Scale CCTV Vehicle Detection Dataset...*, IISc, CVPR 2026 Findings, arXiv:2604.24419.
- *IDD: Indian Driving Dataset*, IIIT-H, WACV 2019.
- *Indian Licence Plate Dataset in the wild*, Tanwar et al., arXiv:2111.06054, 2021.
