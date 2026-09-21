"""Convert the supplied chemical tables without adding chemical knowledge.

Names, forms and rules stay scoped to the rows that actually name them.  Activity
links require a whole comma-delimited preparation item to match a source name;
solutions, concentrations, mixtures and apparatus are never inferred from a
substring.  This module deliberately does not consult an external database.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path


def identity(text: str) -> str:
    """Normalize equivalent characters/spacing; preserve state, spelling, form."""
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))


def stable_id(prefix: str, text: str) -> str:
    return prefix + "-" + hashlib.sha256(identity(text).encode("utf-8")).hexdigest()[:16]


def split_items(text: str) -> list[str]:
    """Split only outer commas, preserving mixtures/parenthetical source text."""
    result, start, depth = [], 0, 0
    for index, char in enumerate(text):
        if char in "([（":
            depth += 1
        elif char in ")]）":
            depth = max(0, depth - 1)
        elif char == "," and depth == 0:
            result.append(text[start:index].strip())
            start = index + 1
    result.append(text[start:].strip())
    return [item for item in result if item]


def trailing_parenthetical(text: str) -> tuple[str, str | None]:
    if not text.endswith(")"):
        return text, None
    depth = 0
    for index in range(len(text) - 1, -1, -1):
        if text[index] == ")":
            depth += 1
        elif text[index] == "(":
            depth -= 1
            if depth == 0:
                return text[:index].strip(), text[index + 1:-1]
    return text, None


def parse_source_item(item: str) -> list[dict]:
    item = re.sub(r"\s+등$", "", item.strip())
    # The source explicitly names both forms.  Do not make them synonyms: a rule
    # naming limewater alone must not be copied to calcium hydroxide.
    if " 또는 " in item:
        return [entry for piece in item.split(" 또는 ") for entry in parse_source_item(piece)]
    if item == "수산화 칼슘(석회수)":
        return [{"name": "수산화 칼슘", "aliases": [], "formula": None},
                {"name": "석회수", "aliases": [], "formula": None}]
    name, suffix = trailing_parenthetical(item)
    formula = None
    if suffix is not None and re.fullmatch(r"[A-Za-z0-9()]+", suffix) and suffix not in {"I", "II", "III", "IV"}:
        formula = suffix
        item = name
    name, suffix = trailing_parenthetical(item)
    if suffix and re.fullmatch(r"[가-힣 ]+", suffix):
        return [{"name": name, "aliases": [suffix], "formula": formula}]
    return [{"name": item, "aliases": [], "formula": formula}]


def markdown_tables(content: str) -> list[tuple[str, list[tuple[list[str], str]]]]:
    tables, rows, heading = [], [], ""
    for line in content.splitlines() + [""]:
        if line.startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            rows.append((cells, line))
            continue
        if rows:
            assert len(rows) >= 2 and all(re.fullmatch(r"[-: ]+", cell) for cell in rows[1][0])
            tables.append((heading, rows[2:]))
            rows = []
        if line.startswith("### "):
            heading = line[4:]
    return tables


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_chemical_data(root: Path, activities: list[dict]) -> dict:
    root = Path(root)
    catalogue: dict[str, dict] = {}
    alias_lookup: dict[str, str] = {}
    source_checks, coverage, exclusions, guidelines = [], [], [], []

    def ensure(entry: dict, reference: dict) -> dict:
        canonical = alias_lookup.get(identity(entry["name"]), identity(entry["name"]))
        if canonical not in catalogue:
            name = entry["name"]
            catalogue[canonical] = {
                "id": stable_id("CHEM", name), "name": name, "aliases": [],
                "formula": None, "classifications": [], "storage": [], "cabinets": [],
                "incompatibilities": [], "pictograms": None, "disposal": None,
            }
        record = catalogue[canonical]
        for alias in entry["aliases"]:
            normalized = identity(alias)
            assert normalized not in alias_lookup or alias_lookup[normalized] == canonical, f"Ambiguous source alias: {alias}"
            assert normalized not in catalogue or normalized == canonical, f"Alias already has a separate record: {alias}"
            alias_lookup[normalized] = canonical
            if alias not in record["aliases"]:
                record["aliases"].append(alias)
        if entry["formula"] is not None:
            assert record["formula"] in (None, entry["formula"]), f"Conflicting source formula: {record['name']}"
            record["formula"] = entry["formula"]
        # Every catalogue identity and formula has a directly traceable source.
        if "source_refs" not in record:
            record["source_refs"] = []
        if reference not in record["source_refs"]:
            record["source_refs"].append(reference)
        return record

    def add(names: str, field: str, details: dict, reference: dict) -> None:
        count = 0
        for raw in split_items(names):
            for entry in parse_source_item(raw):
                # Both supplied cabinet tables put this explicitly named
                # solution in a category labelled solid.  Retain its identity,
                # but hold the contradictory cabinet assertion for review.
                if field == "cabinets" and entry["name"] == "페놀프탈레인 용액":
                    ensure(entry, {**reference, "raw_text": raw})
                    exclusions.append({"chemical_name": entry["name"], "field": field,
                        "excluded_value": details, "source_ref": reference, "status": "미확인",
                        "reason": "원자료가 '페놀프탈레인 용액'을 '고체 약품' 분류에 함께 기재하여 보관장 연결을 보류함."})
                    continue
                record = ensure(entry, reference)
                row = {**details, "source_ref": reference}
                if row not in record[field]:
                    record[field].append(row)
                count += 1
        coverage.append({"field": field, "named_entries": count, "source_ref": reference})

    for basename in ("약품규정1", "약품규정2"):
        json_path = root / "output" / "parsed" / f"{basename}_파싱.json"
        md_path = root / "output" / "parsed" / f"{basename}_파싱.md"
        document = json.loads(json_path.read_text(encoding="utf-8-sig"))
        markdown = md_path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        for section in document["sections"]:
            content = section["content_markdown"].replace("\r\n", "\n")
            assert content in markdown, f"JSON/MD mismatch: {basename}: {section['heading']}"
            print_page = int(re.search(r"인쇄면 (\d+)쪽", section["heading"])[1])
            def ref(raw: str) -> dict:
                assert raw in content
                return {"file": document["source_file"], "print_page": print_page, "raw_text": raw}
            source_checks.append({"file": str(json_path.relative_to(root)), "markdown_file": str(md_path.relative_to(root)),
                                  "print_page": print_page, "json_matches_markdown": True})
            guideline_content = None
            guideline_title = section["heading"].split(" - ", 1)[1]
            if print_page == 16:
                guideline_content = content.split("### 물질안전보건자료(MSDS)에 대한 정보 검색", 1)[0].strip()
            elif print_page == 17:
                guideline_content = content.split("### 약품의 일반적인 분류", 1)[0].strip()
                guideline_title = "2.1. 화학 약품의 분류 및 보관"
            elif print_page == 21:
                guideline_content = content
            elif print_page == 22:
                guideline_content = content.split("이 페이지에는", 1)[0].strip()
                guideline_title = "가연성 물질 전용 보관장"
            elif print_page == 23:
                guideline_content = content.split("### 화학 약품의 보관장에 따른 약품 분류(예시)", 1)[0].strip()
                guideline_title = "실험실용 냉장고"
            elif print_page == 25:
                guideline_content = content
            if guideline_content:
                guidelines.append({"id": stable_id("GUIDE", f"{document['source_file']}:{print_page}:{guideline_title}"),
                                   "title": guideline_title, "content_markdown": guideline_content,
                                   "source_ref": ref(guideline_content)})
            tables = markdown_tables(content)
            if print_page == 6:
                for heading, rows in tables:
                    for cells, raw in rows:
                        category, names = cells
                        add(names, "cabinets", {"name": heading, "category": category, "qualifier": None}, ref(raw))
            elif print_page == 7:
                heading = ""
                category = ""
                qualifier = next(line[2:] for line in content.splitlines() if line.startswith("> "))
                for line in content.splitlines():
                    if line.startswith("### "):
                        heading = line[4:]
                    elif line.endswith(":"):
                        category = line[:-1]
                    elif line.startswith("- "):
                        add(line[2:], "cabinets", {"name": heading, "category": category,
                            "qualifier": qualifier if heading == "가연성 물질 전용 보관장" else None}, ref(line))
            elif print_page == 17:
                for _, rows in tables:
                    for cells, raw in rows:
                        group, label, names = cells
                        add(names, "classifications", {"group": group, "label": label}, ref(raw))
            elif print_page == 18:
                for heading, rows in tables:
                    for cells, raw in rows:
                        if heading == "위험물 분류 예시":
                            label, names = cells
                            add(names, "classifications", {"group": heading, "label": label}, ref(raw))
                        elif heading == "분리 보관이 필요한 화학 약품":
                            names, incompatible = cells
                            add(names, "incompatibilities", {"materials_raw": incompatible}, ref(raw))
                        else:
                            raise AssertionError(f"Unexpected table: {heading}")
            elif print_page == 20:
                for _, rows in tables:
                    for cells, raw in rows:
                        prop, instruction, names = cells
                        add(names, "storage", {"property": prop, "instruction": instruction}, ref(raw))
            elif print_page == 23:
                qualifier = next(line[2:] for line in content.splitlines() if line.startswith("> "))
                for _, rows in tables:
                    for cells, raw in rows:
                        cabinet, category, names = cells
                        add(names, "cabinets", {"name": cabinet, "category": category,
                            "qualifier": qualifier if cabinet == "가연성 물질 전용 보관장" else None}, ref(raw))

    chemicals = sorted(catalogue.values(), key=lambda row: row["name"])
    name_index = {}
    for chemical in chemicals:
        for name in [chemical["name"], *chemical["aliases"]]:
            normalized = identity(name)
            assert normalized not in name_index or name_index[normalized]["id"] == chemical["id"]
            name_index[normalized] = chemical
    linked_activities, materials_by_chemical, unresolved, lexical_review = [], {}, [], []
    for original in activities:
        activity = {**original, "material_ids": [], "chemical_ids": []}
        raw = original.get("materials_raw")
        if raw:
            for item in split_items(raw):
                chemical = name_index.get(identity(item))
                if chemical:
                    chemical_id = chemical["id"]
                    material = materials_by_chemical.setdefault(chemical_id, {
                        "id": stable_id("MAT", chemical["name"]), "name": chemical["name"],
                        "chemical_id": chemical_id, "activity_ids": [], "source_mentions": [],
                    })
                    if activity["id"] not in material["activity_ids"]:
                        material["activity_ids"].append(activity["id"])
                    mention = {"activity_id": activity["id"], "source_row": activity["source_row"],
                               "raw_text": raw, "matched_text": item, "match_method": "whole_item_source_name"}
                    if mention not in material["source_mentions"]:
                        material["source_mentions"].append(mention)
                    if chemical_id not in activity["chemical_ids"]:
                        activity["chemical_ids"].append(chemical_id)
                        activity["material_ids"].append(material["id"])
                else:
                    unmatched = {"activity_id": activity["id"], "source_row": activity["source_row"], "item_raw": item}
                    unresolved.append(unmatched)
                    # Text overlap is a private review aid, never a public identity
                    # link or an assertion that an item is itself a chemical.
                    candidates = sorted({entry["id"] for name, entry in name_index.items()
                                         if len(name) >= 2 and name in identity(item)})
                    if candidates:
                        lexical_review.append({**unmatched, "text_overlap_chemical_ids": candidates,
                            "status": "미확인", "reason": "전체 항목이 자료의 약품명과 일치하지 않아 연결하지 않음. 문자열 포함은 약품 동일성의 근거가 아님."})
        linked_activities.append(activity)
    materials = sorted(materials_by_chemical.values(), key=lambda row: row["name"])
    report = {
        "policy": {"name_matching": "whole materials item; Unicode NFKC, whitespace differences and explicitly written aliases only",
                   "no_inferred_forms_or_concentrations": True, "no_reverse_incompatibility_rules": True,
                   "ghs_assignment": "미확인", "per_chemical_disposal_assignment": "미확인"},
        "counts": {"chemicals": len(chemicals), "materials_with_source_name_links": len(materials),
                   "activities": len(activities),
                   "activities_with_links": sum(bool(row["chemical_ids"]) for row in linked_activities),
                   "links": sum(len(row["chemical_ids"]) for row in linked_activities),
                   "unmatched_preparation_items": len(unresolved),
                   "unmatched_items_with_name_text_overlap": len(lexical_review),
                   "covered_source_rows": len(coverage), "excluded_assertions": len(exclusions),
                   "shared_management_guidelines": len(guidelines)},
        "source_checks": source_checks, "covered_rows": coverage,
        "excluded_assertions": exclusions,
        "unmatched_preparation_items_note": "기구와 일반 준비물을 포함한 미연결 원문 항목이며, 모두 약품이라는 의미가 아님.",
        "unmatched_preparation_items": unresolved, "name_overlap_review": lexical_review,
        "field_counts": {field: sum(len(row[field]) for row in chemicals)
                         for field in ("classifications", "storage", "cabinets", "incompatibilities")},
    }
    return {"chemicals": chemicals, "materials": materials, "activities": linked_activities,
            "guidelines": guidelines, "report": report}


def self_check(result: dict) -> None:
    by_name = {record["name"]: record for record in result["chemicals"]}
    assert all(row["pictograms"] is None and row["disposal"] is None for row in by_name.values())
    assert by_name["에탄올"]["storage"] and by_name["수산화 나트륨"]["storage"]
    assert not by_name["염화 나트륨"]["storage"]
    assert not by_name["수산화 칼슘"]["storage"]
    assert by_name["석회수"]["storage"]
    assert by_name["아이오딘"]["id"] != by_name["아이오딘 용액"]["id"]
    assert not any("갈색 병" in row["instruction"] for row in by_name["아이오딘"]["storage"])
    assert not by_name["암모니아수"]["incompatibilities"]
    assert by_name["암모니아"]["incompatibilities"]
    assert not by_name["나트륨"]["incompatibilities"]  # Group row has no inferred member rules.
    assert "명반" in by_name["백반"]["aliases"]
    assert "구연산" in by_name["시트르산"]["aliases"]
    assert not by_name["페놀프탈레인 용액"]["cabinets"]
    assert {row["source_ref"]["print_page"] for row in result["guidelines"]} == {16, 17, 21, 22, 23, 25}
    assert all(row["content_markdown"] == row["source_ref"]["raw_text"] for row in result["guidelines"])
    for material in result["materials"]:
        chemical = next(row for row in by_name.values() if row["id"] == material["chemical_id"])
        exact_names = {identity(name) for name in [chemical["name"], *chemical["aliases"]]}
        for mention in material["source_mentions"]:
            assert mention["matched_text"] in mention["raw_text"]
            assert identity(mention["matched_text"]) in exact_names


def check_link_boundaries(root: Path) -> None:
    fixtures = [
        ("염화 나트륨", {"염화 나트륨"}),
        ("질산 칼륨", {"질산 칼륨"}),
        ("에탄올", {"에탄올"}),
        ("수산화나트륨", {"수산화 나트륨"}),
        ("구연산", {"시트르산"}),
        ("아이오딘-아이오딘화 칼륨 용액", set()),
        ("5% 수산화 나트륨 수용액", set()),
        ("에탄올 버너", set()),
        ("묽은 염산", set()),
        ("푸른색 리트머스 종이", set()),
        ("물과 에탄올 혼합물", set()),
        ("혼합물(에탄올, 아이오딘)", set()),
        ("마그네슘 리본", {"마그네슘 리본"}),
        ("아이오딘 용액", {"아이오딘 용액"}),
        ("황산 구리(Ⅱ)", {"황산 구리(II)"}),
        ("황산 구리(Ⅱ) 수용액", set()),
    ]
    data = build_chemical_data(root, [
        {"id": f"boundary_fixture_{i}", "source_row": None, "materials_raw": raw}
        for i, (raw, _) in enumerate(fixtures)
    ])
    names = {chemical["id"]: chemical["name"] for chemical in data["chemicals"]}
    for activity, (raw, expected) in zip(data["activities"], fixtures):
        assert {names[cid] for cid in activity["chemical_ids"]} == expected, raw


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    root = Path(__file__).resolve().parents[1]
    activities = json.loads((root / "site/dist/data/activities.json").read_text(encoding="utf-8"))
    result = build_chemical_data(root, activities)
    self_check(result)
    check_link_boundaries(root)
    destination = root / "output/validation/chemicals"
    write_json(destination / "chemical-conversion-report.json", result["report"])
    write_json(destination / "chemical-catalogue-review.json", result["chemicals"])
    print(json.dumps(result["report"]["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
