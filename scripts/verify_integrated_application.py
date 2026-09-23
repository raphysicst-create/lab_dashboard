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
UNIT_HISTORY = COMBINED_DIR / "decision_history/20260923-units"
UNIT_REPORT = ROOT / "output/validation/unit-normalization-20260923/data-validation.json"
CLASSIFICATION_HISTORY = COMBINED_DIR / "decision_history/20260923-high-classification"
CLASSIFICATION_REPORT = ROOT / "output/validation/high-classification-20260923/data-validation.json"
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
    "supplies_bbox", "evidence", "성취기준 연결", "준비물 분류", "준비물 분류 비항목", "판단출처",
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


def verify_units(live, activities, check, counts, live_hash=None):
    """Check the new transformation independently, then return its input views.

    No activity achievement link is used to determine its chapter. The old
    middle registry supplies chapter vocabulary; high-school chapter vocabulary
    is fixed by volume. Roman/Arabic prefixes and subchapters are only syntax.
    """
    required = [UNIT_HISTORY / name for name in [COMBINED.name, "public-activities.json",
                "unit_catalog.json", "application.json"]]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.is_file()]
    check("unit_history_required_files_exist", not missing, missing)
    if missing:
        return None
    prior = read_json(UNIT_HISTORY / COMBINED.name)
    prior_public = read_json(UNIT_HISTORY / "public-activities.json")
    catalog = read_json(UNIT_HISTORY / "unit_catalog.json")
    application = read_json(UNIT_HISTORY / "application.json")
    meta = live["metadata"]["unit_normalization"]
    prior_hash = file_hash(UNIT_HISTORY / COMBINED.name)
    check("unit_snapshot_and_output_hash_chain", prior_hash == meta.get("snapshot_sha256")
          == application.get("before_sha256")
          and (live_hash or file_hash(COMBINED)) == application.get("output_sha256")
          and meta.get("snapshot") == (UNIT_HISTORY / COMBINED.name).relative_to(ROOT).as_posix())

    middle = {}
    for standard in prior["achievement_standards"]:
        match = re.fullmatch(r"9과(\d{2})-\d{2}", standard["code"])
        if match:
            number = int(match[1])
            middle[number] = standard["chapter"]
    high = {1: ["과학의 기초", "물질과 규칙성", "시스템과 상호작용"],
            2: ["변화와 다양성", "환경과 에너지", "과학과 미래 사회"]}
    expected = [{"id": f"middle-{n:02d}", "school_level": "중학교", "volume": None,
                 "number": n, "label": f"{n}. {middle[n]}"} for n in sorted(middle)]
    expected += [{"id": f"high-{v}-{n:02d}", "school_level": "고등학교", "volume": v,
                  "number": n, "label": f"통합과학 {v} · {n}. {title}"}
                 for v, titles in high.items() for n, title in enumerate(titles, 1)]
    expected.append({"id": "high-2-appendix", "school_level": "고등학교", "volume": 2,
                     "number": None, "label": "통합과학 2 · 부록"})
    check("unit_catalog_23_middle_6_high_and_one_appendix", set(middle) == set(range(1, 24))
          and catalog == expected and live.get("units") == expected and meta.get("unit_count") == 30)

    def chapter_key(raw):
        major = re.split(r"[>/]", unicodedata.normalize("NFKC", raw), maxsplit=1)[0]
        major = re.sub(r"^\s*(?:\d+|[IVX]+)\s*[.．]\s*", "", major)
        return re.sub(r"[\s·⋅ㆍ]", "", major)

    by_title = {(u["school_level"], u["volume"], chapter_key(
        u["label"].split(" · ", 1)[-1])): u for u in expected}
    old_public = {a["id"]: a for a in prior_public}
    public = {a["id"]: a for a in activities}
    current = {r["id"]: r for r in live["data"]}
    check("unit_all_1277_ids_and_order_preserved", len(prior["data"]) == len(live["data"]) == 1277
          and [r["id"] for r in prior["data"]] == [r["id"] for r in live["data"]]
          == [r["id"] for r in activities] == [r["id"] for r in prior_public]
          and len(current) == len(public) == 1277)
    raw_errors, field_errors, mapping_errors = [], [], []
    used = Counter()
    for original in prior["data"]:
        rid = original["id"]
        row, exposed, old_exposed = current.get(rid, {}), public.get(rid, {}), old_public.get(rid, {})
        raw = original["단원명"]
        if row.get("단원명 원문") != raw or exposed.get("unit_raw") != raw:
            raw_errors.append(rid)
        row_without_units = {k: v for k, v in row.items() if k not in {"단원명", "단원명 원문", "단원 번호", "단원 ID"}}
        original_without_units = {k: v for k, v in original.items() if k != "단원명"}
        exposed_without_units = {k: v for k, v in exposed.items() if k not in {"unit", "unit_raw", "unit_number"}}
        old_exposed_without_units = {k: v for k, v in old_exposed.items() if k not in {"unit", "unit_raw", "unit_number"}}
        if row_without_units != original_without_units or exposed_without_units != old_exposed_without_units:
            field_errors.append(rid)
        unit = by_title.get((old_exposed.get("school_level"), old_exposed.get("volume"), chapter_key(raw)))
        if unit is None or (row.get("단원명"), row.get("단원 번호"), row.get("단원 ID"),
                            exposed.get("unit"), exposed.get("unit_number")) != (
                            unit["label"], unit["number"], unit["id"], unit["label"], unit["number"]):
            mapping_errors.append({"id": rid, "raw": raw, "expected": unit, "actual": row.get("단원명")})
        else:
            used[unit["id"]] += 1
    check("unit_all_original_chapter_labels_preserved_verbatim", not raw_errors, raw_errors)
    check("unit_all_nonunit_combined_and_public_fields_exactly_preserved", not field_errors, field_errors)
    check("unit_assignments_match_actual_raw_chapter_not_achievement", not mapping_errors, mapping_errors)
    check("unit_duplicates_collapsed_to_29_main_and_one_appendix", len(used) == 30
          and used["high-2-appendix"] == 1 and dict(used) == application.get("unit_counts")
          and len({r["unit"] for r in activities}) == 30
          and sum(r.get("unit_number") is None for r in activities) == 1)
    prior_other = {k: v for k, v in prior.items() if k not in {"metadata", "data"}}
    live_other = {k: v for k, v in live.items() if k not in {"metadata", "data", "units"}}
    check("unit_nonrow_content_and_prior_metadata_preserved", prior_other == live_other
          and {k: v for k, v in live["metadata"].items() if k != "unit_normalization"} == prior["metadata"])
    counts.update(canonical_main_units=29, canonical_total_units=len(used),
                  unit_label_changes=sum(r["단원명"] != current[r["id"]]["단원명"] for r in prior["data"]),
                  unit_assignment_basis="원문 대단원명 및 기존 학교급·권수; 활동 성취기준 미사용")
    return prior, prior_public, prior_hash


