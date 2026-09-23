"""Compile reviewed textbook achievement findings without editing source or site data."""
import collections
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/research/achievement-standards-20260923'
PARTS = [
    'jihaksa/jihaksa-achievement-standards.json',
    'ybm-k7-k8/ybm_k7_k8_standards.json',
    'ybm-k9/ybm_k9_achievement_standards.json',
]
BOOKS = {
    'jihaksa_K7': ('지학사 K7', 82, 26, 294),
    'jihaksa_K8': ('지학사 K8', 87, 32, 352),
    'YBM_K7': ('YBM K7', 68, 26, 252),
    'YBM_K8': ('YBM K8', 83, 32, 328),
    'YBM_K9': ('YBM K9', 88, 29, 328),
}
STATUS = {
    'direct': '문서에 직접 연결',
    'scope_based': '소단원·목표·쪽수 대조 연결안',
    'candidate': '후보 — 판단 필요',
    'unconfirmed': '미확인',
}


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def normalized(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text)).replace('·', '⋅')


def main():
    official = read(OUT / 'official/official_standards.json')
    official_by_code = {r['code']: r for r in official['standards']}
    combined = read(ROOT / 'outputs/extraction/combined-20260922/science_experiment_supplies_combined.json')
    if 'achievement_mapping' in combined['metadata']:
        raise SystemExit('성취기준 적용 후입니다. 적용 전 조사 기록은 보존하며, 현재 결과 검증은 scripts/verify_achievement_application.py를 실행하세요.')
    source_rows = {r['id']: r for r in combined['data'] if r.get('source', {}).get('book_id') in BOOKS}
    assert len(source_rows) == 408
    mappings, book_standards, variants = [], [], []
    for part in PARTS:
        data = read(OUT / part)
        for standard in data['standards']:
            assert standard['book_id'] in BOOKS and standard['code'] in official_by_code
            canonical = official_by_code[standard['code']]['raw_text']
            if normalized(standard['raw_text']) != normalized(canonical):
                variants.append({'book_id': standard['book_id'], 'code': standard['code'],
                                 'textbook_text': standard['raw_text'], 'official_text': canonical})
            book_standards.append({**standard, 'official_text': canonical, 'research_file': part})
        for finding in data['activity_mappings']:
            original = source_rows[finding['activity_id']]
            book_id = original['source']['book_id']
            assert finding['book_id'] == book_id
            assert finding['title'] == original['탐구활동']
            assert finding['status'] in STATUS and finding['evidence']
            codes = finding.get('standard_codes')
            candidates = finding.get('candidate_codes') or []
            if finding['status'] in ('direct', 'scope_based'):
                assert codes and not set(codes).intersection(candidates)
            else:
                assert not codes
            for code in (codes or []) + candidates:
                assert code in official_by_code
            for evidence in finding['evidence']:
                if evidence.get('pdf_page') is not None:
                    assert 1 <= evidence['pdf_page'] <= BOOKS[book_id][3]
            mappings.append({**finding, 'candidate_codes': candidates,
                             'unit_raw': original['단원명'], 'printed_page': original['쪽'],
                             'original_achievement_raw': original['성취기준'], 'research_file': part})
    by_id = {r['activity_id']: r for r in mappings}
    assert len(by_id) == len(mappings) == 408 and set(by_id) == set(source_rows)
    mappings = [by_id[key] for key in source_rows]
    assert len({(r['book_id'], r['code']) for r in book_standards}) == len(book_standards)
    counts = []
    for book_id, (label, expected_rows, expected_standards, _) in BOOKS.items():
        rows = [r for r in mappings if r['book_id'] == book_id]
        standards = [r for r in book_standards if r['book_id'] == book_id]
        assert len(rows) == expected_rows and len(standards) == expected_standards
        book_codes = {s['code'] for s in standards}
        assert all(code in book_codes for r in rows for code in (r['standard_codes'] or []))
        counts.append({'book_id': book_id, 'label': label, 'standards': len(standards),
                       'activities': len(rows), **{s: sum(r['status'] == s for r in rows) for s in STATUS}})
    baseline = read(OUT / 'baseline.json')['files']
    for path, expected_hash in baseline.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected_hash, path
    metadata = {
        'research_date': '2026-09-23', 'purpose': '성취기준 조사 및 활동 연결 검토. 사이트 적용 전 자료.',
        'site_modified': False, 'original_data_modified': False, 'default_sort_modified': False,
        'status_definitions': STATUS,
        'scope_based_limit': '교과서의 소단원·학습목표·쪽수와 공식 기준을 대조해 도출한 연결안이다. 출판사가 활동별 공식 코드를 직접 지정했다는 뜻은 아니다.',
        'candidate_policy': '후보·미확인은 standard_codes를 null로 두며 candidate_codes와 분리한다.',
        'official_source_url': official['source_url'], 'book_counts': counts,
    }
    totals = dict(collections.Counter(r['status'] for r in mappings))
    write(OUT / 'achievement_findings.json', {'metadata': metadata,
          'official_standards': official['standards'], 'book_standards': book_standards,
          'activity_mappings': mappings})
    pending = [r for r in mappings if r['status'] in ('candidate', 'unconfirmed') or r['candidate_codes']]
    write(OUT / 'review_needed.json', {'note': '사용자 판단 또는 추가 지도자료 확인이 필요한 활동', 'activities': pending})
    write(OUT / 'validation.json', {'status': 'passed', 'activity_count': 408,
          'unique_official_standards': len(official_by_code), 'book_standard_records': len(book_standards),
          'status_counts': totals, 'review_activity_count': len(pending),
          'additional_candidate_activity_count': sum(r['status'] in ('direct', 'scope_based') and bool(r['candidate_codes']) for r in mappings),
          'book_counts': counts, 'textbook_official_text_variants': variants,
          'source_and_site_hashes_unchanged': True})
    lines = ['# 지학사·YBM 성취기준 조사 결과', '',
             '조사일: 2026-09-23. 기존 통합 JSON·사이트 데이터·기본 정렬은 변경하지 않았습니다.', '',
             '## 확인한 성취기준', '',
             '[교육부 고시 제2022-33호 과학과 교육과정](' + official['source_url'] + ')과 교과서 자료를 대조했습니다. 중학교 공식 기준은 중복 제외 87개입니다. 기존 원자료의 성취기준 56개는 공백·가운뎃점 표기를 제외하고 공식 문장과 모두 일치합니다.', '',
             '| 교과서 | 성취기준 | 활동 | 문서 직접 연결 | 범위·목표 대조 연결안 | 후보 | 미확인 |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for c in counts:
        lines.append(f"| {c['label']} | {c['standards']} | {c['activities']} | {c['direct']} | {c['scope_based']} | {c['candidate']} | {c['unconfirmed']} |")
    lines += ['', '성취기준 개수는 책별 수록 범위이며 같은 학년의 두 출판사는 같은 기준을 사용합니다.', '',
              '## 연결 상태의 의미', '',
              '- **문서 직접 연결**: 교사용 지도 계획 등의 동일 성취기준 칸에 활동명 또는 해당 활동의 쪽수가 명시됩니다. 빈 성취기준 칸에 앞 행의 코드를 이어 붙이지 않았습니다.',
              '- **범위·목표 대조 연결안**: 교과서의 소단원·지도 목표·자기점검 목표와 본문 쪽수를 공식 기준과 대조한 결과입니다. 활동별 공식 코드의 직접 기재와는 구분합니다.',
              '- **후보·미확인**: 다른 소단원의 확장 활동, 여러 기준을 넘나드는 창의 활동 등입니다. 임의 확정하지 않고 판단 목록에 남겼습니다.', '',
              'YBM K9 원본은 학생용 교과서입니다. 공식 코드 자체는 교육부 고시에서 확인했고, 책의 ‘나의 학습 되돌아보기’에 제시된 목표와 참조 쪽수를 대조했습니다. 참조 쪽수와 검토자가 목차·본문에서 도출한 소단원 범위는 구분해 기록했습니다.', '',
              '## 결과 파일', '',
              '- [통합 조사 JSON](achievement_findings.json): 408개 활동의 코드·근거 쪽수·인용·판단 상태',
              '- [판단이 필요한 활동](review_needed.json)',
              '- [공식 성취기준 87개 원문](official/standards.md)',
              '- [기존 원자료 56개 기준과 공식 코드 대조표](original_achievement_crosswalk.json)',
              '- [검증 기록](validation.json)', '',
              '각 책별 상세 조사와 시각 검수 기록은 하위 폴더에 보존했습니다. 교과서 표현과 고시 문장의 차이는 양쪽을 따로 보존했습니다. 판단 목록에는 범위 연결안 외에 추가 후보 코드가 있는 활동도 포함합니다.', '',
              '## 판단이 필요한 활동', '']
    for row in pending:
        codes = ', '.join(row['candidate_codes']) or '후보 없음'
        lines.append(f"- **{BOOKS[row['book_id']][0]} {row['printed_page']}쪽 · {row['title']}** — {codes}. {row['reason']}")
    (OUT / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'activities': 408, 'status_counts': totals, 'book_counts': counts,
                      'text_variants': variants}, ensure_ascii=False))


if __name__ == '__main__':
    main()
