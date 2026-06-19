# 11 — Performance Evaluation

> Task 8 of the brief: evaluate Accuracy, Precision, Recall, F1, mAP + computational efficiency &
> scalability. This doc defines exactly what to measure, how, and where the code lives (`ml/eval/`).

## 1. What we measure (and why each)

| Metric | Applies to | Why it matters here |
|---|---|---|
| **mAP@50**, **mAP@50:95** | vehicle/person/plate detection | standard detection accuracy; comparable to UVH-26/BMD-45 papers |
| **Precision** | each violation class | of issued challans, how many were correct (fairness!) |
| **Recall** | each violation class | of real violations, how many we caught |
| **F1** | each violation class | balance of the two |
| **Accuracy + Confusion matrix** | helmet, vehicle-type, violation type | where classes get confused |
| **ANPR exact-string accuracy** | plates | % plates read perfectly |
| **ANPR CER** (char error rate) | plates | partial-credit quality of OCR |
| **Latency** (ms/image) | system | real-time feasibility (CPU & GPU) |
| **Throughput** (images/sec) | system | scale capacity |
| **Edge-filter saving factor** | scale design | % frames dropped before central compute |

## 2. Datasets/splits for evaluation

- **Detection:** held-out **val split of UVH-26 / BMD-45** (never train on val). Report mAP per class +
  overall. Compare pretrained-UVH-26 vs COCO-baseline to *show the Bengaluru-data advantage*.
- **Helmet / violations:** a **labelled mini-set** (50–200 images you annotate, or Roboflow val split).
  Even a small, honest set is fine for a hackathon — state the size.
- **ANPR:** a set of plate crops with ground-truth strings (Kaggle Indian plates / your labelled samples).

## 3. How to compute (tools)

```python
# 3.1 Detection mAP — easiest via Ultralytics:
#   yolo detect val model=ml/weights/uvh26/yolo11s.pt data=ml/configs/uvh26_val.yaml
#   -> prints mAP50, mAP50-95 per class. Save the results table.

# 3.2 Classification P/R/F1 + confusion matrix (helmet, violation type):
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix, classification_report
p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average=None, labels=labels)
print(classification_report(y_true, y_pred, target_names=labels))
cm = confusion_matrix(y_true, y_pred, labels=labels)   # plot with matplotlib

# 3.3 ANPR:
exact_acc = mean([pred == gt for pred, gt in pairs])
cer = mean([edit_distance(pred, gt) / max(1, len(gt)) for pred, gt in pairs])  # use python-Levenshtein

# 3.4 Latency / throughput:
import time
t0 = time.perf_counter()
for img in bench_images: run_pipeline(img)
elapsed = time.perf_counter() - t0
print("ms/image:", 1000*elapsed/len(bench_images), "images/sec:", len(bench_images)/elapsed)
```

## 4. Evaluation harness layout (`ml/eval/`)

```
ml/eval/
  eval_detection.py     # wraps ultralytics val -> metrics.json (mAP per class)
  eval_violations.py    # P/R/F1 + confusion matrix on labelled mini-set -> plots + report
  eval_anpr.py          # exact-acc + CER on plate set
  bench_latency.py      # ms/image + images/sec on CPU (and GPU if available)
  report.py             # aggregates all -> ml/eval/metrics.json + ml/eval/figures/*
```

Output a single `ml/eval/metrics.json`:
```json
{
  "detection": {"mAP50": null, "mAP50_95": null, "per_class": {}},
  "helmet": {"precision": null, "recall": null, "f1": null},
  "violations": {"per_class": {}},
  "anpr": {"exact_acc": null, "cer": null},
  "system": {"ms_per_image_cpu": null, "images_per_sec_cpu": null, "ms_per_image_gpu": null},
  "edge_filter_saving_pct": null,
  "eval_set_sizes": {"detection_val": null, "violation_mini": null, "anpr": null}
}
```

## 5. Targets (restate from the vision doc)

| Metric | Prototype target | Stretch (fine-tuned/GPU) |
|---|---|---|
| Vehicle mAP@50 | ≥ 0.70 (UVH-26 pretrained) | ≥ 0.85 |
| Helmet F1 | ≥ 0.85 | ≥ 0.92 |
| ANPR exact-acc (clear plates) | ≥ 0.70 | ≥ 0.90 |
| Latency CPU | ≤ 2000 ms/img | — |
| Latency GPU | — | ≤ 200 ms/img |

## 6. How to present results (for judges)

1. **One table** of headline metrics (mAP, helmet F1, ANPR acc, latency).
2. **One bar chart**: UVH-26-pretrained vs COCO-baseline mAP → proves the Bengaluru-data advantage.
3. **One confusion matrix** (helmet or violation type).
4. **One latency/throughput line** → "X images/sec on a laptop CPU; Y on one GPU."
5. **The capacity math** from [07](07_SCALABILITY_ROADMAP.md) → "whole city ≈ single-digit GPUs."
6. **Honesty slide**: state eval-set sizes and which classes are beta (seatbelt, wrong-side single-image).

## 7. Continuous evaluation (scale)

At scale, evaluation never stops: sample issued challans for human audit, track **precision drift** per
camera, feed confirmed/dismissed reviews back as new training labels (active learning), and re-evaluate
each model version via the canary pipeline before full rollout.
