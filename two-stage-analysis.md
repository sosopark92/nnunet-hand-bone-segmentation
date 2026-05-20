# 2-Stage nnU-Net Hand Segmentation — Results Analysis

## Pipeline Overview

| Stage | Input | Model | Output |
|-------|-------|-------|--------|
| Stage 1 | Full hand CT | Whole-hand nnU-Net (Dataset100) | Coarse 29-class mask |
| Stage 2 | ROI-cropped sub-volumes | 3 ROI-specific nnU-Nets (Dataset201–203) | Fine masks per ROI |
| Merge | 3 ROI predictions | Rule-based label assignment | Final full-hand mask |

**Key design idea:** Stage 1 finds *where* the bones are → Stage 2 focuses on *fine detail* within each region.

**Why Stage 1 predictions (not GT) are used during inference:**  
At inference time, ground truth does not exist. Stage 1 acts as a coarse locator to define the crop bounding boxes for the new test image.

---

## ROI Group Design

### Training (Step 1) — Ground Truth used for cropping

```
ThumbROI (Dataset201):             Trapezium(7), Scaphoid(3), Metacarpal-1(11)
DigitsMetacarpalsROI (Dataset202): Metacarpals(11–15), Proximal/Middle/Distal phalanges(16–29)
CarpalsWristROI (Dataset203):      Radius(1), Ulna(2), Carpals(3–10)
```

### Inference (Step 3) — Stage 1 prediction used for cropping

The same label sets are used to locate each ROI in the Stage 1 prediction and compute the bounding box.

---

## Problem 1: Crops Are Too Large and Overlapping

### Observed crop sizes (test case HAND_008, full image = 868×410×410)

| ROI | Crop Shape | % of Full Volume |
|-----|-----------|-----------------|
| ThumbROI | 533 × 238 × 316 | ~61% |
| DigitsMetacarpalsROI | 555 × 347 × 379 | ~64% |
| CarpalsWristROI | 750 × 325 × 319 | ~87% |

All three crops cover the majority of the full CT volume and overlap heavily with each other.

### Root Cause

**1. Labels span the full z-axis (longitudinal axis of the scan)**  
The hand is imaged from fingertips to wrist along the z-axis. Most bone groups extend across this full length, so the bounding box always ends up covering nearly the entire z range.

**2. Overlapping label definitions**  
Some labels appear in more than one ROI group:

| Label | ThumbROI | DigitsMetacarpalsROI | CarpalsWristROI |
|-------|----------|---------------------|-----------------|
| Scaphoid (3) | ✓ | — | ✓ |
| Metacarpal-1 (11) | ✓ | ✓ | — |

Each shared label forces its ROI's bounding box to stretch further, making crops larger than necessary.

### Consequence

The three sub-models receive nearly identical input volumes. The network does not get a meaningfully focused view, which reduces the benefit of the 2-stage approach.

---

## Problem 2: Mismatch Between Training Labels and Merge Labels

The labels used during training (`ROI_GROUPS`) do not match the labels each ROI is responsible for at merge time (`ROI_PRIMARY_LABELS`):

| ROI | Trained on | Responsible for at merge |
|-----|-----------|--------------------------|
| ThumbROI | 3, 7, 11 | **7, 11 only** (scaphoid ignored) |
| CarpalsWristROI | 1–10 | **1–6, 8–10** (trapezium ignored) |
| DigitsMetacarpalsROI | 11–29 | **12–29** (metacarpal-1 ignored) |

Each model spent training capacity on labels that are never used in the final output, and the model assigned to predict a label may not have been the one trained most specifically for it.

---

## Merge Strategy

The merge resolves spatial overlap by assigning each label to exactly one authoritative ROI:

```python
ROI_PRIMARY_LABELS = {
    "CarpalsWristROI":      [1, 2, 3, 4, 5, 6, 8, 9, 10],
    "ThumbROI":             [7, 11],
    "DigitsMetacarpalsROI": list(range(12, 30)),
}
```

**Process:**
1. Initialise a zero array (background) matching the full CT size
2. For each ROI prediction, paste only its primary labels back into the correct bounding box position
3. No label is written more than once → no spatial conflict in the final output

**Limitation:** Even though the merge is clean, the predictions being pasted may be of lower quality because the models were trained on overlapping, unfocused crops.

---

## What's next? Recommendations for Improvement

### 1. Remove overlapping labels — each label in exactly one ROI
```
ThumbROI:             7 (trapezium), 11 (metacarpal-1)          ← thumb-specific only
DigitsMetacarpalsROI: 12–15 (metacarpals 2–5), 16–29 (phalanges)
CarpalsWristROI:      1 (radius), 2 (ulna), 3–6, 8–10 (other carpals)
```
Scaphoid (3) would need a deliberate home — it sits anatomically at the wrist, so CarpalsWristROI is appropriate.

### 2. Align training labels with merge labels
Train each ROI model only on the labels it will actually be responsible for in the merge. This removes wasted training capacity and keeps the model focused.

### 3. Consider axis-aligned splitting
Instead of grouping by anatomical category, split along the z-axis (longitudinal axis). For example:
- **Distal zone:** phalanges (fingertips to PIP joints)
- **Middle zone:** metacarpals + proximal phalanges
- **Proximal zone:** carpals + radius/ulna

This guarantees minimal z-axis overlap between crops.

### 4. Reduce margin if needed
The current 10 mm margin is reasonable, but if crops are already large, reducing to 5 mm may help tighten the focus without losing context.

---

## Summary

| Issue | Impact | Fix |
|-------|--------|-----|
| Overlapping label definitions in ROI_GROUPS | Crops cover ~60–87% of full volume | Remove shared labels |
| Training labels ≠ merge labels | Models trained on irrelevant labels | Align ROI_GROUPS with ROI_PRIMARY_LABELS |
| Bones span full z-axis | All crops are large in z | Split by spatial zone, not only anatomy |
| Large overlapping crops | 2-stage offers little benefit over baseline | Apply fixes above, then retrain |