def verify_high_classification(live, activities, check, counts, live_hash):
    """Validate classification on current rows before unwinding older stages."""
    history = CLASSIFICATION_HISTORY
    review = HIGH_DIR / "preparation_classification"
    manifest_names = ["miraen_jihaksa", "chunjae", "visang_donga"]
    required = [history / COMBINED.name, history / "public-activities.json",
                history / "application.json", COMBINED_DIR / "preparation_item_catalogue.json"]
    required += [review / f"{name}.json" for name in manifest_names]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    check("classification_required_history_and_manifests_exist", not missing, missing)
    if missing:
        return None
    prior = read_json(history / COMBINED.name)
    prior_public = read_json(history / "public-activities.json")
    application = read_json(history / "application.json")
    meta = live["metadata"]["high_preparation_classification"]
    prior_hash = file_hash(history / COMBINED.name)
    check("classification_stage_hash_chain", prior_hash == meta.get("snapshot_sha256")
          == application.get("before_sha256") and live_hash == application.get("output_sha256")
          and meta.get("snapshot") == (history / COMBINED.name).relative_to(ROOT).as_posix()
          and application.get("status") == "passed")
    manifests = [row for name in manifest_names for row in read_json(review / f"{name}.json")["records"]]
    manifest_by_id = {row["record_id"]: row for row in manifests}
    check("classification_review_manifest_hashes", application.get("manifest_sha256") == {
        name: file_hash(review / f"{name}.json") for name in manifest_names})
    current = {row["id"]: row for row in live["data"]}
    public = {row["id"]: row for row in activities}
    old_public = {row["id"]: row for row in prior_public}
    high_ids = {row["id"] for row in prior["data"] if row.get("학교급") == "고등학교"}
    check("classification_ids_order_and_exact_414_high_scope", len(prior["data"]) == len(live["data"]) == 1276
          and len(current) == len(public) == 1276 and len(high_ids) == len(manifests) == len(manifest_by_id) == 414
          and set(manifest_by_id) == high_ids
          and [row["id"] for row in prior["data"]] == [row["id"] for row in live["data"]]
          == [row["id"] for row in activities] == [row["id"] for row in prior_public])
    categories = ["실험 기자재", "실험 준비물"]
    allowed_fields = set(categories + ["분류 보류", "준비물 분류", "준비물 표시 방식", "준비물 분류 비항목"])
    allowed_public = {"equipment", "supplies", "material_classification_pending"}
    field_errors, span_errors, partition_errors, public_errors, catalogue_errors = [], [], [], [], []
    totals, unique = Counter(), {}
    null_count, text_count, nonitem_count = 0, 0, 0
    old_catalogue = {name_key(text): item for item in read_json(COMBINED_DIR / "preparation_item_catalogue.json")["items"]
                     for text in item.get("raw_variants", [item["representative_text"]])}
    for original in prior["data"]:
        rid = original["id"]
        row, exposed, old_exposed = current.get(rid, {}), public.get(rid, {}), old_public.get(rid, {})
        if rid not in high_ids:
            if row != original or exposed != old_exposed:
                field_errors.append({"id": rid, "error": "middle_row_changed"})
            continue
        if ({key: value for key, value in row.items() if key not in allowed_fields}
                != {key: value for key, value in original.items() if key not in allowed_fields}
                or {key: value for key, value in exposed.items() if key not in allowed_public}
                != {key: value for key, value in old_exposed.items() if key not in allowed_public}):
            field_errors.append({"id": rid, "error": "nonclassification_field_changed"})
        if row.get("준비물 표시 방식") != "분류" or exposed.get("material_classification_pending") is not False:
            public_errors.append({"id": rid, "error": "display_mode_or_pending_flag"})
        raw = original["교구"]
        manifest = manifest_by_id.get(rid, {})
        if raw is None:
            null_count += 1
            if (manifest.get("items", "missing") is not None or manifest.get("non_items")
                    or any(row.get(key, "missing") is not None for key in categories + ["분류 보류", "준비물 분류"])
                    or row.get("준비물 분류 비항목") or exposed.get("equipment", "missing") is not None
                    or exposed.get("supplies", "missing") is not None):
                partition_errors.append({"id": rid, "error": "null_source_was_classified"})
            continue
        text_count += 1
        items = row.get("준비물 분류")
        nonitems = row.get("준비물 분류 비항목", [])
        if not isinstance(items, list) or not items or not isinstance(nonitems, list):
            partition_errors.append({"id": rid, "error": "missing_item_array"})
            continue
        used, expected_manifest = set(), []
        parts = [{"raw": item.get("원문"), "span": item.get("원문_범위")} for item in items] + nonitems
        for part in parts:
            span = part.get("span")
            valid = (isinstance(span, list) and len(span) == 2 and all(type(n) is int for n in span)
                     and 0 <= span[0] < span[1] <= len(raw))
            if not valid:
                span_errors.append({"id": rid, "error": "invalid_span", "span": span})
                continue
            start, end = span
            if part.get("raw") != raw[start:end] or used.intersection(range(start, end)):
                span_errors.append({"id": rid, "error": "changed_raw_or_overlapping_span", "span": span})
            used.update(range(start, end))
        if any(not char.isspace() and char not in ",，□☐•" for index, char in enumerate(raw) if index not in used):
            span_errors.append({"id": rid, "error": "uncovered_nonseparator_text"})
        for item in items:
            category, text = item.get("분류"), item.get("원문")
            if category not in categories or not isinstance(text, str):
                partition_errors.append({"id": rid, "error": "invalid_or_pending_category"})
                continue
            key = name_key(text)
            iid = "ITEM-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
            if item.get("item_id") != iid or (key in unique and unique[key] != category):
                catalogue_errors.append({"id": rid, "raw": text, "error": "item_id_or_category_inconsistent"})
            old_item = old_catalogue.get(key)
            if old_item and old_item["category"] != category:
                catalogue_errors.append({"id": rid, "raw": text, "error": "existing_catalogue_decision_changed"})
            unique[key] = category
            totals[category] += 1
            expected_manifest.append({"raw": text, "span": item.get("원문_범위"), "category": category,
                                      "reason": item.get("근거"), "decision_source": item.get("판단출처")})
        if (expected_manifest != manifest.get("items") or nonitems != manifest.get("non_items", [])
                or any(not entry.get("reason") for entry in nonitems)):
            partition_errors.append({"id": rid, "error": "review_manifest_or_nonitem_evidence_mismatch"})
        nonitem_count += len(nonitems)
        if row.get("분류 보류") != [] or any(row.get(category) != [i["원문"] for i in items if i.get("분류") == category] for category in categories):
            partition_errors.append({"id": rid, "error": "category_partition_mismatch"})
        if exposed.get("equipment") != row.get("실험 기자재") or exposed.get("supplies") != row.get("실험 준비물"):
            public_errors.append({"id": rid, "error": "public_classification_not_exact"})
    check("classification_middle_862_and_all_nonclassification_fields_unchanged", not field_errors, field_errors)
    check("classification_exact_disjoint_spans_cover_all_nonseparator_text", not span_errors, span_errors)
    check("classification_partition_nulls_and_review_manifest_match", not partition_errors, partition_errors)
    check("classification_public_equipment_supplies_and_flags_match", not public_errors, public_errors)
    check("classification_existing_catalogue_and_item_id_consistency", not catalogue_errors, catalogue_errors)
    previous_metadata = prior["metadata"]
    current_metadata = {key: value for key, value in live["metadata"].items() if key != "high_preparation_classification"}
    current_metadata["preparation_classification"] = dict(current_metadata.get("preparation_classification", {}))
    current_metadata["preparation_classification"]["scope"] = previous_metadata["preparation_classification"].get("scope")
    check("classification_only_authorized_metadata_changed", current_metadata == previous_metadata
          and {key: value for key, value in live.items() if key not in {"data", "metadata"}}
          == {key: value for key, value in prior.items() if key not in {"data", "metadata"}})
    check("classification_statistics_match_all_414_records", text_count == 238 and null_count == 176
          and meta.get("record_count") == application.get("classified_high") == 414
          and meta.get("with_preparation_text") == application.get("with_preparation_text") == text_count
          and meta.get("without_preparation_text") == application.get("without_preparation_text") == null_count
          and meta.get("item_occurrences") == application.get("item_occurrences") == dict(totals)
          and meta.get("unique_item_count") == application.get("unique_items") == len(unique))
    counts.update(classified_high_records=414, classified_high_with_text=text_count,
                  classified_high_without_text=null_count, classified_high_item_occurrences=dict(totals),
                  classified_high_unique_items=len(unique), classified_high_nonitem_entries=nonitem_count)
    return prior, prior_public, prior_hash


