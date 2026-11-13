"""Re-section the report onto the template outline WITHOUT losing subsections, and record the
reproducibility work.

Previous attempt split the markdown on every heading including '###', so each subsection became its
own block and only the parent's opening paragraph survived -- Methodology dropped from 2995 to 764
characters. This splits on '##' only, so subsections stay with their parent.

It also adds a Reproduction subsection describing the weights now stored in the repository, which
the report predates: the form requires the committee to be able to reproduce the predictions, so
the report must say where the weights live and how they are verified.
"""
import pathlib
import re

BASE = pathlib.Path.home() / "projects/kaggle-/filament-final-release"
md = (BASE / "REPORT.md").read_text(encoding="utf-8")

# split on level-2 headings only, so '###' subsections remain inside their parent section
parts = re.split(r"\n(?=## )", md)
head = parts[0].strip()
secs = []
for p in parts[1:]:
    title = re.sub(r"^##\s*", "", p.splitlines()[0]).strip()
    secs.append((title, p.rstrip()))


def grab(*prefixes):
    out = []
    for pref in prefixes:
        for title, text in secs:
            if title.startswith(pref):
                out.append(text)
    return "\n\n".join(out)


REPRO = """## 2.3 Reproduction

The ten U-Net fold checkpoints are stored in this repository under `weights/`, so the pipeline
reproduces the submitted predictions without re-training and without any mounted dataset. Each
checkpoint is verified against the sha256 recorded in `weights/solar_unet_receipt.json` before use,
and the notebook prefers the repository copy, falling back to a Kaggle mount only if the local one
is absent. `requirements.txt` pins the library versions, including the `segmentation_models_pytorch`
wheel the encoders need, which is vendored into the same directory so the run needs no internet.
The out-of-fold keep-rule grid that selects the decision rule is stored alongside them, so the rule
can be re-derived rather than taken on trust.

The weights were trained by Kaggle user **dariushafshar** on the competition's 707 labelled training
images and are redistributed here unmodified; this is credited in `NOTICE.md`. The contributions of
this work are the inference-stage pipeline, the decision-rule analysis of Section 3, and the
reproducibility packaging.
"""

def first_sentences(text, n=3):
    """A real abstract is short -- the introduction already carries the full summary."""
    body = text.split("\n", 1)[-1].strip().replace("\n", " ")
    parts = re.split(r"(?<=[.;])\s+", body)
    return " ".join(parts[:n])


aligned = f"""# Solar Filament Segmentation 2026 — Technical Report

**Track:** filament-segmentation-2026 (MAGFiLO 1.0, Kaggle 2026)
**Task:** instance segmentation of solar filaments in full-disk images
**Metric:** panoptic quality (PQ) at IoU > 0.5
**Best public score:** 0.39

## Abstract

{first_sentences(grab("1. Summary"))}

## 1. Introduction

{grab("1. Summary", "2. Data and task")}

## 2. Methodology

{grab("3. Method")}

{REPRO}

## 3. Evaluation

{grab("4. The measurement problem", "5. Results", "6. Limitations")}

## 4. Acknowledgment

{grab("8. Attribution")}
"""

out = BASE / "REPORT_TEMPLATE_ALIGNED.md"
out.write_text(aligned, encoding="utf-8")

print(f"aligned report: {len(aligned)} chars (original {len(md)})")
for title, text in [("Abstract", grab("1. Summary")), ("Introduction", grab("1. Summary", "2. Data and task")),
                    ("Methodology", grab("3. Method") + REPRO), ("Evaluation", grab("4. The measurement problem", "5. Results", "6. Limitations", "7. Reproduction")),
                    ("Acknowledgment", grab("8. Attribution"))]:
    print(f"  {title:16s} {len(text):6d} chars")
missing = [k for k in ["ResNet34", "EfficientNetV2", "0.4523", "dariushafshar", "sha256", "out-of-fold", "0.39", "keep rule", "U-Net"] if k.lower() not in aligned.lower()]
print("missing key terms:", missing if missing else "none")
