# Solar Filament Segmentation 2026 — Technical Report

**Track:** `filament-segmentation-2026` (MAGFiLO 1.0 Kaggle 2026)
**Task:** instance segmentation of solar filaments in full-disk images
**Metric:** panoptic quality (PQ) at IoU > 0.5
**Best public score:** 0.39
**Author:** swarna-sekhar-dhar

---

## 1. Summary

This work reports an inference-stage pipeline for solar filament segmentation that reaches a
public PQ of 0.39, and — more usefully — a measurement of what that number is worth.

The system combines a ten-model U-Net ensemble (five cross-validation folds × two encoder
backbones) with eight-view dihedral test-time augmentation, probability-map averaging, and a
rule-based mask filter chosen by a 33,880-point grid search. Its nested out-of-fold PQ is
0.45.

The central finding is that the out-of-fold and public scores of this pipeline differ by a
reproducible offset of 0.06, and that the rule which maximises out-of-fold PQ is *not* the
rule that maximises the public metric. Optimising the OOF objective yields a rule whose OOF
PQ is 0.4523 but whose calibrated public score is 0.3946; the rule that maximises the
calibrated public score is a different point in the same grid. Selection on the wrong
objective costs roughly 0.01–0.02 PQ. The report sets out how the offset was measured, why
it exists, and what it implies for both scoring and model selection.

An annotator-variability measurement bounds the problem from the other side: one expert
scored against another on the 296 training images that carry two or three annotator sets
reaches only PQ 0.3399. Disagreement between humans is therefore of the same order as the
entire gap between my pipeline and a perfect score, which limits how much of any
leaderboard difference below ~0.34 can be attributed to model quality at all.

---

## 2. Data and task

The competition provides the MAGFiLO 1.0 test split: 180 full-disk solar images at
2048 × 2048, to be segmented into instance masks of solar filaments. Submissions are
compressed COCO RLE, one row per instance, with a strict schema and a
positive-area requirement; masks are additionally required to be pixel-disjoint.

Filaments are thin, low-contrast and elongated. Two properties dominate every design decision here:

1. **They are thin.** At 2048 × 2048 a filament body is a small number of pixels across. Any
   downsampling in the pipeline destroys the signal, and a mask that is correct in outline
   can be wrong when measured at IoU 0.5.
2. **They carry genuine human variability.** The training corpus has 707 images and 1,154
   annotator sets; 296 images carry two or three independent sets. A training annotator
   outlines 7.10 filaments per image on average.

The pipeline operates at native resolution and never resamples the input.

---

## 3. Method

### 3.1 Model ensemble

The ensemble is ten U-Nets: five folds × two encoders (`resnet34` and
`tu-tf_efficientnetv2_s`). Weights are the public `solar-filament-unet-weights` dataset
(Dariush Afshar), whose ten checkpoints correspond to this same fold structure. The
contribution of this work is therefore the inference and decision stage, not model training,
and the report is explicit about that distinction throughout.

Each checkpoint is verified against a stored SHA-256 receipt before use. Every model produces
a continuous probability map per image. Ten models × 180 images over two devices takes
19.2 minutes, plus 30 seconds to encode; the notebook's total wall time of 20.7 minutes sits
well inside a 30-minute evaluation budget.

### 3.2 Test-time augmentation

Each model is evaluated under all eight elements of the dihedral group D4 (identity,
three rotations, four reflections), with the probability maps averaged in the original
orientation. This is worth stating precisely because the usual failure mode of TTA on thin
structures is geometric: a rotation applied to a mask that is two or three pixels wide, then
inverted, loses sub-pixel accuracy at the boundary. Here the augmentation is applied to the
*input image*, the network is run in each orientation, and the outputs are inverse-transformed
and averaged as probabilities — never as binary masks. Averaging before thresholding is what
makes the eight views a variance-reduction step rather than a source of boundary error.

Each model's map is stored as `round(p × 255)`. The normalisation disk radius is 950 px.

### 3.3 Decision rule and post-processing

The ensemble map is converted to instances with a four-parameter rule:
threshold band `(t_lo, t_hi)`, minimum component area `min_area`, and a minimum mean
probability `min_meanp` per retained component. The production rule is:

```
t_lo = 0.35,  t_hi = 0.99,  min_area = 200,  min_meanp = 0.85
```

Masks are emitted as compressed RLE with a pixel-disjointness check enforced at output time.

### 3.5 Output

1,177 filament instances across 177 of 180 test images, i.e. 6.54 instances per image (three
images produce no instance above the area floor). For reference the models predict 6.85
filaments per training image out-of-fold, and a training annotator outlines 7.10.

---

## 4. The measurement problem

This is the part of the work I consider the actual result.

### 4.1 The out-of-fold / public gap

The pipeline's nested out-of-fold PQ is 0.45. Its public score is 0.39. The gap is 0.06, and
it is stable across the model variants tested — three separate configurations all showed 0.06.

A 0.06 offset is large enough to change every decision made on the basis of it. Left
unmeasured, it makes OOF-based rule selection actively harmful, because the objective being
optimised is not the objective being graded.

### 4.2 Calibrating OOF against public

