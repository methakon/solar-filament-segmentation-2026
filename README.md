# Solar Filament Segmentation 2026

Instance segmentation of solar filaments in full-disk images, for the
`filament-segmentation-2026` (MAGFiLO 1.0 Kaggle 2026) competition.
Metric: panoptic quality (PQ) at IoU > 0.5. **Best public score: 0.39.**

The full write-up is in [REPORT.md](REPORT.md). The short version:

- **Pipeline** — ten U-Net checkpoints (5 folds × 2 encoders: `resnet34`,
  `tu-tf_efficientnetv2_s`) run across all eight dihedral views, averaged as probabilities,
  thresholded and filtered by a four-parameter rule, emitted as pixel-disjoint COCO RLE.
- **Runtime** — ~21 minutes end to end on a two-GPU Kaggle session, inside a 30-minute budget.
- **The result worth reading** — the pipeline's out-of-fold PQ is 0.45 but its public score is
  0.39, a stable 0.06 gap. The rule that maximises OOF PQ is *not* the rule that maximises the
  public metric (0.4523 vs a calibrated 0.3946). Selecting on the wrong objective costs
  0.01–0.02 PQ. For calibration and the noise floor, see §4 of the report.

## Layout

```
REPORT.md                                      technical report, markdown source
report.pdf                                     technical report, 4 pages A4 (the deliverable)
report.html                                    intermediate render
tools/md_to_html.py                            renders REPORT.md -> PDF (via libreoffice)
requirements.txt                               pinned dependencies
NOTICE.md                                      third-party attribution
pipeline/
  solar-filament-apex-v1-champion.ipynb        the submitted pipeline, self-contained
results/
  submission_v1_champion.csv                   the 0.39 submission (1,177 instances)
  solar-filament-apex-v1-champion.log          run log: checkpoint receipts, timings, rule grid
```

## Reproduce

```bash
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute pipeline/solar-filament-apex-v1-champion.ipynb
```

The notebook expects two inputs, both already public:

1. the competition data source `filament-segmentation-2026` (test split);
2. the `solar-filament-unet-weights` dataset for the ten checkpoints.

Each checkpoint is verified against a stored SHA-256 receipt before it is used, so a corrupted
or substituted weight file fails loudly rather than silently degrading the score. Total
runtime is about 20 minutes on two GPUs.

## What is and is not original here

The U-Net **checkpoints are a public dataset** fitted to this same five-fold split. **This work
contributes the inference and decision stage**: the ten-model ensemble across dihedral
augmentation, probability-space (not mask-space) averaging, the four-parameter mask rule and
its search, and the out-of-fold-to-public calibration analysis in §4. The report states this
explicitly and does not claim the backbone weights as original. Attribution is in
[NOTICE.md](NOTICE.md).

## Honest limitations

- With one public observation per variant, the calibration scalar (`r = 0.77`) reproduces the
  gap but cannot be cross-validated.
- A leaderboard improvement smaller than ~0.01 cannot be confirmed by a single submission.
- One expert scored against another reaches only PQ 0.3399 on the multiply-annotated training
  images — model differences below that band are measuring annotation convention as much as
  segmentation quality.
- Thin filament barbs are suppressed by the area floor; the calibrated optimum's preference for
  a zero area floor is direct evidence that detail is being discarded.