def main():
    checks = []
    counts = {}
    report_path = REPORT

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
            "written_files": [report_path.relative_to(ROOT).as_posix()],
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "checks": len(checks),
                          "failures": failures, "counts": counts,
                          "report": str(report_path)}, ensure_ascii=False, indent=2))
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
    live_public = public.copy()
    active_count = len(combined['data'])
    integration_output_hash = file_hash(COMBINED)
    classified_high = "high_preparation_classification" in combined["metadata"]
    if classified_high:
        report_path = CLASSIFICATION_REPORT
        context = verify_high_classification(combined, public["activities"], check, counts, integration_output_hash)
        if context is None:
            return finish()
        combined, public["activities"], integration_output_hash = context
        counts["classification_preservation_basis"] = "현재 1,276행을 분류 전 스냅샷과 대조한 뒤 부록 제거·단원 정규화·최초 통합 이력을 역순 검증"
    removed_appendix = 'appendix_removal' in combined['metadata']
    if removed_appendix:
        if not classified_high:
            report_path = ROOT/'output/validation/remove-appendix-20260923/data-validation.json'
        history=COMBINED_DIR/'decision_history/20260923-remove-appendix'
        prior=read_json(history/COMBINED.name); prior_public=read_json(history/'public-activities.json')
        decision=read_json(history/'application.json'); excluded={'donga_IS2_045'}
        check('appendix_only_one_record_removed', combined['data']==[r for r in prior['data'] if r['id'] not in excluded]
              and active_count==1276 and combined['metadata']['appendix_removal']['excluded_ids']==list(excluded))
        check('appendix_remaining_public_rows_exactly_preserved',public['activities']==[r for r in prior_public if r['id'] not in excluded])
        check('appendix_unit_and_view_references_removed',len(combined['units'])==29
              and all(u['id']!='high-2-appendix' for u in combined['units'])
              and all(not (set(v.get('record_ids',[])) & excluded) for v in combined['views'].values())
              and len({a['unit'] for a in public['activities']})==29)
        check('appendix_counts_and_preservation_chain',combined['metadata']['record_count']==1276
              and combined['metadata']['integrated_science']['activities']==414
              and file_hash(history/COMBINED.name)==decision['before_sha256']==combined['metadata']['appendix_removal']['snapshot_sha256']
              and integration_output_hash==decision['output_sha256'])
        combined=prior;public['activities']=prior_public;integration_output_hash=file_hash(history/COMBINED.name)
        counts.update(current_active_activities=active_count,removed_appendix_activities=1)
    if "unit_normalization" in combined["metadata"]:
        if not removed_appendix and not classified_high:report_path = UNIT_REPORT
        context = verify_units(combined, public["activities"], check, counts, integration_output_hash)
        if context is None:
            return finish()
        combined, public["activities"], integration_output_hash = context
        counts["integration_preservation_basis"] = "정규화 전 1,277행 스냅샷; 현재 행까지의 보존은 unit_* 검사로 별도 대조"
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
    for row in live_public["activities"]:
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

    for name, document in live_public.items():
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
    check("combined_application_and_public_source_hashes", integration_output_hash == application.get("output_sha256")
          and hashes["combined"] == public["sources"].get("source_sha256") and public["sources"].get("record_count") == active_count
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
