"""Unify approved publisher labels while preserving the original source values."""
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / 'outputs/extraction/combined-20260922'
TARGET = DIRECTORY / 'science_experiment_supplies_combined.json'
HISTORY = DIRECTORY / 'decision_history/20260923-publishers'
ALIASES = {'동아': '동아출판', '미래앤': '미래엔', '비상': '비상교육'}


def read(path):
    return json.loads(path.read_text('utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    current = read(TARGET)
    HISTORY.mkdir(parents=True, exist_ok=True)
    snapshot = HISTORY / TARGET.name
    if not snapshot.exists():
        assert len(current['data']) == 1276 and 'publisher_normalization' not in current['metadata']
        snapshot.write_bytes(TARGET.read_bytes())
        for name in ['activities', 'textbooks']:
            (HISTORY / f'public-{name}.json').write_bytes((ROOT / f'site/dist/data/{name}.json').read_bytes())
    before = read(snapshot)
    result = copy.deepcopy(before)
    changed = 0
    for row in result['data']:
        original = row['출판사']
        if original in ALIASES:
            assert '출판사 원문' not in row
            row['출판사 원문'] = original
            row['출판사'] = ALIASES[original]
            changed += 1
    counts = dict(Counter(row['출판사'] for row in result['data']))
    assert changed == 266 and len(counts) == 8
    result['metadata']['publisher_counts'] = counts
    result['metadata']['publisher_normalization'] = {
        'date': '2026-09-23',
        'authorization': '사용자 요청: 천재 교과서 빼고 두 이름으로 나뉜 교과서 표기 일원화',
        'aliases': ALIASES, 'changed_rows': changed,
        'snapshot': snapshot.relative_to(ROOT).as_posix(), 'snapshot_sha256': digest(snapshot),
    }
    assert current == before or current == result, 'Subsequent edits detected; refusing overwrite'
    write(TARGET, result)
    report = {'status': 'passed', 'before_sha256': digest(snapshot), 'output_sha256': digest(TARGET),
              'aliases': ALIASES, 'changed_rows': changed, 'publisher_counts': counts, 'record_count': 1276}
    write(HISTORY / 'application.json', report)
    write(DIRECTORY / 'validation.json', report)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
