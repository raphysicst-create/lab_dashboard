"""Build public, source-preserving data; keep review status outside the Site."""
import hashlib
import json
import re
from pathlib import Path
from build_chemicals import build_chemical_data, self_check, check_link_boundaries

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'outputs/extraction/combined-20260922/science_experiment_supplies_combined.json'
DEST = ROOT / 'site' / 'dist' / 'data'
REVIEW = ROOT / 'output' / 'validation'

# User-specified mapping: grade 1 covers units 1-8; grade 2 covers units 9-15.
# These are source unit numbers, not official curriculum identifiers.
GRADE_BY_UNIT = {n: 1 if n <= 8 else 2 for n in range(1, 16)}

def key(prefix, text):
    return prefix + '-' + hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def main():
    source = json.loads(SOURCE.read_text(encoding='utf-8-sig'))
    rows = source['data']
    assert len({r['id'] for r in rows}) == len(rows), 'Duplicate activity IDs'
    achievements, textbooks, activities = {}, {}, []
    review = []
    books = {book['book_id']: book for dataset in source['metadata']['source_datasets']
             for book in dataset['original_metadata'].get('source_books', [])}
    for row in rows:
        unit, standard, publisher = row['단원명'], row['성취기준'], row['출판사']
        unit_match = re.match(r'^\s*(\d+)\.', unit or '')
        unit_number = int(unit_match[1]) if unit_match else None
        book = books.get(row.get('source', {}).get('book_id'))
        assert not row.get('source') or book is not None, 'Unknown source book'
        assert not row['분류 보류'], 'Resolve pending classifications before publication'
        grade = book['grade'] if book else GRADE_BY_UNIT.get(unit_number)
        standard_match = re.match(r'^\s*(\d+)-(\d+)\.', standard or '')
        sequence = (int(standard_match[2]) if standard_match
                    and int(standard_match[1]) == unit_number else None)
        aid = key('ACH', json.dumps([unit, standard], ensure_ascii=False)) if standard is not None else None
        # These IDs identify source labels only, never infer textbook editions.
        tid = key('TXT', publisher or '')
        if aid is not None:
            achievements[aid] = {'id': aid, 'unit': unit, 'unit_number': unit_number,
                                 'sequence': sequence, 'raw_text': standard, 'code': None, 'grade': grade}
        textbooks[tid] = {'id': tid, 'publisher_raw': publisher, 'title': None, 'edition': None, 'grade': None}
        activity = {
            'id': row['id'], 'source_row': row['source_row'],
            'achievement_id': aid, 'textbook_id': tid, 'grade': grade,
            'unit': unit, 'unit_number': unit_number,
            'achievement_raw': standard, 'publisher_raw': publisher,
            'page': row['쪽'], 'title': row['탐구활동'], 'materials_raw': row['교구'],
            'equipment': row['실험 기자재'], 'supplies': row['실험 준비물'],
            # Category arrays preserve the approved classification and raw item text.
            'material_ids': [],
        }
        activities.append(activity)
        review.append({'activity_id': row['id'], 'source_row': row['source_row'],
                       'activity': 'textbook_not_checked', 'materials': 'textbook_not_checked',
                       'quantity': 'not_checked',
                       'grade_mapping': 'source_book' if book else 'user_specified',
                       'grade_mapping_basis': book['book_id'] if book else 'User instruction: units 1-8 = grade 1; units 9-15 = grade 2',
                       'achievement_number_mapping': 'source_prefix' if sequence is not None else 'not_checked',
                       'official_achievement_mapping': 'not_checked',
                       'missing_materials': row['교구'] is None})
    chemical_data = build_chemical_data(ROOT, activities)
    self_check(chemical_data)
    check_link_boundaries(ROOT)
    write(DEST / 'activities.json', chemical_data['activities'])
    write(DEST / 'achievements.json', list(achievements.values()))
    write(DEST / 'textbooks.json', list(textbooks.values()))
    write(DEST / 'materials.json', chemical_data['materials'])
    write(DEST / 'quantities.json', [])
    write(DEST / 'chemicals.json', chemical_data['chemicals'])
    write(DEST / 'chemical_guidelines.json', chemical_data['guidelines'])
    write(DEST / 'sources.json', {'source_name': SOURCE.name,
          'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(), 'record_count': len(rows)})
    write(REVIEW / 'verification.json', review)
    write(REVIEW / 'chemicals' / 'chemical-conversion-report.json', chemical_data['report'])
    write(REVIEW / 'chemicals' / 'chemical-catalogue-review.json', chemical_data['chemicals'])
    print(json.dumps({'activities': len(rows), 'achievements': len(achievements),
                      'publisher_labels': len(textbooks),
                      'missing_materials': sum(r['교구'] is None for r in rows),
                      'chemical_data': chemical_data['report']['counts']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
