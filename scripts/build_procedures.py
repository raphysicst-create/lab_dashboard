"""Validate the per-activity textbook review and export only confirmed student steps."""

import argparse
import hashlib
import json
import re
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "outputs/review/procedures"
PUBLIC = ROOT / "site/dist/data"
FIGURES = PUBLIC.parent / "procedure-figures"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def student_text(value):
    return (isinstance(value, str) and bool(value.strip()) and value == value.strip()
            and not re.search(r"\[\[|!\[|\]\(|https?://|[A-Z]:[\\/]|textbook_wiki|\.pdf\b|[\x00-\x1f\ue000-\uf8ff\ufffd]", value, re.I))


def validate_row(row, filename, sources):
    key = row["id"]
    require(row["pdf"] == filename, f"{key}: incorrect source PDF")
    for field in ("pdf_pages", "printed_pages"):
        pages = row[field]
        require(isinstance(pages, list) and pages and all(type(p) is int and p >= 1 for p in pages)
                and pages == sorted(set(pages)), f"{key}: invalid {field}")
    require(max(row["pdf_pages"]) <= sources[filename]["page_count"], f"{key}: PDF page out of bounds")
    require(len(row["pdf_pages"]) == len(row["printed_pages"]), f"{key}: unpaired source pages")
    require(isinstance(row["note"], str) and row["note"].strip(), f"{key}: missing review note")
    if row["status"] in ("pending", "held"):
        require(row["groups"] is None, f"{key}: unresolved steps must be null")
        return None
    require(row["status"] == "confirmed", f"{key}: unknown review status")
    groups = row["groups"]
    require(isinstance(groups, list) and groups, f"{key}: missing groups")
    referenced = set()
    for group in groups:
        require(isinstance(group, dict) and set(group) in ({"heading", "steps"}, {"heading", "steps", "figures"}), f"{key}: invalid group")
        require(group["heading"] is None or student_text(group["heading"]), f"{key}: invalid heading")
        steps = group["steps"]
        require(isinstance(steps, list) and steps and all(student_text(s) for s in steps),
                f"{key}: missing or invalid student steps")
        if "figures" in group:
            require(isinstance(group["figures"], list) and group["figures"], f"{key}: invalid figure list")
            for figure in group["figures"]:
                require(isinstance(figure, dict) and set(figure) == {"file", "alt", "caption"}
                        and all(student_text(figure[k]) for k in ("caption", "alt")), f"{key}: invalid figure")
                name = figure["file"]
                require(isinstance(name, str) and re.fullmatch(re.escape(key) + r"-original-[0-9]{2}\.svg", name)
                        and name not in referenced, f"{key}: invalid or repeated figure filename")
                referenced.add(name)
                path = FIGURES / name
                require(path.is_file() and not path.is_symlink(), f"{key}: missing figure {name}")
                raw = path.read_text(encoding="utf-8")
                require("<!DOCTYPE" not in raw.upper() and "<!ENTITY" not in raw.upper(),
                        f"{key}: SVG declarations are not allowed")
                tree = ET.fromstring(raw)
                require(tree.tag == "{http://www.w3.org/2000/svg}svg" and "viewBox" in tree.attrib,
                        f"{key}: invalid SVG root")
                allowed = {"svg", "g", "defs", "style", "title", "desc", "rect", "circle", "ellipse",
                           "line", "polyline", "polygon", "path", "text", "tspan", "marker",
                           "linearGradient", "radialGradient", "stop", "clipPath", "pattern"}
                for element in tree.iter():
                    tag = element.tag.rsplit("}", 1)[-1]
                    require(tag in allowed, f"{key}: forbidden SVG element {tag}")
                    for attribute, value in element.attrib.items():
                        attribute = attribute.rsplit("}", 1)[-1].lower()
                        require(not attribute.startswith("on") and attribute not in {"href", "src"},
                                f"{key}: SVG must be self contained")
                        require(not re.search(r"(?:https?:|data:|@import)", value, re.I),
                                f"{key}: external or embedded image resource")
                require(not re.search(r"(?:@import|url\(\s*['\"]?(?:https?:|data:))", raw, re.I),
                        f"{key}: external SVG style resource")
    return groups


def build(source_dir):
    activities = read(PUBLIC / "activities.json")
    source_index = read(REVIEW / "source-index.json")
    sources = read(REVIEW / "source-files.json")
    if source_dir:
        for name, data in sources.items():
            digest = hashlib.sha256()
            with (source_dir / name).open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            require(digest.hexdigest() == data["sha256"], f"Changed PDF: {name}")
    rows = {}
    counts = Counter()
    for section in ("legacy", "middle", "high"):
        for row in read(REVIEW / f"{section}.json"):
            key = row["id"]
            require(key in source_index and key not in rows, f"Unknown or duplicate activity: {key}")
            source = source_index[key]
            filename = source["pdf"]
            anchors = set(zip(source["pdf_pages"], source["printed_pages"]))
            rows[key] = validate_row(row, filename, sources)
            corrected = not anchors.intersection(zip(row["pdf_pages"], row["printed_pages"]))
            require(row.get("reference_correction", False) is corrected,
                    f"{key}: record whether the reviewed pages correct the original reference")
            counts[row["status"]] += 1
    ids = [activity["id"] for activity in activities]
    require(len(ids) == len(rows) and set(ids) == set(rows) == set(source_index),
            "Review must cover every activity exactly once")
    referenced = {f["file"] for groups in rows.values() if groups
                  for group in groups for f in group.get("figures", [])}
    require(referenced == {p.name for p in FIGURES.glob("*")}, "Unreferenced files in public procedure figures")
    return {key: rows[key] for key in ids}, counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare with the public JSON without writing")
    parser.add_argument("--source-dir", type=Path, help="Also verify the checksums of the original PDFs")
    args = parser.parse_args()
    records, counts = build(args.source_dir)
    target = PUBLIC / "procedures.json"
    data = (json.dumps(records, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if args.check:
        require(target.read_bytes().replace(b"\r\n", b"\n") == data, "Public procedures need rebuilding")
    else:
        stream = tempfile.NamedTemporaryFile(dir=target.parent, delete=False)
        temporary = Path(stream.name)
        try:
            with stream:
                stream.write(data)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    print(json.dumps({"activities": len(records), "confirmed": counts["confirmed"],
                      "held": counts["held"], "pending": counts["pending"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
