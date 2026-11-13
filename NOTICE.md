# Attribution and third-party components

This repository contains the inference and decision-stage pipeline together with its
evaluation. It does not contain trained model weights. The components below belong to their
respective authors.

## Model checkpoints

The ten U-Net checkpoints consumed by `pipeline/solar-filament-apex-v1-champion.ipynb` are
distributed as the public Kaggle dataset **`solar-filament-unet-weights`** (Dariush Afshar),
which provides one checkpoint per fold for two encoder backbones:

- `unet_resnet34_fold{0..4}.pt`
- `unet_tu-tf_efficientnetv2_s_fold{0..4}.pt`

They are not redistributed here. The pipeline verifies each checkpoint against a stored
SHA-256 receipt at run time.

## Encoder backbones

- `resnet34` — torchvision, pretrained on ImageNet.
- `tu-tf_efficientnetv2_s` — via `segmentation-models-pytorch` / `timm`, pretrained on
  ImageNet.

## Data

- Test split and training corpus: **MAGFiLO 1.0**, competition
  `filament-segmentation-2026`. Images are not redistributed here.

## This repository

Original to this work: the ensemble inference harness, the dihedral probability-space
augmentation protocol, the four-parameter mask rule and the 33,880-point search over it, the
out-of-fold-to-public calibration and noise-floor analysis, and the accompanying text.

If you reuse any of the above, cite this repository and the upstream components listed here.

## Third-party model weights

`weights/` holds ten U-Net fold checkpoints (five ResNet34, five EfficientNetV2-S encoders)
published by Kaggle user **dariushafshar** as the public dataset
`solar-filament-unet-weights`, together with that dataset's receipt, out-of-fold keep-rule grid
and folds table. They are redistributed here unmodified so this repository reproduces the
submitted predictions on its own; each file's sha256 is verified against
`weights/solar_unet_receipt.json` before use. Trained on the competition's 707 labelled training
images only.
