"""Apply reviewed achievement links, preserving the pre-application source snapshot."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/extraction/combined-20260922'
TARGET = OUT / 'science_experiment_supplies_combined.json'
HISTORY = OUT / 'decision_history/20260923-achievements'
SNAPSHOT = HISTORY / TARGET.name
RESEARCH = ROOT / 'outputs/research/achievement-standards-20260923'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    current = read(TARGET)
    HISTORY.mkdir(parents=True, exist_ok=True)
    if not SNAPSHOT.exists():
        assert 'achievement_mapping' not in current['metadata'], 'Missing pre-application snapshot'
        expected = read(RESEARCH / 'baseline.json')['files'][TARGET.relative_to(ROOT).as_posix()]
        assert sha(TARGET) == expected, 'Combined data changed since the reviewed research'
        SNAPSHOT.write_bytes(TARGET.read_bytes())
    prior_validation = HISTORY / 'prior-validation.json'
    if not prior_validation.exists():
        prior_validation.write_bytes((OUT / 'validation.json').read_bytes())
    before = read(SNAPSHOT)
    findings = read(RESEARCH / 'achievement_findings.json')
    crosswalk = read(RESEARCH / 'original_achievement_crosswalk.json')['rows']
    original_codes = {r['original_label']: r['official_code'] for r in crosswalk}
    original_labels = {r['official_code']: r['original_label'] for r in crosswalk}
    original_units = {original_codes[r['성취기준']]: r['단원명'] for r in before['data'] if not r.get('source')}
    standards = []
    for standard in findings['official_standards']:
        code = standard['code']
        match = re.fullmatch(r'9과(\d+)-(\d+)', code)
        number, sequence = map(int, match.groups())
        standards.append({**standard,
            'display_text': original_labels.get(code, f'{number}-{sequence}. ' + standard['raw_text']),
            'unit': original_units.get(code, f'{number}. ' + standard['chapter']),
            'unit_number': number, 'sequence': sequence})
    by_code = {s['code']: s for s in standards}
    mappings = {r['activity_id']: r for r in findings['activity_mappings']}
    result = deepcopy(before)
    counts = Counter()
    for row in result['data']:
        row['성취기준 원문'] = row['성취기준']
        if row['id'] in mappings:
            finding = mappings[row['id']]
            assert row['source']['book_id'] == finding['book_id']
            assert row['탐구활동'] == finding['title']
            assert row['성취기준'] == finding['original_achievement_raw']
            codes = finding['standard_codes'] if finding['status'] in ('direct', 'scope_based') else None
            # This research has exactly one accepted code per linked activity.
            assert not codes or len(codes) == 1
            row['성취기준'] = by_code[codes[0]]['display_text'] if codes else None
            row['성취기준 코드'] = codes
            row['성취기준 연결'] = {k: deepcopy(finding[k]) for k in
                ('status', 'candidate_codes', 'reason', 'evidence', 'research_file')}
            counts[finding['status']] += 1
        else:
            code = original_codes[row['성취기준']]
            row['성취기준 코드'] = [code]
            row['성취기준 연결'] = {
                'status': 'original_text_match', 'candidate_codes': [],
                'reason': '기존 성취기준 문장이 공식 원문과 일치함(공백·가운뎃점 표기 정규화). 기존 활동 연결은 유지.',
                'research_file': 'original_achievement_crosswalk.json'}
    assert counts == {'direct': 136, 'scope_based': 234, 'candidate': 29, 'unconfirmed': 9}
    result['achievement_standards'] = standards
    result['metadata']['achievement_mapping'] = {
        'applied_date': '2026-09-23', 'authorization': '사용자 요청: json이랑 사이트에 반영해줘',
        'accepted_statuses': ['direct', 'scope_based'], 'status_counts': dict(counts),
        'newly_linked_activities': 370, 'unconfirmed_activities': 38,
        'original_value_field': '성취기준 원문',
        'scope_based_limit': findings['metadata']['scope_based_limit'],
        'candidate_policy': '후보 코드와 미확인은 공개 연결에서 제외하며 검토 근거에만 보존한다.',
        'research_file': (RESEARCH / 'achievement_findings.json').relative_to(ROOT).as_posix(),
        'research_sha256': sha(RESEARCH / 'achievement_findings.json'),
        'pre_application_snapshot': SNAPSHOT.relative_to(ROOT).as_posix(),
        'pre_application_sha256': sha(SNAPSHOT),
        'official_source_url': findings['metadata']['official_source_url'],
    }
    result['metadata']['missing_value_counts']['성취기준'] = 38
    if 'achievement_mapping' in current['metadata']:
        assert current == result, 'Applied data changed; do not overwrite subsequent edits'
    else:
        assert current == before, 'Combined data changed after snapshot'
    write(TARGET, result)
    write(HISTORY / 'application.json', {
        'status': 'applied', 'before_sha256': sha(SNAPSHOT), 'after_sha256': sha(TARGET),
        'research_sha256': sha(RESEARCH / 'achievement_findings.json'),
        'activities': len(result['data']), 'status_counts': dict(counts),
        'official_standards': len(standards), 'new_links': 370, 'remaining_null': 38,
        'preserved': ['original input files', 'original achievement values', 'preparation text and classification',
                      'activity order', 'grade mapping', 'default sort rule'],
    })
    write(OUT / 'validation.json', {
        'status': 'passed', 'record_count': len(result['data']),
        'unique_id_count': len({row['id'] for row in result['data']}),
        'output_sha256': sha(TARGET), 'new_achievement_links': 370,
        'unconfirmed_achievements': 38, 'official_standards': len(standards),
        'application_record': 'decision_history/20260923-achievements/application.json',
        'prior_validation': 'decision_history/20260923-achievements/prior-validation.json',
        'independent_validation': 'output/validation/achievement-site-20260923/data-validation.json',
        'scope': '조사한 연결 적용 및 적용 전 스냅샷 보존. 전체 보존·공개 연결 검증은 independent_validation 참고.',
    })
    print(json.dumps({'activities': len(result['data']), 'new_links': 370,
                      'remaining_null': 38, 'official_standards': len(standards)}))


if __name__ == '__main__':
    main()
