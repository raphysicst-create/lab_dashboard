"""Compare scientific quantities before and after an editorial revision.

The baseline must be the local, unpublished archive. Differences are review
candidates: a figure may replace a sentence, and a documented source correction
may deliberately change an earlier error.
"""
import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AMOUNT = re.compile(r"\d+(?:\.\d+)?(?:\s*[~∼～–-]\s*\d+(?:\.\d+)?)?\s*(?:mL|mL|kg|mg|cm|mm|km|m/s|℃|°C|°|%|L|g|분|초|시간|방울|마리|회)")
SAFETY = ("보안경", "장갑", "실험복", "화상", "화재", "흐르는 물", "입에", "먹지", "마시지", "직접 맡", "교사", "폐액", "밀폐")


def text(row):
    return " ".join(step for group in row["groups"] or [] for step in group["steps"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    args = parser.parse_args()
    changes, quantities, safety, held = [], [], [], []
    for section in ("legacy", "middle", "high"):
        old = {row["id"]: row for row in json.loads((args.baseline / (section + ".json")).read_text(encoding="utf-8-sig"))}
        new = json.loads((ROOT / "outputs/review/procedures" / (section + ".json")).read_text(encoding="utf-8-sig"))
        assert set(old) == {row["id"] for row in new}
        for row in new:
            previous = old[row["id"]]
            before, after = text(previous), text(row)
            if before != after:
                changes.append(row["id"])
            if previous["groups"] and row["groups"] is None:
                held.append({"id": row["id"], "note": row["note"]})
                continue
            graphic_text = []
            for group in row["groups"] or []:
                for figure in group.get("figures", []):
                    if figure["file"].endswith(".svg"):
                        svg = ET.parse(ROOT / "site/dist/procedure-figures" / figure["file"])
                        graphic_text.extend(" ".join(node.itertext()) for node in svg.iter() if node.tag.endswith("}text"))
            all_after = after + " " + " ".join(graphic_text)
            tokens = lambda value: {re.sub(r"\s", "", item) for item in AMOUNT.findall(value)}
            removed, added = tokens(before) - tokens(all_after), tokens(all_after) - tokens(before)
            if removed or added:
                quantities.append({"id": row["id"], "removed": sorted(removed), "added": sorted(added), "before": before, "after": after, "note": row["note"]})
            lost = [word for word in SAFETY if word in before and word not in all_after]
            if lost:
                safety.append({"id": row["id"], "terms": lost, "before": before, "after": after})
    report = {"changed_activities": changes, "quantity_candidates": quantities,
              "safety_candidates": safety, "newly_held": held}
    target = ROOT / "scratchpad/independent-release/fact-diff.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"changed_activities": len(changes), "quantity_candidates": len(quantities), "safety_candidates": len(safety), "newly_held": [row["id"] for row in held]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
