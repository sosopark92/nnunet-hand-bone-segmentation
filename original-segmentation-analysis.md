# Original Baseline Segmentation — Results Analysis

## Experiment Setup

| Item | Value |
|------|-------|
| Dataset | Dataset100_HAND — KU Leuven hand/wrist CT |
| Training cases | 5 |
| Test case | HAND_008 (single case) |
| Model | nnUNetTrainer_250epochs, `3d_fullres` |
| Architecture | PlainConvUNet, 6-stage encoder-decoder |
| Patch size | 96 × 224 × 96 voxels |
| Median image size | 461 × 976 × 461 voxels |
| Voxel spacing | ~0.245 × 0.222 × 0.245 mm |
| Epochs | 250 (250 iterations/epoch) |
| Loss | Dice + Cross-Entropy with deep supervision |
| Optimizer | SGD (lr=0.01, momentum=0.99, Nesterov) |
| GPU | NVIDIA GeForce RTX 4090 |
| Classes | 29 foreground + background (30 total) |

---

## Per-Label Results (HAND_008, 250 epochs)

> Labels 26–29 (distal phalanges 2–5) have n_ref = 0 in the test case — these bones are not present in HAND_008 and are excluded from interpretation.

| Label | Bone | Dice | IoU | FN | FP | Interpretation |
|-------|------|------|-----|-----|-----|----------------|
| 1 | Radius | **0.000** | 0.000 | 713,170 | 1,310,855 | Complete failure — 0 TP despite heavy prediction |
| 2 | Ulna | **0.081** | 0.042 | 1,272,852 | 886,662 | Critical failure — 93% of volume missed |
| 3 | Scaphoid | 0.986 | 0.973 | 1,018 | 3,663 | Excellent |
| 4 | Lunate | 0.984 | 0.968 | 216 | 3,410 | Excellent |
| 5 | Triquetrum | 0.978 | 0.958 | 348 | 3,368 | Excellent |
| 6 | Pisiform | 0.976 | 0.953 | 1,023 | 1,617 | Excellent |
| 7 | Trapezium | 0.977 | 0.955 | 554 | 6,395 | Excellent |
| 8 | Trapezoid | 0.958 | 0.920 | 3,657 | 2,861 | Good |
| 9 | Capitate | 0.981 | 0.964 | 510 | 6,653 | Excellent |
| 10 | Hamate | 0.982 | 0.965 | 701 | 5,307 | Excellent |
| 11 | Metacarpal 1 | 0.926 | 0.862 | 44,530 | 2,309 | Good (under-segmented) |
| 12 | Metacarpal 2 | 0.834 | 0.716 | 54,907 | 106,345 | Moderate (large FP) |
| 13 | Metacarpal 3 | 0.725 | 0.569 | 130,802 | 79,618 | Poor |
| 14 | Metacarpal 4 | 0.733 | 0.579 | 111,354 | 32,260 | Poor |
| 15 | Metacarpal 5 | 0.745 | 0.594 | 100,305 | 2,750 | Moderate (large FN) |
| 16 | Proximal phalanx 1 | 0.985 | 0.970 | 1,926 | 3,298 | Excellent |
| 17 | Proximal phalanx 2 | 0.639 | 0.470 | 10,251 | 212,996 | Poor (massive FP — label confusion) |
| 18 | Proximal phalanx 3 | 0.260 | 0.149 | 206,989 | 35,697 | Very poor — mostly missed |
| 19 | Proximal phalanx 4 | 0.901 | 0.820 | 36,352 | 2,486 | Good |
| 20 | Proximal phalanx 5 | 0.976 | 0.953 | 515 | 5,694 | Excellent |
| 21 | Middle phalanx 2 | 0.657 | 0.489 | 26,070 | 12,012 | Poor |
| 22 | Middle phalanx 3 | 0.803 | 0.670 | 17,758 | 16,570 | Moderate |
| 23 | Middle phalanx 4 | 0.841 | 0.726 | 9,590 | 24,713 | Moderate |
| 24 | Middle phalanx 5 | 0.855 | 0.747 | 9,948 | 3,682 | Moderate |
| 25 | Distal phalanx 1 | 0.927 | 0.863 | 6,447 | 4,558 | Good |

---

## Performance by Anatomical Group

| Group | Labels | Dice Range | Overall |
|-------|--------|-----------|---------|
| Carpals | 3–10 | 0.958 – 0.986 | **Excellent** |
| Thumb bones | 7, 11, 16, 25 | 0.926 – 0.985 | **Good to Excellent** |
| Metacarpals 2–5 | 12–15 | 0.725 – 0.834 | **Mixed / Poor** |
| Proximal phalanges | 16–20 | 0.260 – 0.985 | **Highly inconsistent** |
| Middle phalanges | 21–24 | 0.657 – 0.855 | **Moderate** |
| Forearm (radius, ulna) | 1–2 | 0.000 – 0.081 | **Critical failure** |

