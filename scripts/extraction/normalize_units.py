"""Unify chapter labels by source chapter, retaining exact original labels."""
import copy, hashlib, json, re, unicodedata
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/extraction/combined-20260922'
TARGET=OUT/'science_experiment_supplies_combined.json'
HISTORY=OUT/'decision_history/20260923-units'
def read(p):return json.loads(p.read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def chapter_key(label):
    label=re.split(r'[>/]',label)[0]
    label=unicodedata.normalize('NFKC',label)
    label=re.sub(r'^\s*(?:\d+|[IVX]+)\s*\.\s*','',label)
    return re.sub(r'\s+','',label).replace('⋅','·')

def main():
    HISTORY.mkdir(parents=True,exist_ok=True)
    snapshot=HISTORY/TARGET.name;current=read(TARGET)
    if not snapshot.exists():
        assert len(current['data'])==1277 and 'unit_normalization' not in current['metadata']
        snapshot.write_bytes(TARGET.read_bytes())
        (HISTORY/'prior-validation.json').write_bytes((OUT/'validation.json').read_bytes())
        (HISTORY/'public-activities.json').write_bytes((ROOT/'site/dist/data/activities.json').read_bytes())
    before=read(snapshot);result=copy.deepcopy(before);catalog={};lookup={}
    for s in before['achievement_standards']:
        high=s.get('school_level')=='고등학교';volume=s.get('volume') if high else None;n=s['unit_number']
        uid=f'high-{volume}-{n:02d}' if high else f'middle-{n:02d}'
        label=s['unit'];name=label.split(' · ',1)[-1] if high else label
        entry={'id':uid,'school_level':'고등학교' if high else '중학교','volume':volume,'number':n,'label':label}
        assert uid not in catalog or catalog[uid]==entry
        catalog[uid]=entry;lookup[(high,volume,chapter_key(name))]=entry
    appendix={'id':'high-2-appendix','school_level':'고등학교','volume':2,'number':None,'label':'통합과학 2 · 부록'}
    catalog[appendix['id']]=appendix;lookup[(True,2,'부록')]=appendix
    books={b['book_id']:b for d in before['metadata']['source_datasets'] for b in d['original_metadata'].get('source_books',[])}
    mapping=[]
    for r in result['data']:
        raw=r['단원명'];high=r.get('학교급')=='고등학교'
        volume=books[r['source']['book_id']]['volume'] if high else None
        matched=lookup.get((high,volume,chapter_key(raw)))
        assert matched is not None,f"Unrecognized source chapter: {r['id']} {raw}"
        r.update({'단원명 원문':raw,'단원명':matched['label'],'단원 번호':matched['number'],'단원 ID':matched['id']})
        mapping.append({'record_id':r['id'],'original':raw,'unit_id':matched['id'],'normalized':matched['label']})
    result['units']=list(catalog.values())
    result['metadata']['unit_normalization']={'date':'2026-09-23','policy':'실제 원문 대단원명과 학교급·권수로 연결. 중학교 기존 1~23단원 체계와 통합과학 권별 1~3단원 체계를 사용. 부록은 번호 null. 성취기준으로 활동 소속을 추정하지 않음.',
        'original_field':'단원명 원문','snapshot':snapshot.relative_to(ROOT).as_posix(),'snapshot_sha256':sha(snapshot),'unit_count':len(catalog)}
    assert current==before or current==result,'Subsequent edits detected; refusing overwrite'
    write(TARGET,result);write(HISTORY/'unit_catalog.json',list(catalog.values()));write(HISTORY/'mapping.json',mapping)
    report={'status':'passed','record_count':len(mapping),'unit_count':len(catalog),'before_sha256':sha(snapshot),'output_sha256':sha(TARGET),
        'unit_counts':dict(Counter(r['단원 ID'] for r in result['data'])),'changed_labels':sum(m['original']!=m['normalized'] for m in mapping),
        'preserved':'All non-unit activity fields and exact original chapter labels.',
        'validation':'output/validation/unit-normalization-20260923/data-validation.json'}
    write(HISTORY/'application.json',report);write(OUT/'validation.json',report)
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
