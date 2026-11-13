"""Render REPORT.md to a clean, print-ready HTML for PDF conversion.

Handles only what the report uses: headings, paragraphs, tables, fenced code, bullet lists,
bold and inline code. Deliberately small so the output is predictable.
"""
import html
import pathlib
import re

src = pathlib.Path("REPORT.md").read_text()
lines = src.splitlines()
out, i = [], 0
in_code = False
in_list = False
in_table = False

def inline(t):
    t = html.escape(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    return t

def close_list():
    global in_list
    if in_list:
        out.append("</ul>")
        in_list = False

def close_table():
    global in_table
    if in_table:
        out.append("</tbody></table>")
        in_table = False

while i < len(lines):
    line = lines[i]

    if line.strip().startswith("```"):
        close_list(); close_table()
        if not in_code:
            out.append("<pre>")
            in_code = True
        else:
            out.append("</pre>")
            in_code = False
        i += 1
        continue
    if in_code:
        out.append(html.escape(line))
        i += 1
        continue

    if re.match(r"^\s*\|.*\|\s*$", line):
        close_list()
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not in_table:
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in cells) + "</tr></thead><tbody>")
            in_table = True
            i += 2                      # skip the |---| separator row
            continue
        out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
        i += 1
        continue
    close_table()

    m = re.match(r"^(#{1,4})\s+(.*)$", line)
    if m:
        close_list()
        lvl = len(m.group(1))
        out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
        i += 1
        continue

    if re.match(r"^\s*[-*]\s+", line):
        if not in_list:
            out.append("<ul>")
            in_list = True
        out.append("<li>" + inline(re.sub(r"^\s*[-*]\s+", "", line)) + "</li>")
        i += 1
        continue
    close_list()

    if line.strip() == "---":
        out.append("<hr/>")
        i += 1
        continue

    if line.strip():
        out.append(f"<p>{inline(line)}</p>")
    i += 1

close_list(); close_table()

doc = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Solar Filament Segmentation 2026 - Technical Report</title>
<style>
@page {{ size: A4; margin: 11mm 11mm; }}
body {{ font-family: Georgia, 'Times New Roman', serif; font-size: 8.7pt; line-height: 1.19; color: #111; }}
h1 {{ font-size: 14.5pt; margin: 0 0 2mm 0; }}
h2 {{ font-size: 10.2pt; margin: 2.6mm 0 1mm 0; border-bottom: 0.6pt solid #999; padding-bottom: 1mm; }}
h3 {{ font-size: 9.6pt; margin: 2.4mm 0 1mm 0; }}
p {{ margin: 0 0 1.15mm 0; text-align: justify; }}
code {{ font-family: 'DejaVu Sans Mono', monospace; font-size: 7.9pt; background: #f2f2f2; padding: 0 1px; }}
pre {{ font-family: 'DejaVu Sans Mono', monospace; font-size: 7.7pt; background: #f6f6f6;
       border-left: 2pt solid #bbb; padding: 1.1mm 1.8mm; margin: 0 0 1.5mm 0; white-space: pre-wrap; }}
table {{ border-collapse: collapse; width: 100%; margin: 0 0 3mm 0; font-size: 7.9pt; }}
th, td {{ border: 0.5pt solid #aaa; padding: 0.7mm 1.4mm; text-align: left; vertical-align: top; }}
th {{ background: #eeeeee; }}
ul {{ margin: 0 0 3mm 5mm; padding: 0; }}
li {{ margin-bottom: 1mm; }}
hr {{ border: none; border-top: 0.5pt solid #ccc; margin: 4mm 0; }}
</style></head><body>
{chr(10).join(out)}
</body></html>"""

pathlib.Path("report.html").write_text(doc)
print(f"wrote report.html ({len(doc)} bytes, {len(out)} blocks)")
