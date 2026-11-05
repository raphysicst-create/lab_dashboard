"""Validate and combine the independently extracted YBM K7/K8/K9 datasets.

Run with Python 3.10+. Source PDFs are read only; the original 454-row JSON is
not an input to the combination and is never modified.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import unicodedata


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / 'outputs/extraction/ybm-20260922'
FIELDS = ('id', 'source_row', '단원명', '성취기준', '출판사', '쪽', '탐구활동', '교구', 'source')


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--source-dir', type=Path, default=Path('C:/Users/USER/Desktop/maintain/textbook_wiki/raw'))
    args = parser.parse_args()
    errors, warnings, books, rows = [], [], [], []
    original = ROOT / 'science_experiment_supplies.json'
    original_hash = hashlib.sha256(original.read_bytes()).hexdigest()
    baseline_results = []
    baseline_path = args.output / 'baseline.json'
    if baseline_path.exists():
        for relative, expected in json.loads(baseline_path.read_text(encoding='utf-8')).items():
            actual = file_sha256(ROOT / relative)
            baseline_results.append({'file': relative, 'unchanged': actual == expected, 'sha256': actual})
            if actual != expected:
                errors.append(f'Protected baseline file changed: {relative}')
    for level, grade, page_count in [('K7', 1, 252), ('K8', 2, 328), ('K9', 3, 328)]:
        path = args.output / level / f'science_experiment_supplies_YBM_{level}.json'
        obj = json.loads(path.read_text(encoding='utf-8-sig'))
        data = obj['data']
        source = args.source_dir / f'textbook_YBM_{level}.pdf'
        sha = file_sha256(source)
        declared_sha = obj['metadata'].get('sha256', obj['metadata'].get('source_sha256'))
        if not isinstance(declared_sha, str) or declared_sha.lower() != sha:
            errors.append(f'{level}: source hash mismatch/missing')
        if obj['metadata'].get('record_count') != len(data):
            errors.append(f'{level}: metadata record_count mismatch')
        if obj['metadata'].get('grade') != grade:
            errors.append(f'{level}: incorrect grade metadata')
        if obj['metadata'].get('book_id') != f'YBM_{level}':
            errors.append(f'{level}: incorrect book_id metadata')
        if obj['metadata'].get('pdf_page_count') != page_count:
            errors.append(f'{level}: incorrect pdf_page_count')
        ids = [r.get('id') for r in data]
        seen_keys = set()
        for r in data:
            rid = r.get('id', '(missing)')
            missing = [f for f in FIELDS if f not in r]
            if missing:
                errors.append(f'{rid}: missing fields {missing}')
                continue
            if not isinstance(rid, str) or not rid.startswith(f'ybm_{level.lower()}_'):
                errors.append(f'{rid}: incorrect book-specific ID')
            if r['source_row'] is not None or r['출판사'] != 'YBM':
                errors.append(f'{rid}: incorrect provenance/publisher')
            for f in ['단원명', '탐구활동']:
                if not isinstance(r[f], str) or not r[f].strip():
                    errors.append(f'{rid}: empty/non-string {f}')
            for f in ['단원명', '탐구활동', '교구']:
                if isinstance(r[f], str) and re.search(r'[\u0590-\u08ff\u0980-\u0dff\x00-\x08\x0b\x0c\x0e-\x1f]', r[f]):
                    errors.append(f'{rid}: suspicious font-decoding characters in {f}; inspect original image')
            for f in ['교구', '성취기준']:
                if r[f] is not None and (not isinstance(r[f], str) or not r[f].strip()):
                    errors.append(f'{rid}: {f} must be null or non-empty string')
                if r[f] in ['미확인', '없음', '자료 없음']:
                    errors.append(f'{rid}: placeholder instead of null in {f}')
            s = r['source']
            if s.get('book_id') != f'YBM_{level}':
                errors.append(f'{rid}: source.book_id mismatch')
            pages = s.get('pdf_pages')
            if not isinstance(pages, list) or not pages or any(type(p) is not int or not 1 <= p <= page_count for p in pages):
                errors.append(f'{rid}: invalid PDF pages')
            elif len(set(pages)) != len(pages):
                errors.append(f'{rid}: repeated PDF page')
            printed = s.get('printed_pages')
            if not isinstance(printed, list) or any(type(p) is not int or p <= 0 for p in printed):
                errors.append(f'{rid}: invalid printed_pages')
            if r['쪽'] is not None and (type(r['쪽']) is not int or r['쪽'] not in (printed or [])):
                errors.append(f'{rid}: first printed page not in source pages')
            for f in ['activity_type', 'chapter_label', 'title_quote']:
                if not isinstance(s.get(f), str) or not s[f].strip():
                    errors.append(f'{rid}: missing {f}')
            if not isinstance(s.get('review_notes'), list):
                errors.append(f'{rid}: review_notes must be list')
            for value, quote in [('교구', 'supplies_quote'), ('성취기준', 'standard_quote')]:
                if r[value] is not None and not s.get(quote):
                    errors.append(f'{rid}: {value} lacks evidence quote')
            key = (r['쪽'], r['탐구활동'])
            if key in seen_keys:
                errors.append(f'{rid}: duplicate title at printed page')
            seen_keys.add(key)
        if len(ids) != len(set(ids)):
            errors.append(f'{level}: duplicate IDs')
        view = obj.get('views', {}).get('기본자료', {})
        if view.get('record_ids') != ids or view.get('record_count') != len(data):
            errors.append(f'{level}: 기본자료 view must match all IDs in order')
        coverage_path = args.output / level / 'coverage.json'
        if not coverage_path.exists():
            errors.append(f'{level}: missing coverage.json')
        else:
            coverage = json.loads(coverage_path.read_text(encoding='utf-8-sig'))
            coverage_pages = coverage.get('pages', coverage.get('page_decisions', []))
            if sorted(p.get('pdf_page', -1) for p in coverage_pages) != list(range(1, page_count + 1)):
                errors.append(f'{level}: coverage must classify every PDF page exactly once')
            by_page = {p.get('pdf_page'): p for p in coverage_pages}
            by_id = {r['id']: r for r in data}
            for p in coverage_pages:
                unknown = set(p.get('record_ids', [])) - set(ids)
                if unknown:
                    errors.append(f"{level}: coverage page {p.get('pdf_page')} references unknown records {sorted(unknown)}")
                for rid in set(p.get('record_ids', [])) - unknown:
                    if p.get('pdf_page') not in by_id[rid]['source']['pdf_pages']:
                        errors.append(f"{rid}: coverage page {p.get('pdf_page')} not in record source pages")
            for r in data:
                for p in r['source']['pdf_pages']:
                    if r['id'] not in by_page.get(p, {}).get('record_ids', []):
                        errors.append(f"{r['id']}: missing from coverage page {p}")
        books.append({
            'book_id': f'YBM_{level}', 'grade': grade,
            'source_file': source.name, 'source_sha256': sha,
            'pdf_page_count': page_count, 'record_count': len(data),
            'supplies_null': sum(r['교구'] is None for r in data),
            'standards_null': sum(r['성취기준'] is None for r in data),
            'by_chapter': dict(Counter(r['단원명'] for r in data)),
            'by_activity_type': dict(Counter(r['source'].get('activity_type') for r in data)),
            'extraction_metadata': obj['metadata'],
        })
        rows.extend(data)
    if len({r['id'] for r in rows}) != len(rows):
        errors.append('combined: duplicate IDs')
    review_path = args.output / 'parent_review.json'
    if review_path.exists():
        review = json.loads(review_path.read_text(encoding='utf-8'))
        if review.get('original_454_record_json_sha256_before_combination') != original_hash:
            errors.append('Original 454-row dataset changed since the review baseline')
    reference_results = []
    references_path = args.output / 'reference_checks.json'
    if references_path.exists():
        def comparable(value):
            if value is None:
                return None
            return re.sub(r'[\s,，]', '', unicodedata.normalize('NFKC', value))

        references = json.loads(references_path.read_text(encoding='utf-8'))['checks']
        for ref in references:
            matching = [r for r in rows if r['source']['book_id'] == ref['book_id'] and r['쪽'] == ref['page'] and comparable(r['탐구활동']) == comparable(ref['title'])]
            result = {'book_id': ref['book_id'], 'printed_page': ref['page'], 'title': ref['title'], 'passed': False}
            if len(matching) != 1:
                errors.append(f"Reference {ref['book_id']} p{ref['page']}: expected title missing/duplicate: {ref['title']}")
            else:
                row = matching[0]
                same = comparable(row['교구']) == comparable(ref['supplies'])
                pages_ok = set(ref.get('pdf_pages_include', [])).issubset(row['source']['pdf_pages'])
                result.update({'record_id': row['id'], 'supplies_match': same, 'page_coverage_match': pages_ok, 'passed': same and pages_ok})
                if not same or not pages_ok:
                    errors.append(f"Reference {row['id']}: visually checked supplies/page coverage mismatch")
            reference_results.append(result)
    report = {
        'status': 'passed' if not errors else 'failed',
        'scope': 'Structural/provenance validation, not a claim of complete visual verification.',
        'books': books, 'total_record_count': len(rows), 'errors': errors, 'warnings': warnings,
        'independent_visual_reference_checks': reference_results,
        'original_454_record_json_sha256': original_hash,
        'original_454_record_json_unchanged_during_validation': hashlib.sha256(original.read_bytes()).hexdigest() == original_hash,
        'protected_baseline_files': baseline_results,
    }
    write_json(args.output / 'validation.json', report)
    if errors:
        print(json.dumps({'status': 'failed', 'errors': errors}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    combined = {
        'metadata': {
            'schema_version': '1.0-YBM-extraction', 'record_count': len(rows),
            'source_books': books,
            'original_columns': ['단원명', '성취기준', '출판사', '쪽', '탐구활동', '교구'],
            'notes': [
                'K7, K8 and K9 are independent book extractions; existing 454 activity rows are not merged.',
                'Chapter names/numbers preserve the source book and are not the website grade mapping.',
                'Missing explicitly stated supplies or confirmed achievement standards remain null.',
                'Source document type is recorded per book; activities target the student textbook region.',
                'See book coverage.json, extraction_report.md and parent review for verification limits.',
            ],
        },
        'data': rows,
        'views': {
            '기본자료': {'record_count': len(rows), 'record_ids': [r['id'] for r in rows]},
            **{b['book_id']: {'record_count': b['record_count'], 'record_ids': [r['id'] for r in rows if r['source']['book_id'] == b['book_id']]} for b in books},
        },
    }
    write_json(args.output / 'science_experiment_supplies_YBM.json', combined)
    print(json.dumps({'status': 'passed', 'total': len(rows), 'books': [{k: b[k] for k in ['book_id', 'record_count', 'supplies_null', 'standards_null']} for b in books]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
