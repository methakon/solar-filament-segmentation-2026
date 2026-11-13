"""Make the released repo reproduce the submission without a Kaggle dataset input.

Two defects in the current release:
  1. the notebook resolves its weights through find_file() under /kaggle/input, i.e. it needs a
     mounted Kaggle dataset -- an "additional file" the committee is explicitly told they should
     not need;
  2. the repo therefore contains no weights at all, and the form requires them to be stored in
     the repo and loaded by the notebook so the run reproduces without re-training.

This patches the lookup to prefer a repo-local weights/ directory and still fall back to the
Kaggle mount, so the same notebook runs unchanged on Kaggle and reproduces from the repo.
"""
import json
import pathlib

NB = pathlib.Path.home() / "projects/kaggle-/filament-final-release/pipeline/solar-filament-apex-v1-champion.ipynb"

OLD = '''RECEIPT_PATH = find_file("solar_unet_receipt.json")
WEIGHTS_DIR = os.path.dirname(RECEIPT_PATH)'''

NEW = '''# Weights are stored in this repository (weights/), so the run reproduces with no Kaggle
# dataset mounted. The Kaggle mount is still honoured as a fallback, which keeps this same
# notebook runnable inside the competition environment.
_LOCAL = [os.path.join(os.getcwd(), "weights"), "weights", "../weights"]
WEIGHTS_DIR = next((d for d in _LOCAL
                    if os.path.exists(os.path.join(d, "solar_unet_receipt.json"))), None)
if WEIGHTS_DIR is None:
    WEIGHTS_DIR = os.path.dirname(find_file("solar_unet_receipt.json"))
RECEIPT_PATH = os.path.join(WEIGHTS_DIR, "solar_unet_receipt.json")
assert os.path.exists(RECEIPT_PATH), RECEIPT_PATH'''

nb = json.load(open(NB))
hits = 0
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    if OLD in src:
        cell["source"] = src.replace(OLD, NEW).splitlines(keepends=True)
        hits += 1
assert hits == 1, f"expected exactly one patch site, found {hits}"

# The grid the keep rule is chosen from must also live in the repo.
G_OLD = 'grid = pd.read_csv(find_file("oof_keep_rule_grid.csv"))'
G_NEW = ('_g = os.path.join(WEIGHTS_DIR, "oof_keep_rule_grid.csv")\n'
         'grid = pd.read_csv(_g if os.path.exists(_g) else find_file("oof_keep_rule_grid.csv"))')
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    if G_OLD in src:
        cell["source"] = src.replace(G_OLD, G_NEW).splitlines(keepends=True)
        hits += 1

json.dump(nb, open(NB, "w"))
print(f"patched {NB.name}: weights lookup + keep-rule grid now resolve inside the repo")
