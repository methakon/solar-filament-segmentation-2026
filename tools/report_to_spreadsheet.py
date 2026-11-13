"""Emit the technical report as a spreadsheet, the only type the form's upload field accepts.

The field's accept list is spreadsheet-only:
  .xls .xlsx .xlsm .xltm .ods .csv plus Google Sheets and Drive folders.
No PDF, DOCX or plain text. So the report is laid out as rows: one row per paragraph, with its
section and subsection, which stays readable when opened as a sheet.
"""
import csv
import pathlib
import re

BASE = pathlib.Path.home() / "projects/kaggle-/filament-final-release"
md = (BASE / "REPORT.md").read_text(encoding="utf-8")

rows = [["Section", "Subsection", "Content"]]
section = subsection = ""
for block in md.split("\n"):
    line = block.rstrip()
    if not line.strip():
        continue
    m = re.match(r"^#\s+(.*)$", line)
    if m:
        section, subsection = m.group(1), ""
        continue
    m = re.match(r"^##\s+(.*)$", line)
    if m:
        section, subsection = m.group(1), ""
        continue
    m = re.match(r"^###\s+(.*)$", line)
    if m:
        subsection = m.group(1)
        continue
    text = re.sub(r"^\s*[-*]\s+", "", line).strip()
    text = text.replace("**", "").replace("`", "")
    rows.append([section, subsection, text])

csv_path = BASE / "report.csv"
with open(csv_path, "w", newline="", encoding="utf-8-sig") as fh:
    csv.writer(fh).writerows(rows)

print(f"wrote {csv_path.name}: {len(rows)-1} content rows")
print(f"  sections: {sorted({r[0] for r in rows[1:] if r[0]})[:9]}")