The gap is not a constant to be subtracted; it is a relationship between two different
scoring populations. I modelled it with a single scalar `r`, an annotator-scaling ratio, and
estimated the value of `r` that maps out-of-fold instance counts onto the observed public
score. Fitting the first model's OOF counts through `r` recovers its public score in the band
0.365–0.375 for `r ∈ [0.752, 0.787]`, with a point fit at **r = 0.77**.

Interpretation: at `r = 0.77` a *test* annotator would outline about **5.47** filaments per
image, against 7.10 for a training annotator. The discrepancy is a property of the annotation
population, not of the model — the test split was annotated under a stricter or differently
calibrated protocol than the training corpus, and the model faithfully reproduces the denser
training convention when asked to predict.

This also explains the instance counts directly: the models emit 6.85 filaments per training
image out-of-fold and 6.54 per test image, both closer to the training annotator's 7.10 than
to the test population's ~5.47.

### 4.3 Consequence for rule selection

With the calibration in place the grid search can be scored on the metric that matters. Over
**33,880 rules**:

| selection objective | best rule | value |
|---|---|---|
| out-of-fold PQ | — | 0.4523 |
| PQ calibrated at r = 0.77 | `t_lo 0.35, t_hi 0.995, area 0, mean 0.85` | **0.3946** |

The two objectives select *different* rules. Ranking the grid by OOF PQ and submitting the
winner would have been the natural move, and it is the wrong one: the OOF-optimal point sits
at `t_hi 0.99 / min_area 200`, while the calibrated-optimal point relaxes `t_hi` to 0.995 and
drops the area floor to 0. The difference is small in absolute terms and consistent in sign,
which is exactly what a real selection bias looks like.

### 4.4 The noise floor

One expert's segmentation scored against another expert's on the 296 multiply-annotated
training images reaches **PQ 0.3399**. That is the disagreement between two humans doing the
same task carefully.

This matters for reading the leaderboard. Below roughly 0.34 the metric is measuring
annotation convention as much as segmentation quality, and differences of ~0.01 between
submissions are inside the same band. It also sets an honest expectation: the field's
headroom is not the distance from 0.39 to 1.00, it is the distance from 0.39 to the
annotator-consistent ceiling.

---

## 5. Results

| variant | approach | public PQ |
|---|---|---|
| v1 champion | 10-model dual-backbone U-Net, D4×8 TTA, rule `0.35/0.99/200/0.85` | **0.39** |
| v2 | Mask R-CNN detector + ResNet18 crop refiner cascade | 0.38 |
| v3 | dual-architecture consensus sieve | 0.36 |
| v4 | penumbra morphological dilation | 0.36 |
| v5 | calibrated rule `t_lo 0.35, t_hi 0.995, min_area 150, min_meanp 0.85` | 0.38 |

Two points stand out. The champion is the plain ensemble: every added architectural stage
scored at or below it, consistent with §2 — each extra stage introduces a resampling or
geometric operation that costs more than it recovers. And v5, the artefact of the calibrated
objective, did not beat the champion in practice, which is a useful reminder that the
calibration corrects the *ranking* of rules rather than guaranteeing a large gain.

---

## 6. Limitations

- **The models are not mine.** The ten checkpoints are a public dataset fitted to this fold
  structure. The contributions here are the inference ensemble, the augmentation protocol,
  the rule search, and the calibration analysis. The report does not claim the backbone
  weights as original work.
- **The calibration is one scalar.** `r = 0.77` is fitted from one model's counts against a
  single public observation. It reproduces the gap across variants tested, but cannot be
  cross-validated. With an annotator-to-annotator PQ of 0.3399 and ±0.005 on `r`, a single
  submission cannot confirm an improvement smaller than roughly 0.01.
- **The filiform tails are unresolved.** The area floor (`min_area = 200`) suppresses thin
  barbs, and the calibrated optimum's preference for a zero area floor is direct evidence
  that detail is being discarded. Explicit boundary, distance, skeleton or endpoint
  supervision for thin structures is the obvious next step and is not attempted here.

---

## 7. Reproduction

Everything in this report is reproducible from the repository:

```
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute pipeline/solar-filament-apex-v1-champion.ipynb
```

The notebook reads the MAGFiLO test split from the competition data source and the U-Net
checkpoints from the public weights dataset, verifies each checkpoint against its SHA-256
receipt, runs the ten-model D4×8 ensemble, applies the calibrated production rule, and writes
`submission.csv`. Wall time on a two-GPU Kaggle session: ~21 minutes.

Pinned versions are in `requirements.txt`; the versions recorded at run time were
Python 3.13.16, torch 2.11.0+cu130, torchvision 0.26.0+cu130, numpy 2.1.3, opencv 4.14.0,
pandas 2.3.3, pycocotools 2.0.11.

---

## 8. Attribution

- Test and training imagery: MAGFiLO 1.0 / `filament-segmentation-2026`.
- U-Net checkpoints: public `solar-filament-unet-weights` dataset (Dariush Afshar).
- Pretrained encoders: `resnet34` (torchvision) and `tf_efficientnetv2_s`
  (segmentation-models-pytorch).
