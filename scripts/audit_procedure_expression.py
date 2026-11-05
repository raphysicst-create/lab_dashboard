"""Read-only lexical comparison with local textbooks; matches require human review.

This is an editorial aid, not a copyright clearance or an infringement detector.
Detailed matching text is written only to the ignored scratchpad directory.
"""
import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def normalize(value):
    return re.sub(r"[\W_]", "", unicodedata.normalize("NFKC", value), flags=re.UNICODE)


def longest_match(text, source, minimum):
    low, high, found = minimum, len(text), ""
    while low <= high:
        length = (low + high) // 2
        candidate = next((text[i:i + length] for i in range(len(text) - length + 1)
                          if text[i:i + length] in source), None)
        if candidate is None:
            high = length - 1
        else:
            found = candidate
            low = length + 1
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--review-dir", type=Path, default=ROOT / "outputs/review/procedures")
    parser.add_argument("--minimum", type=int, default=25)
    parser.add_argument("--label", default="current")
    args = parser.parse_args()
    import fitz
    scratch = ROOT / "scratchpad/independent-release"
    scratch.mkdir(parents=True, exist_ok=True)
    cache_path = scratch / "pdf-text-cache.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    books, matches, exact, counts = {}, [], [], Counter()
    for section in ("legacy", "middle", "high"):
        path = args.review_dir / (section + ".json")
        records = json.loads(path.read_text(encoding="utf-8-sig"))
        for row in records:
            counts["activities"] += 1
            if row["groups"] is None:
                counts["held"] += 1
                continue
            pages = []
            filename = row["pdf"]
            for number in row["pdf_pages"]:
                key = filename + ":" + str(number)
                if key not in cache:
                    if filename not in books:
                        books[filename] = fitz.open(args.source_dir / filename)
                    cache[key] = normalize(books[filename][number - 1].get_text())
                pages.append((number, cache[key]))
            for gi, group in enumerate(row["groups"]):
                for si, step in enumerate(group["steps"]):
                    counts["steps"] += 1
                    normal = normalize(step)
                    base = {"section": section, "id": row["id"], "group": gi,
                            "step": si, "text": step, "pdf": filename}
                    exact_page = next((page for page, text in pages if normal in text), None)
                    if exact_page is not None:
                        exact.append({**base, "page": exact_page, "length": len(normal)})
                    best, page_number = "", None
                    for page, text in pages:
                        match = longest_match(normal, text, max(args.minimum, len(best) + 1))
                        if len(match) > len(best):
                            best, page_number = match, page
                    if best:
                        matches.append({**base, "page": page_number, "match": best,
                                        "length": len(best), "fraction": round(len(best) / len(normal), 3)})
        print(section + " complete", flush=True)
    cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    report = {"counts": dict(counts), "exact_steps": exact,
              "long_matches": sorted(matches, key=lambda value: -value["length"]),
              "interpretation": "Lexical matches are review candidates, not legal findings. Non-matches do not prove originality."}
    output = scratch / (args.label + "-expression-audit.json")
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"counts": dict(counts), "exact_steps": len(exact),
                      "long_matches": len(matches), "report": str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
