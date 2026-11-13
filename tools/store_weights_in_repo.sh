#!/usr/bin/env bash
# Store the model weights in the released repository so the submission reproduces without a
# Kaggle dataset mount and without re-training (the form's explicit requirement).
set -euo pipefail

SRC="$TMPDIR/filw"
REPO="$HOME/projects/kaggle-/filament-final-release"
cd "$REPO"

echo "=== repo identity ==="
git remote -v | head -2
git log --oneline -2
echo

python3 "$REPO/tools/patch_nb_repo_weights.py"

echo "=== staging weights ($(du -sh "$SRC" | cut -f1)) ==="
mkdir -p weights
cp -f "$SRC"/*.pt "$SRC"/solar_unet_receipt.json "$SRC"/oof_keep_rule_grid.csv \
      "$SRC"/folds.csv "$SRC"/keep_rule_train.npz "$SRC"/README.md "$SRC"/*.whl weights/
# the wheel is the library the models need, kept so the notebook installs with internet off
ls -la weights | awk '{printf "  %10s  %s\n",$5,$9}' | tail -n +4

echo
echo "=== weight integrity (sha256 vs receipt) ==="
python3 - <<'PY'
import hashlib, json, pathlib
w = pathlib.Path("weights")
rec = json.load(open(w / "solar_unet_receipt.json"))
bad = 0
for m in rec["ensemble"]["models"]:
    h = hashlib.sha256((w / m["file"]).read_bytes()).hexdigest()
    ok = h == m["sha256"]
    bad += not ok
    print(f"  {m['file']:42s} {'OK' if ok else 'MISMATCH'}")
print(f"  -> {len(rec['ensemble']['models'])} weights, {bad} mismatched")
raise SystemExit(1 if bad else 0)
PY

echo
echo "=== provenance credit ==="
if ! grep -qi "dariushafshar" NOTICE.md; then
  cat >> NOTICE.md <<'EOF'

## Third-party model weights

`weights/` holds ten U-Net fold checkpoints (five ResNet34, five EfficientNetV2-S encoders)
published by Kaggle user **dariushafshar** as the public dataset
`solar-filament-unet-weights`, together with that dataset's receipt, out-of-fold keep-rule grid
and folds table. They are redistributed here unmodified so this repository reproduces the
submitted predictions on its own; each file's sha256 is verified against
`weights/solar_unet_receipt.json` before use. Trained on the competition's 707 labelled training
images only.
EOF
fi
git add -A
git status --short | head -8
echo "  staged files: $(git status --porcelain | wc -l)"

echo
echo "=== commit + push ==="
git commit -q -m "Store the ten U-Net fold checkpoints and the out-of-fold keep-rule grid in the repository

Makes the released notebook self-contained: it loads the weights from weights/ and verifies each
one against the receipt's sha256, so predictions reproduce without re-training and without any
mounted dataset." || echo "(nothing to commit)"
git push origin HEAD 2>&1 | tail -3
echo
echo "DONE: $(git log --oneline -1)"
