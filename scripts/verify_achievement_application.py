"""Independently verify the 2026-09-23 achievement-standard application.

Run after the pre-application combined-data snapshot has been saved and
``scripts/build_data.py`` has regenerated public JSON. This script only writes
its validation report; it never edits source or public data.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "outputs/research/achievement-standards-20260923"
COMBINED = ROOT / "outputs/extraction/combined-20260922/science_experiment_supplies_combined.json"
SNAPSHOT = (ROOT / "outputs/extraction/combined-20260922/decision_history/"
            "20260923-achievements/science_experiment_supplies_combined.json")
PUBLIC = ROOT / "site/dist/data"
REPORT = ROOT / "output/validation/achievement-site-20260923/data-validation.json"

# Captured before the achievement-only change. Canonical JSON ignores key
# formatting but retains every activity and every non-achievement field.
BASE_PUBLIC_NONACH_SHA256 = "a322d3e549434a40643e30fec89fe928e35e812615703b748035391f7f7660f7"
ALLOWED_ROW_CHANGES = {"성취기준", "성취기준 코드", "성취기준 원문", "성취기준 연결"}
STATUS_COUNTS = {"direct": 136, "scope_based": 234, "candidate": 29, "unconfirmed": 9}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def legacy_id(unit: str, label: str) -> str:
    payload = json.dumps([unit, label], ensure_ascii=False)
    return "ACH-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def main() -> int:
    checks = []

    def check(name: str, ok: bool, detail=None) -> None:
        item = {"name": name, "passed": bool(ok)}
        if detail is not None:
            item["detail"] = detail
        checks.append(item)

    required = [SNAPSHOT, COMBINED, RESEARCH / "achievement_findings.json",
                RESEARCH / "original_achievement_crosswalk.json",
                RESEARCH / "official/official_standards.json",
                RESEARCH / "review_needed.json", RESEARCH / "baseline.json",
                PUBLIC / "activities.json", PUBLIC / "achievements.json"]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    check("required_files", not missing, missing)
    if missing:
        return finish(checks, {})

    old = read_json(SNAPSHOT)
    new = read_json(COMBINED)
    findings = read_json(RESEARCH / "achievement_findings.json")
    crosswalk = read_json(RESEARCH / "original_achievement_crosswalk.json")["rows"]
    official_file = read_json(RESEARCH / "official/official_standards.json")
    review = read_json(RESEARCH / "review_needed.json")["activities"]
    baseline = read_json(RESEARCH / "baseline.json")
    activities = read_json(PUBLIC / "activities.json")
    achievements = read_json(PUBLIC / "achievements.json")
    old_rows, rows = old["data"], new["data"]
    mappings = findings["activity_mappings"]
    official = {entry["code"]: entry for entry in official_file["standards"]}
    registry = new.get("achievement_standards", [])
    registry_by_code = {entry["code"]: entry for entry in registry}
    code_by_label = {entry["original_label"]: entry["official_code"] for entry in crosswalk}
    mapping_by_id = {entry["activity_id"]: entry for entry in mappings}
    achievement_by_id = {entry["id"]: entry for entry in achievements}

    check("pre_application_snapshot_hash",
          hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest() ==
          baseline["files"]["outputs/extraction/combined-20260922/science_experiment_supplies_combined.json"])
    check("original_input_file_unchanged",
          hashlib.sha256((ROOT / "science_experiment_supplies.json").read_bytes()).hexdigest() ==
          baseline["files"]["science_experiment_supplies.json"])
    check("all_three_input_files_unchanged",
          all(hashlib.sha256((ROOT / entry['input_file']).read_bytes()).hexdigest() == entry['sha256']
              for entry in old['metadata']['source_datasets']))
    check("official_87_unique_and_research_identical",
          len(official) == 87 == len(official_file["standards"])
          and findings["official_standards"] == official_file["standards"])
    check("crosswalk_56_unique_and_official",
          len(crosswalk) == 56 == len(code_by_label)
          and len({x["official_code"] for x in crosswalk}) == 56
          and all(x["official_code"] in official
                  and x["official_text"] == official[x["official_code"]]["raw_text"]
                  for x in crosswalk))
    check("mapping_408_unique_and_status_counts",
          len(mappings) == 408 == len(mapping_by_id)
          and dict(Counter(x["status"] for x in mappings)) == STATUS_COUNTS)
    review_ids = {entry["activity_id"] for entry in review}
    unresolved_ids = {entry["activity_id"] for entry in mappings
                      if entry["status"] in ("candidate", "unconfirmed")}
    extra_candidates = {entry["activity_id"] for entry in mappings
                        if entry["status"] in ("direct", "scope_based")
                        and entry["candidate_codes"]}
    check("review_41_exact_and_extra_candidates_3",
          len(review) == len(review_ids) == 41
          and len(unresolved_ids) == 38 and len(extra_candidates) == 3
          and review_ids == unresolved_ids | extra_candidates)

    check("combined_862_order_and_views",
          len(old_rows) == len(rows) == 862
          and [x["id"] for x in old_rows] == [x["id"] for x in rows]
          and old["views"] == new["views"])
    check("combined_87_registry_official_text",
          len(registry) == len(registry_by_code) == 87
          and set(registry_by_code) == set(official)
          and all(entry.get("raw_text") == official[code]["raw_text"]
                  and entry.get("chapter") == official[code]["chapter"]
                  and isinstance(entry.get("display_text"), str)
                  for code, entry in registry_by_code.items()))
    def normalized(text):
        return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text)).replace('·', '⋅')
    check("display_labels_preserve_official_wording",
          all(normalized(re.sub(r'^\d+-\d+\.\s*', '', entry['display_text'])) ==
              normalized(official[code]['raw_text']) for code, entry in registry_by_code.items()))
    check("combined_metadata_nonachievement_preserved",
          all(new["metadata"].get(k) == v for k, v in old["metadata"].items()
              if k not in {"missing_value_counts", "notes"})
          and all(new["metadata"].get("missing_value_counts", {}).get(k) == v
                  for k, v in old["metadata"].get("missing_value_counts", {}).items()
                  if k != "성취기준"))
    unrelated_differences = [before["id"] for before, after in zip(old_rows, rows)
                             if {k: v for k, v in before.items() if k not in ALLOWED_ROW_CHANGES}
                             != {k: v for k, v in after.items() if k not in ALLOWED_ROW_CHANGES}]
    check("all_original_nonachievement_row_values_preserved",
          not unrelated_differences, unrelated_differences[:12])

    row_ids = {row["id"] for row in rows}
    check("research_covers_exact_extracted_rows",
          len(row_ids) == 862 and set(mapping_by_id) == {row["id"] for row in old_rows[454:]})
    check("original_454_labels_preserved",
          all(before["성취기준"] == after["성취기준"]
              for before, after in zip(old_rows[:454], rows[:454])))
    check("original_454_official_codes",
          all(row.get("성취기준 코드") == [code_by_label.get(row["성취기준"])]
              and code_by_label.get(row["성취기준"]) in official
              for row in rows[:454]))
    check("original_454_connection_provenance",
          all(isinstance(row.get("성취기준 연결"), dict)
              and row["성취기준 연결"].get("status") == "original_text_match"
              and row["성취기준 연결"].get("candidate_codes") == []
              and row["성취기준 연결"].get("research_file") == "original_achievement_crosswalk.json"
              and bool(row["성취기준 연결"].get("reason"))
              for row in rows[:454]))

    mapping_errors = []
    for before, row in zip(old_rows[454:], rows[454:]):
        mapping = mapping_by_id.get(row["id"])
        if mapping is None:
            mapping_errors.append((row["id"], "missing_research_mapping"))
            continue
        status = mapping["status"]
        expected_codes = mapping["standard_codes"] if status in ("direct", "scope_based") else None
        if before["성취기준"] is not None:
            mapping_errors.append((row["id"], "preexisting_label_not_null"))
        if row.get("성취기준 코드") != expected_codes:
            mapping_errors.append((row["id"], "official_code_mismatch"))
        expected_text = registry_by_code[expected_codes[0]]["display_text"] if expected_codes else None
        if expected_text is not None and expected_text != row.get("성취기준"):
            mapping_errors.append((row["id"], "official_text_mismatch"))
        if expected_text is None and row.get("성취기준") is not None:
            mapping_errors.append((row["id"], "unresolved_label_should_be_null"))
        if row.get("성취기준 원문") is not None:
            mapping_errors.append((row["id"], "original_null_not_preserved"))
        link = row.get("성취기준 연결")
        if not isinstance(link, dict) or link.get("status") != status:
            mapping_errors.append((row["id"], "status_mismatch"))
        if isinstance(link, dict) and (link.get("evidence") != mapping["evidence"]
                                       or link.get("candidate_codes") != mapping["candidate_codes"]
                                       or link.get("reason") != mapping["reason"]
                                       or link.get("research_file") != mapping["research_file"]):
            mapping_errors.append((row["id"], "evidence_or_candidate_mismatch"))
    check("extracted_408_mapping_text_status_and_evidence", not mapping_errors,
          mapping_errors[:18])
    check("original_454_raw_copy_field",
          all(row.get("성취기준 원문") == before["성취기준"]
              for before, row in zip(old_rows[:454], rows[:454])))
    check("all_codes_are_one_official_or_null",
          all((row.get("성취기준 코드") is None or
               (isinstance(row["성취기준 코드"], list) and len(row["성취기준 코드"]) == 1
                and row["성취기준 코드"][0] in official)) for row in rows))
    check("370_applied_38_unresolved",
          sum(row["성취기준"] is not None for row in rows[454:]) == 370
          and sum(row["성취기준"] is None for row in rows[454:]) == 38)

    check("public_862_order_and_nonachievement_digest",
          len(activities) == 862
          and [a["id"] for a in activities] == [r["id"] for r in rows]
          and digest([{k: v for k, v in a.items()
                       if k not in {"achievement_id", "achievement_raw"}}
                      for a in activities]) == BASE_PUBLIC_NONACH_SHA256)
    check("public_raw_labels_match_combined",
          len(activities) == len(rows)
          and all(a.get("achievement_raw") == r.get("성취기준")
                  for a, r in zip(activities, rows)))
    check("original_56_public_ids_preserved",
          all(a.get("achievement_id") == legacy_id(r["단원명"], r["성취기준"])
              for a, r in zip(activities[:454], old_rows[:454])))
    check("public_achievements_87_unique_official_codes",
          len(achievements) == 87 == len(achievement_by_id)
          and {a.get("code") for a in achievements} == set(official))

    public_errors = []
    grades_by_code = {}
    for activity, row in zip(activities, rows):
        codes = row.get("성취기준 코드")
        achievement_id = activity.get("achievement_id")
        if codes is None:
            if achievement_id is not None:
                public_errors.append((activity["id"], "unresolved_id_not_null"))
            continue
        code = codes[0]
        achievement = achievement_by_id.get(achievement_id)
        if achievement is None or achievement.get("code") != code:
            public_errors.append((activity["id"], "code_id_reference_mismatch"))
        grades_by_code.setdefault(code, set()).add(activity.get("grade"))
    check("public_activity_code_id_references", not public_errors, public_errors[:18])
    check("public_achievement_grades_match_activities",
          all(a.get("grades") == sorted(grades_by_code.get(a.get("code"), set()))
                  for a in achievements))
    check("public_achievement_display_text_matches_registry",
          all(a.get("raw_text") == registry_by_code[a["code"]]["display_text"]
              for a in achievements if a.get("code") in registry_by_code))
    check("chemical_links_45_61_preserved",
          sum(bool(a.get("chemical_ids")) for a in activities) == 45
          and sum(len(a.get("chemical_ids", [])) for a in activities) == 61)

    counts = {
        "combined_rows": len(rows),
        "public_activities": len(activities),
        "public_achievements": len(achievements),
        "research_mapping_status": dict(Counter(x["status"] for x in mappings)),
        "combined_extracted_with_standards": sum(x["성취기준"] is not None for x in rows[454:]),
        "combined_extracted_unresolved": sum(x["성취기준"] is None for x in rows[454:]),
        "public_grades": dict(Counter(str(x.get("grade")) for x in activities)),
        "equipment_occurrences": sum(len(x["실험 기자재"] or []) for x in rows),
        "supplies_occurrences": sum(len(x["실험 준비물"] or []) for x in rows),
        "chemical_linked_activities": sum(bool(x.get("chemical_ids")) for x in activities),
        "chemical_link_occurrences": sum(len(x.get("chemical_ids", [])) for x in activities),
    }
    check("grade_and_classification_totals",
          counts["public_grades"] == {"1": 328, "2": 446, "3": 88}
          and counts["equipment_occurrences"] == 2924
          and counts["supplies_occurrences"] == 1095
          and sum(len(x["분류 보류"] or []) for x in rows) == 0)
    return finish(checks, counts)


def finish(checks: list[dict], counts: dict) -> int:
    failed = [item["name"] for item in checks if not item["passed"]]
    report = {"status": "pass" if not failed else "fail",
              "scope": "Local data and static-site JSON, 2026-09-23 achievement application",
              "checks": checks, "failed_checks": failed, "counts": counts}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "failed_checks": failed,
                      "report": str(REPORT.relative_to(ROOT)), "counts": counts}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
