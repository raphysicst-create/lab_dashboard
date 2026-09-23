"""Combine the original, Jihaksa and YBM JSONs without changing source records."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/extraction/combined-20260922'
INPUTS = [
    ('original', '원자료', 'science_experiment_supplies.json'),
    ('jihaksa', '지학사', 'outputs/extraction/jihaksa-20260922/science_experiment_supplies_jihaksa.json'),
    ('ybm', 'YBM', 'outputs/extraction/ybm-20260922/science_experiment_supplies_YBM.json'),
]
FIELDS = ['단원명', '성취기준', '출판사', '쪽', '탐구활동', '교구']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    existing = OUT / 'science_experiment_supplies_combined.json'
    if existing.exists() and 'preparation_classification' in json.loads(existing.read_text(encoding='utf-8'))['metadata']:
        raise SystemExit('준비물 분류가 추가된 통합본입니다. 덮어쓰지 않았습니다. 분류 변경은 classify_supplies.py를 사용하세요.')
    records, sources, views, originals = [], [], {}, []
    for dataset_id, label, relative in INPUTS:
        path = ROOT / relative
        source_hash = sha(path)
        obj = json.loads(path.read_text(encoding='utf-8-sig'))
        data = obj['data']
        if obj['metadata']['record_count'] != len(data):
            raise ValueError(f'{label}: metadata count mismatch')
        ids = [r['id'] for r in data]
        if len(ids) != len(set(ids)):
            raise ValueError(f'{label}: duplicate IDs')
        for row in data:
            if any(key not in row for key in FIELDS):
                raise ValueError(f'{label}: missing original field')
        start = len(records)
        records.extend(data)
        views[label] = {'record_count': len(data), 'record_ids': ids}
        source_views = {}
        for name, view in obj.get('views', {}).items():
            combined_name = f'{label}/{name}'
            if not set(view['record_ids']).issubset(ids):
                raise ValueError(f'{label}/{name}: unknown record reference')
            views[combined_name] = view
            source_views[name] = combined_name
        sources.append({
            'dataset_id': dataset_id, 'label': label, 'input_file': relative,
            'sha256': source_hash, 'record_count': len(data),
            'record_index_range_zero_based': [start, len(records) - 1],
            'view': label, 'original_view_names': source_views,
            'original_metadata': obj['metadata'],
        })
        originals.append(obj)
    ids = [r['id'] for r in records]
    if len(ids) != len(set(ids)):
        raise ValueError('Cross-dataset ID collision; inputs remain unchanged')
    combined = {
        'metadata': {
            'schema_version': '1.0-combined', 'record_count': len(records),
            'original_columns': FIELDS, 'source_datasets': sources,
            'missing_value_counts': {key: sum(r[key] is None for r in records) for key in FIELDS},
            'publisher_counts': dict(Counter(r['출판사'] for r in records)),
            'notes': [
                '원자료 → 지학사 → YBM 순서로 각 입력의 행 순서를 유지하여 통합했다.',
                '행의 ID, 원문, null, 출처·검토 필드를 수정하지 않고 모두 보존했다.',
                '출처별 views와 metadata.source_datasets로 각 행의 입력 파일을 추적할 수 있다.',
                '원래의 views는 출처명/뷰이름으로 보존하고 기본자료는 전체 행을 참조한다.',
                '활동 제목의 유사성만으로 행을 합치거나 중복 삭제하지 않았다.',
                '출처별 단원 번호 체계와 성취기준 확인 상태를 그대로 유지했다.',
            ],
        },
        'data': records,
        'views': {'기본자료': {'record_count': len(records), 'record_ids': ids}, **views},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / 'science_experiment_supplies_combined.json'
    write_json(target, combined)
    saved = json.loads(target.read_text(encoding='utf-8'))
    results = []
    for source, obj in zip(sources, originals):
        start, end = source['record_index_range_zero_based']
        same = saved['data'][start:end + 1] == obj['data']
        untouched = sha(ROOT / source['input_file']) == source['sha256']
        if not same or not untouched:
            raise ValueError(f"{source['label']}: preservation check failed")
        results.append({'dataset': source['label'], 'record_count': source['record_count'],
                        'records_exactly_preserved': same, 'input_file_unchanged': untouched})
    if saved != combined:
        raise ValueError('JSON round-trip mismatch')
    report = {'status': 'passed', 'record_count': len(records), 'unique_id_count': len(set(ids)),
              'output_sha256': sha(target), 'sources': results,
              'scope': '통합 구조와 원본 행·파일 보존 검사. 원문 교과서 재검토가 아님.'}
    write_json(OUT / 'validation.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