---

## Key Observations

### 1. Radius and Ulna — Complete Failure

- **Radius (label 1):** Dice = 0.0. The model predicted 1.31M FP voxels for this class but achieved 0 TP. The ground truth has 713K voxels, none of which were correctly predicted.
- **Ulna (label 2):** Dice = 0.081. The model caught only ~7% of the reference volume (94K of 1.37M voxels).

**Why this happens — patch size mismatch with bone length:**
The radius and ulna run the full longitudinal extent of the CT (~976 voxels). The patch size along this axis is only 224 voxels — less than 25% of the bone's length. In any single patch during inference, the model sees only a short cylindrical cross-section of these bones without enough context to reliably classify it as a distinct long bone. The carpals, in contrast, are compact and fit comfortably within a single patch, which explains why they are segmented so well.

For radius, the unusual pattern of FP=1.31M with TP=0 suggests the model is predicting the label in the wrong spatial region entirely — possibly confusing part of the ulna or background cortical bone with the radius label.

### 2. Carpals — Near-Perfect

All eight carpal bones (labels 3–10) achieved Dice ≥ 0.958. Their compact size and distinctive CT appearance allow the model to learn them reliably within the patch window.

### 3. Thumb Anatomy — Already Good at Baseline

Trapezium (7), Metacarpal 1 (11), Proximal phalanx 1 (16), and Distal phalanx 1 (25) all scored above 0.92. The thumb is spatially distinct from the other fingers and does not suffer from the label confusion that affects the parallel fingers.

This is an important baseline context: the 2-stage experiment was motivated by wanting better thumb accuracy, but the baseline is already strong for the thumb.

### 4. Metacarpals 2–5 — Moderate Performance

- Metacarpal 2 (0.834) has large FP (106K), suggesting over-extension of prediction into adjacent tissue.
- Metacarpal 3 (0.725) and Metacarpal 4 (0.733) show high FN, meaning significant portions of the bone are simply not detected.
- Metacarpal 5 (0.745) has 100K FN — under-segmented, likely because it is at the lateral edge of the hand.

### 5. Proximal Phalanges — Severe Inconsistency

The five proximal phalanges range from Dice 0.260 to 0.985, making this the most inconsistent group:

- **Phalanx 1 (0.985):** Excellent — thumb is spatially isolated.
- **Phalanx 5 (0.976):** Excellent — the 5th finger is on the edge and has distinct position.
- **Phalanx 4 (0.901):** Good.
- **Phalanx 2 (0.639):** Poor, with 212,996 FP. The model is spreading predictions for this label into neighbouring structures — likely label confusion with the adjacent phalanges 3 or 4.
- **Phalanx 3 (0.260):** Very poor — 207K of 249K reference voxels are missed. The middle finger's proximal phalanx is in the center of the hand, surrounded by similar-looking structures, making it hard to isolate.

**Root cause:** The parallel, visually similar fingers (especially 2, 3, 4) are difficult to distinguish at the patch level without global positional context. Within a small patch, the model cannot easily determine which finger it is looking at.

### 6. Middle Phalanges — Moderate

Middle phalanges (21–24) score 0.657–0.855. The same finger-confusion problem applies, though the gradient is less extreme than proximal phalanges.

---

## Summary Table

| Issue | Affected Labels | Root Cause |
|-------|----------------|------------|
| Radius/ulna complete failure | 1, 2 | Patch too small for long bones; no global extent context |
| Metacarpal under/over-segmentation | 12–15 | Mixed: over-prediction for MC2, under-detection for MC3–5 |
| Proximal phalanx label confusion | 17 (FP), 18 (FN) | Parallel fingers appear identical in local patches |
| Proximal phalanx 3 missed entirely | 18 | Surrounded by adjacent similar structures, no positional cue |

---

## Relation to the 2-Stage Experiment

The 2-stage pipeline was designed to improve segmentation by focusing on anatomical sub-regions. Based on these baseline results:

- **Thumb ROI (labels 7, 11, 16):** Baseline is already good (0.926–0.977). The 2-stage approach may offer only marginal gain here.
- **CarpalsWristROI (labels 1–10):** Carpals are excellent but **radius and ulna are the critical failures** in this group. ROI cropping alone may not help if the crop still spans the full bone length; the patch-size-to-bone-length mismatch remains.
- **DigitsMetacarpalsROI (labels 12–29):** This is where the most room for improvement exists — metacarpals 3/4 and the parallel proximal/middle phalanges are consistently weak.

The baseline makes clear that the main problem is not small bones (carpals are fine) but **long bones** (radius, ulna) and **positionally ambiguous parallel structures** (middle fingers). The 2-stage design should be evaluated against these specific failure modes.
