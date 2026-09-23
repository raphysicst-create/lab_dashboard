"""Independently verify the 2026-09-23 high-school JSON/site application.

Reads the preserved 862-row snapshot, the 415-row high-school source and the
generated public JSON. It imports no production converter and writes only the
named validation report. A failing check exits nonzero and never repairs data.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMBINED_DIR = ROOT / "outputs/extraction/combined-20260922"
COMBINED = COMBINED_DIR / "science_experiment_supplies_combined.json"
SNAPSHOT = COMBINED_DIR / "decision_history/20260923-integrated-science"
HIGH_DIR = ROOT / "outputs/extraction/integrated-science-20260923"
HIGH = HIGH_DIR / "science_experiment_supplies_integrated_science.json"
PUBLIC = ROOT / "site/dist/data"
REPORT = ROOT / "output/validation/integrated-site-20260923/data-validation.json"
MIDDLE_ADDITIONS = {"grade_key", "school_level", "grade_label", "achievement_ids"}
PUBLIC_ACTIVITY_KEYS = {
    "id", "source_row", "achievement_id", "achievement_ids", "textbook_id",
    "grade", "unit", "unit_number", "achievement_raw", "publisher_raw", "page",
    "title", "materials_raw", "equipment", "supplies", "material_ids",
    "chemical_ids", "school_level", "grade_key", "grade_label", "unit_raw",
    "volume", "material_classification_pending",
}
PUBLIC_ACHIEVEMENT_KEYS = {
    "id", "unit", "unit_number", "sequence", "raw_text", "code", "grade",
    "grades", "school_level", "grade_key", "volume", "sort_order",
}
FORBIDDEN_PUBLIC_KEYS = {
    "source", "source_file", "source_books", "pdf_pages", "printed_pages",
    "standard_mapping", "standard_evidence", "activity_evidence", "title_quote",
    "supplies_quote", "standard_quote", "review_notes", "review_note", "rationale",
    "mapping_method", "candidate_codes", "verification_status", "title_bbox",
    "supplies_bbox", "evidence", "성취기준 연결", "준비물 분류", "판단출처",
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def name_key(value):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value))


def comma_items(raw):
    """Keep wrapped words and parenthesized commas inside a single raw item."""
    if raw is None:
        return []
    result, start, depth = [], 0, 0
    for index, char in enumerate(raw):
        if char in "(（[【{":
            depth += 1
        elif char in ")）]】}":
            depth = max(0, depth - 1)
        elif char in ",，" and depth == 0:
            result.append(raw[start:index].strip())
            start = index + 1
    result.append(raw[start:].strip())
    return [part for part in result if part]


def main():
    checks = []
    counts = {}

    def check(name, condition, detail=None):
        result = {"name": name, "passed": bool(condition)}
        if detail is not None:
            result["detail"] = detail
        checks.append(result)

    def finish():
        failures = [entry for entry in checks if not entry["passed"]]
        report = {
            "status": "failed" if failures else "passed",
            "checked_at_utc": datetime.now(timezone.utc).isoformat(),
            "scope": "스냅샷·고등 원자료·공개 JSON의 독립 데이터 검증. 브라우저 동작·실제 배포 및 교과서 의미 재판독은 별도 검증 범위이다.",
            "check_count": len(checks), "failed_check_count": len(failures),
            "counts": counts, "checks": checks,
            "written_files": [REPORT.relative_to(ROOT).as_posix()],
        }
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "checks": len(checks),
                          "failures": failures, "counts": counts,
                          "report": str(REPORT)}, ensure_ascii=False, indent=2))
        return 1 if failures else 0

    required = [COMBINED, HIGH, HIGH_DIR / "baseline.json", SNAPSHOT / "application.json",
                SNAPSHOT / "prior-validation.json", SNAPSHOT / COMBINED.name]
    for name in ["activities", "achievements", "materials", "chemicals", "chemical_guidelines", "textbooks"]:
        required.extend([PUBLIC / f"{name}.json", SNAPSHOT / f"public-{name}.json"])
    required.extend([PUBLIC / "sources.json", PUBLIC / "quantities.json"])
    missing = [str(p.relative_to(ROOT)) for p in required if not p.is_file()]
    check("required_files_exist", not missing, missing)
    if missing:
        return finish()

    old = read_json(SNAPSHOT / COMBINED.name)
    combined = read_json(COMBINED)
    high = read_json(HIGH)
    application = read_json(SNAPSHOT / "application.json")
    previous = read_json(SNAPSHOT / "prior-validation.json")
    baseline = read_json(HIGH_DIR / "baseline.json")
    public = {name: read_json(PUBLIC / f"{name}.json") for name in
              ["activities", "achievements", "materials", "chemicals", "chemical_guidelines", "textbooks", "sources", "quantities"]}
    before = {name: read_json(SNAPSHOT / f"public-{name}.json") for name in
              ["activities", "achievements", "materials", "chemicals", "chemical_guidelines", "textbooks"]}
    rows, old_rows, high_rows = combined["data"], old["data"], high["data"]
    middle_ids = [r["id"] for r in old_rows]
    high_ids = [r["id"] for r in high_rows]
    expected_ids = middle_ids + high_ids
    middle_id_set, high_id_set = set(middle_ids), set(high_ids)
    row_by_id = {r["id"]: r for r in rows}
    activity_by_id = {r["id"]: r for r in public["activities"]}
    achievement_by_id = {r["id"]: r for r in public["achievements"]}
    material_by_id = {r["id"]: r for r in public["materials"]}
    chemical_by_id = {r["id"]: r for r in public["chemicals"]}
    textbook_by_id = {r["id"]: r for r in public["textbooks"]}
    registry = {r["code"]: r for r in combined["achievement_standards"]}
    catalog_rows = high["metadata"]["achievement_standard_catalog"]
    catalog = {r["code"]: r for r in catalog_rows}
    public_high_standards = {r["code"]: r for r in public["achievements"] if r.get("code", "").startswith("10통과")}
    books = {r["book_id"]: r for r in high["metadata"]["source_books"]}

    counts.update(combined=len(rows), middle=len(old_rows), high=len(high_rows),
                  public_activities=len(public["activities"]), public_standards=len(public["achievements"]))
    check("record_counts_862_plus_415_equals_1277", len(old_rows) == 862 and len(high_rows) == 415
          and len(rows) == 1277 and combined["metadata"]["record_count"] == 1277)
    check("all_activity_ids_unique_and_exact_order", len(set(expected_ids)) == 1277
          and [r["id"] for r in rows] == expected_ids
          and [r["id"] for r in public["activities"]] == expected_ids)
    check("all_862_middle_combined_rows_exactly_unchanged", rows[:862] == old_rows)
    # The overall view intentionally gains the 415 new IDs; existing subviews
    # and the middle-school order within the overall view must stay exact.
    overall_before = old["views"]["기본자료"]
    overall_after = combined["views"].get("기본자료", {})
    check("existing_subviews_preserved_and_overall_view_extended_exactly",
          all(combined["views"].get(k) == v for k, v in old["views"].items() if k != "기본자료")
          and overall_after.get("record_count") == 1277
          and overall_after.get("record_ids") == expected_ids
          and all(overall_after.get(k) == v for k, v in overall_before.items()
                  if k not in {"record_count", "record_ids"}))
    check("middle_source_dataset_metadata_unchanged", combined["metadata"]["source_datasets"][:3]
          == old["metadata"]["source_datasets"])

    diffs = []
    for original in before["activities"]:
        current = activity_by_id.get(original["id"], {})
        changed = [key for key, value in original.items() if key not in current or current[key] != value]
        extras = sorted(set(current) - set(original) - MIDDLE_ADDITIONS)
        if changed or extras:
            diffs.append({"id": original["id"], "changed_or_missing_keys": changed, "unexpected_new_keys": extras})
        expected_links = [original["achievement_id"]] if original["achievement_id"] else []
        if current.get("achievement_ids") != expected_links:
            diffs.append({"id": original["id"], "error": "middle_achievement_ids_changed"})
        if (current.get("grade_key") != str(original["grade"])
                or current.get("grade_label") != f"중{original['grade']}"
                or current.get("school_level") != "중학교"):
            diffs.append({"id": original["id"], "error": "middle_grade_identity_changed"})
    check("middle_862_public_rows_preserve_every_old_field", len(before["activities"]) == 862 and not diffs, diffs)

    standard_diffs = []
    for original in before["achievements"]:
        current = achievement_by_id.get(original["id"], {})
        changed = [key for key, value in original.items() if key not in current or current[key] != value]
        if changed:
            standard_diffs.append({"id": original["id"], "changed_or_missing_keys": changed})
    check("middle_87_public_standards_keep_ids_and_all_old_fields", len(before["achievements"]) == 87 and not standard_diffs, standard_diffs)
    check("middle_registry_87_entries_exactly_preserved", len(old["achievement_standards"]) == 87
          and all(registry.get(r["code"]) == r for r in old["achievement_standards"]))
    expected_codes = {f"10통과{volume}-{unit:02d}-{sequence:02d}"
                      for volume, sizes in [(1, [4, 6, 6]), (2, [5, 6, 4])]
                      for unit, size in enumerate(sizes, 1) for sequence in range(1, size + 1)}
    check("catalog_31_high_and_public_118_standards_unique", len(catalog_rows) == len(catalog) == 31
          and len(public["achievements"]) == len(achievement_by_id) == 118
          and len(combined["achievement_standards"]) == len(registry) == 118
          and set(public_high_standards) == set(catalog) == expected_codes)

    catalog_errors = []
    for code, standard in catalog.items():
        stored = registry.get(code, {})
        exposed = public_high_standards.get(code, {})
        _, unit, sequence = code.split("-")
        volume = int(code[len("10통과")])
        expected_display = f"{int(unit)}-{int(sequence)}. {standard['text']}"
        if (stored.get("raw_text") != standard["text"] or stored.get("display_text") != expected_display
                or exposed.get("raw_text") != expected_display):
            catalog_errors.append({"code": code, "error": "standard_wording_or_display_changed"})
        if (stored.get("source") != standard["source"] or exposed.get("grade") != 1
                or exposed.get("grades") != [1] or exposed.get("school_level") != "고등학교"
                or exposed.get("grade_key") != "high-1" or exposed.get("volume") != volume
                or exposed.get("unit_number") != int(unit) or exposed.get("sequence") != int(sequence)
                or not exposed.get("unit", "").startswith(f"통합과학 {volume} · ")):
            catalog_errors.append({"code": code, "error": "catalog_identity_or_private_source_changed"})
    check("all_31_high_catalog_texts_and_identities_match", not catalog_errors, catalog_errors)

    high_errors, unresolved, multi = [], [], []
    links_count = 0
    for original in high_rows:
        rid = original["id"]
        current, exposed = row_by_id.get(rid, {}), activity_by_id.get(rid, {})
        preserved = [k for k, value in original.items() if k != "성취기준" and (k not in current or current[k] != value)]
        if preserved:
            high_errors.append({"id": rid, "changed_original_fields": preserved})
        for public_key, raw_key in [("title", "탐구활동"), ("materials_raw", "교구"),
                                    ("unit_raw", "단원명"), ("page", "쪽"),
                                    ("publisher_raw", "출판사"), ("source_row", "source_row")]:
            if public_key not in exposed or exposed[public_key] != original[raw_key]:
                high_errors.append({"id": rid, "error": f"raw_field_changed:{public_key}"})
        volume = books[original["source"]["book_id"]]["volume"]
        if (original.get("학교급") != "고등학교" or original.get("학년") != 1
                or original.get("학년표시") != "고1" or exposed.get("school_level") != "고등학교"
                or exposed.get("grade") != 1 or exposed.get("grade_key") != "high-1"
                or exposed.get("grade_label") != "고1" or exposed.get("volume") != volume
                or exposed.get("unit") != f"통합과학 {volume} · {original['단원명']}"):
            high_errors.append({"id": rid, "error": "high_grade_volume_or_unit_identity"})
        codes = original["성취기준코드"]
        expected_text = "\n".join(registry[c]["display_text"] for c in codes) if codes else None
        expected_link_ids = [public_high_standards[c]["id"] for c in codes]
        links_count += len(codes)
        if len(codes) > 1:
            multi.append(rid)
        if not codes:
            unresolved.append(rid)
        if (current.get("성취기준 원문") != original["성취기준"]
                or current.get("성취기준 코드") != (codes or None)
                or current.get("성취기준") != expected_text
                or exposed.get("achievement_raw") != expected_text
                or exposed.get("achievement_ids") != expected_link_ids
                or exposed.get("achievement_id") != (expected_link_ids[0] if expected_link_ids else None)):
            high_errors.append({"id": rid, "error": "codes_display_original_or_all_references_mismatch"})
        if original["성취기준내용"] != [{"code": c, "text": catalog[c]["text"]} for c in codes]:
            high_errors.append({"id": rid, "error": "source_catalog_wording_mismatch"})
        connection = current.get("성취기준 연결", {})
        source_mapping = original["source"]["standard_mapping"]
        if connection.get("status") != source_mapping["method"] or connection.get("evidence") != source_mapping:
            high_errors.append({"id": rid, "error": "private_mapping_evidence_not_preserved"})
        if (exposed.get("equipment") is not None or exposed.get("supplies") is not None
                or exposed.get("material_classification_pending") is not True):
            high_errors.append({"id": rid, "error": "unconfirmed_classification_not_preserved"})
    counts.update(high_unresolved=len(unresolved), high_multicode_activities=len(multi), high_code_links=links_count,
                  high_materials_null=sum(r["교구"] is None for r in high_rows))
    check("high_415_original_values_grade_mapping_and_all_code_links", not high_errors, high_errors)
    check("high_unresolved_4_remain_null_and_empty_references", len(unresolved) == 4, unresolved)
    check("high_10_book_record_counts_preserved", len(books) == 10 and dict(Counter(r["source"]["book_id"] for r in high_rows))
          == {bid: info["record_count"] for bid, info in books.items()})

    public_schema_errors = []
    for row in public["activities"]:
        extra = sorted(set(row) - PUBLIC_ACTIVITY_KEYS)
        if extra:
            public_schema_errors.append({"id": row.get("id"), "keys": extra})
    for row in public["achievements"]:
        extra = sorted(set(row) - PUBLIC_ACHIEVEMENT_KEYS)
        if extra:
            public_schema_errors.append({"id": row.get("id"), "keys": extra})
    leaks = []

    def scan(value, path):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in FORBIDDEN_PUBLIC_KEYS:
                    leaks.append(f"{path}.{key}")
                scan(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                scan(child, f"{path}[{index}]")
        elif isinstance(value, str) and ("textbook_wiki" in value or "outputs/extraction" in value or "C:/Users/" in value or "C:\\Users\\" in value):
            leaks.append(path)

    for name, document in public.items():
        scan(document, name)
    check("public_no_textbook_review_or_mapping_evidence_metadata", not leaks and not public_schema_errors,
          {"forbidden_keys_or_paths": leaks, "unexpected_record_keys": public_schema_errors})
    check("public_quantities_remain_empty", public["quantities"] == [])

    old_material_errors = []
    for original in before["materials"]:
        current = material_by_id.get(original["id"], {})
        for key, value in original.items():
            actual = current.get(key)
            if key == "activity_ids" and isinstance(actual, list):
                actual = [rid for rid in actual if rid in middle_id_set]
            elif key == "source_mentions" and isinstance(actual, list):
                actual = [r for r in actual if r.get("activity_id") in middle_id_set]
            if actual != value:
                old_material_errors.append({"material_id": original["id"], "changed_key": key})
    check("all_middle_material_chemical_links_and_mentions_preserved", not old_material_errors, old_material_errors)
    check("chemical_and_guideline_data_exactly_unchanged", public["chemicals"] == before["chemicals"]
          and public["chemical_guidelines"] == before["chemical_guidelines"])
    check("all_public_entity_ids_unique", all(len(public[name]) == len({r["id"] for r in public[name]})
          for name in ["activities", "achievements", "materials", "chemicals", "chemical_guidelines", "textbooks"]))
    check("existing_textbooks_unchanged", all(textbook_by_id.get(t["id"]) == t for t in before["textbooks"]))

    link_errors, high_mentions = [], []
    for material in public["materials"]:
        mid, cid = material["id"], material.get("chemical_id")
        if cid not in chemical_by_id:
            link_errors.append({"material_id": mid, "error": "missing_chemical"})
            continue
        chemical = chemical_by_id[cid]
        legal_names = {name_key(chemical["name"]), *(name_key(a) for a in chemical.get("aliases", []))}
        mentions = material["source_mentions"]
        if set(material["activity_ids"]) != {mention["activity_id"] for mention in mentions}:
            link_errors.append({"material_id": mid, "error": "mentions_and_activity_ids_mismatch"})
        for mention in mentions:
            rid = mention["activity_id"]
            source = row_by_id.get(rid, {})
            exposed = activity_by_id.get(rid, {})
            if (mention.get("raw_text") != source.get("교구")
                    or mention.get("source_row") != source.get("source_row")
                    or mid not in exposed.get("material_ids", []) or cid not in exposed.get("chemical_ids", [])):
                link_errors.append({"material_id": mid, "activity_id": rid, "error": "source_or_reverse_reference_mismatch"})
            if rid in high_id_set:
                high_mentions.append({"activity_id": rid, "chemical_id": cid})
                token = mention.get("matched_text", "")
                if (name_key(token) not in legal_names or token not in (source.get("교구") or "")
                        or name_key(token) not in {name_key(x) for x in comma_items(source.get("교구"))}
                        or mention.get("match_method") != "whole_item_source_name"):
                    link_errors.append({"material_id": mid, "activity_id": rid, "error": "high_match_not_literal_whole_item_or_source_alias"})
    for row in public["activities"]:
        rid = row["id"]
        expected_material_ids = {m["id"] for m in public["materials"] if rid in m["activity_ids"]}
        expected_chemical_ids = {material_by_id[mid]["chemical_id"] for mid in expected_material_ids}
        if (set(row.get("material_ids", [])) != expected_material_ids
                or set(row.get("chemical_ids", [])) != expected_chemical_ids
                or row.get("textbook_id") not in textbook_by_id
                or textbook_by_id[row["textbook_id"]]["publisher_raw"] != row["publisher_raw"]
                or any(aid not in achievement_by_id for aid in row.get("achievement_ids", []))):
            link_errors.append({"activity_id": rid, "error": "public_forward_reference_mismatch"})
    counts["high_literal_chemical_mentions"] = len(high_mentions)
    check("public_material_chemical_textbook_and_achievement_references", not link_errors, link_errors)

    hashes = {"combined": file_hash(COMBINED), "high_source": file_hash(HIGH),
              "before_combined": file_hash(SNAPSHOT / COMBINED.name)}
    check("combined_application_and_public_source_hashes", hashes["combined"] == application.get("output_sha256")
          == public["sources"].get("source_sha256") and public["sources"].get("record_count") == 1277
          and set(public["sources"]) == {"source_name", "source_sha256", "record_count"}, hashes)
    check("high_source_and_before_snapshot_hashes", hashes["high_source"] == application.get("input_sha256")
          and hashes["before_combined"] == application.get("before_sha256") == previous.get("output_sha256"))
    dataset_errors = []
    for entry in combined["metadata"]["source_datasets"]:
        path = ROOT / entry["input_file"]
        actual = file_hash(path) if path.is_file() else None
        if actual != entry["sha256"]:
            dataset_errors.append({"input_file": entry["input_file"], "expected": entry["sha256"], "actual": actual})
    check("all_four_source_dataset_hashes_match", len(combined["metadata"]["source_datasets"]) == 4 and not dataset_errors, dataset_errors)
    new_dataset = combined["metadata"]["source_datasets"][-1]
    check("new_dataset_complete_metadata_and_range", new_dataset.get("original_metadata") == high["metadata"]
          and new_dataset.get("record_count") == 415 and new_dataset.get("record_index_range_zero_based") == [862, 1276])
    protected = []
    for filename in ["science_experiment_supplies.json", "outputs/review/science_experiment_review.xlsx"]:
        path = ROOT / filename
        actual = file_hash(path) if path.is_file() else None
        protected.append({"file": filename, "expected_sha256": baseline[filename], "actual_sha256": actual,
                          "unchanged": actual == baseline[filename]})
    check("original_json_and_review_excel_preserved", all(item["unchanged"] for item in protected), protected)
    pdf_hashes = []
    for bid, book in books.items():
        path = Path(book["source_file"])
        actual = file_hash(path) if path.is_file() else None
        pdf_hashes.append({"book_id": bid, "expected_sha256": book["sha256"], "actual_sha256": actual,
                           "unchanged": actual == book["sha256"]})
    check("all_10_original_textbook_pdf_hashes_preserved", all(item["unchanged"] for item in pdf_hashes), pdf_hashes)
    return finish()


if __name__ == "__main__":
    sys.exit(main())
