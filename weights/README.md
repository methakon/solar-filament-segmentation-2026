# Solar Filament U-Net Weights (PQ 0.45 OOF)

Ten U-Net models I trained for the [Solar Filament Segmentation Challenge 2026](https://www.kaggle.com/competitions/filament-segmentation-2026): five folds with a ResNet34 encoder and five with an EfficientNetV2-S encoder. Averaged, they score a nested out-of-fold PQ of **0.4502** on all 707 training images and **0.39** on the public leaderboard. My notebook [Solar Filament U-Net: OOF 0.45 vs Public 0.39](https://www.kaggle.com/code/dariushafshar/solar-filament-u-net-oof-0-45-vs-public-0-39) turns them into a checked submission.csv in one run, with internet off.

## Files

| file | what it is |
|---|---|
| `unet_resnet34_fold0.pt` to `unet_resnet34_fold4.pt` | U-Net with a ResNet34 encoder, one per fold; segmentation_models_pytorch 0.5.0 state dicts, 97.9 MB each |
| `unet_tu-tf_efficientnetv2_s_fold0.pt` to `..._fold4.pt` | U-Net with an EfficientNetV2-S encoder (timm), one per fold, 89.3 MB each |
| `folds.csv` | the fold each training image was held out in (`stem`, `fold`). The fold k models never saw the fold k images, so you can check out-of-fold scores yourself |
| `oof_keep_rule_grid.csv` | out-of-fold PQ of the averaged models for every keep rule I searched, so you can pick a different rule and see what it scored |
| `keep_rule_train.npz` | the training table for the learned keep rule (below): 16 features and the target for each of 8,211 out-of-fold candidate regions. Numbers only: no images, masks or polygons |
| `solar_unet_receipt.json` | the numbers on this card, the keep rules, and the sha256 of every weight file |
| `segmentation_models_pytorch-0.5.0-py3-none-any.whl` | the library the models need, unmodified from PyPI, so a notebook can install it with internet off |
| `README.md` | this text |

## How they were trained

- Data: the competition's 707 training images and their annotations; no other labels or images. Five folds, grouped by image (all annotators of an image in the same fold) and stratified by the site code in the file name and the number of annotators.
- Target: for each image, the mean of its annotators' masks, so a pixel two of three annotators marked has target 2/3.
- Model: segmentation_models_pytorch U-Net with 1 input channel. Encoders start from ImageNet weights (ResNet34: smp 'imagenet' weights; EfficientNetV2-S: timm tf_efficientnetv2_s.in21k_ft_in1k).
- Input: each image is normalised by its own mean and standard deviation inside a 950 px circle around the centre, which covers the solar disk.
- Training: random 512 px crops at full resolution (70% centred on a filament), flips and 90 degree rotations, mild gamma and contrast jitter; BCE on the soft target plus soft Dice; AdamW at lr 0.0003 with weight decay 0.0001, 300 warmup steps then cosine; batch 16 for 10,500 steps per fold, float16.
- Inference: the full 2048 x 2048 image, averaged over 8 flips and rotations, then the 10 models averaged.
- Filaments: regions where p > 0.35 (8-connected), kept when their peak is above 0.99, their mean probability is at least 0.85 and their area is at least 200 px. I chose this rule by nested cross-validation.

## Scores

| models | keep rule (t_lo, t_hi, min_area, min_meanp) | nested OOF PQ | public LB |
|---|---|---|---|
| 5 x ResNet34 | 0.15, 0.97, 250, 0.70 | 0.4299 | 0.37 |
| 5 x EfficientNetV2-S | 0.35, 0.995, 0, 0.85 | 0.4461 | 0.39 |
| all 10, averaged | 0.35, 0.99, 200, 0.85 | 0.4502 | 0.39 |
| all 10, averaged, learned keep rule | learned (see below) | 0.4552 | 0.39 |

Nested OOF means the keep rule is chosen on four folds and scored on the fifth, pooled over all 1,154 annotator-sets with the host's PQ logic. The public score came out about 0.06 lower every time. My best explanation is that the test images were labelled more sparsely than the training images. If each filament a training annotator would draw shows up in the test labels with probability r, my first model's 0.37 implies r of about 0.77, and that same r predicted the next two scores before I submitted them; both came back 0.39. The notebook shows the arithmetic. It is a model that fits, not a proof.

## A learned keep rule

The box rule above looks at three numbers per candidate. The learned rule fits a small gradient-boosted model (scikit-learn `HistGradientBoostingRegressor`, depth 3, 200 iterations) on 16 numbers per candidate region (area, mean and peak probability, shape, contrast against its surroundings, position on the disk) and keeps a candidate when its predicted matched IoU is above 0.26. Nested by fold, scored with the sparse-label estimate PQ' (r = 0.77): box rule 0.3935, learned rule 0.3993, a gain of +0.0058 with a paired bootstrap SD of 0.0014, and all five folds improved. On the public board the learned rule's file scored 0.39, the same as the box rule's: a gain this small is below what the public board can resolve. `keep_rule_train.npz` holds the training table, so the notebook refits the model in seconds.

## How to load one

```python
import torch
import segmentation_models_pytorch as smp

model = smp.Unet(encoder_name="resnet34", encoder_weights=None, in_channels=1, classes=1)
model.load_state_dict(torch.load("unet_resnet34_fold0.pt", map_location="cpu", weights_only=True))
model.eval()  # for the other family: encoder_name="tu-tf_efficientnetv2_s"
# input: float32 (N, 1, 2048, 2048) = (pixel / 255 - mean) / std, mean and std taken inside the disk
# output: one logit per pixel; sigmoid gives the filament probability
```

With internet off, install the library first: `pip install --no-index --no-deps segmentation_models_pytorch-0.5.0-py3-none-any.whl`. The Kaggle image already has torch, timm and its other requirements.

## License and provenance

- My weights, tables and this README are CC BY-NC-SA 4.0, keeping the non-commercial terms of the competition data they were trained on.
- They were trained only on the competition's training data, which the host released under CC BY-NC 4.0, and the competition rules allow that data for non-commercial use. If you use the weights outside the competition, check those terms too.
- The wheel is segmentation_models_pytorch by Pavel Iakubovskii, MIT license (the license text is inside the wheel), sha256 c34e09047771aa4d, the same as on PyPI.
- No competition images, masks or labels are in this dataset. `folds.csv` holds file names and fold numbers, and `oof_keep_rule_grid.csv` holds counts pooled over all images.
- How the metric works and what one expert scores against another: [Filament PQ: Two Experts Agree at 0.34](https://www.kaggle.com/code/dariushafshar/filament-pq-two-experts-agree-at-0-34).
