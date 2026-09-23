"""Apply reviewed high-school supply spans using the existing classroom categories."""
import copy, hashlib, json, re, unicodedata
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/extraction/combined-20260922'
TARGET=OUT/'science_experiment_supplies_combined.json'
HISTORY=OUT/'decision_history/20260923-high-classification'
REVIEW=ROOT/'outputs/extraction/integrated-science-20260923/preparation_classification'
CATEGORIES=['실험 기자재','실험 준비물']
def read(p):return json.loads(p.read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s))
def main():
    HISTORY.mkdir(parents=True,exist_ok=True);snapshot=HISTORY/TARGET.name;current=read(TARGET)
    if not snapshot.exists():
        assert len(current['data'])==1276 and 'high_preparation_classification' not in current['metadata']
        snapshot.write_bytes(TARGET.read_bytes())
        (HISTORY/'public-activities.json').write_bytes((ROOT/'site/dist/data/activities.json').read_bytes())
    before=read(snapshot);result=copy.deepcopy(before);mapping={};counts=Counter();catalog={}
    for name in ['miraen_jihaksa','chunjae','visang_donga']:
        for entry in read(REVIEW/f'{name}.json')['records']:
            assert entry['record_id'] not in mapping
            mapping[entry['record_id']]=entry
    high=[r for r in result['data'] if r.get('학교급')=='고등학교']
    assert len(high)==414 and set(mapping)=={r['id'] for r in high}
    old_catalog={norm(i['representative_text']):i for i in read(OUT/'preparation_item_catalogue.json')['items']}
    for r in high:
        entry=mapping[r['id']];raw=r['교구'];items=entry['items'];r['준비물 표시 방식']='분류'
        if raw is None:
            assert items is None and not entry.get('non_items')
            assert all(r[k] is None for k in CATEGORIES+['분류 보류','준비물 분류'])
            continue
        assert isinstance(items,list) and items
        used=set()
        for part in items+entry.get('non_items',[]):
            a,b=part['span'];assert 0<=a<b<=len(raw) and raw[a:b]==part['raw'],r['id']
            assert not used.intersection(range(a,b)),r['id'];used.update(range(a,b))
        assert all(c.isspace() or c in ',，□☐•' for n,c in enumerate(raw) if n not in used),(r['id'],'Uncovered text')
        for category in CATEGORIES:r[category]=[]
        r['분류 보류']=[];r['준비물 분류']=[]
        for part in items:
            category=part['category'];assert category in CATEGORIES,(r['id'],part)
            key=norm(part['raw']);old=old_catalog.get(key)
            if old:assert old['category']==category,(r['id'],part['raw'],'Existing decision differs',old['category'])
            iid='ITEM-'+hashlib.sha256(key.encode('utf-8')).hexdigest()[:16]
            assert iid not in catalog or catalog[iid]['category']==category,(r['id'],'Inconsistent category',part['raw'])
            r[category].append(part['raw']);counts[category]+=1
            r['준비물 분류'].append({'item_id':iid,'원문':part['raw'],'원문_범위':part['span'],'분류':category,'근거':part['reason'],'판단출처':part['decision_source']})
            item=catalog.setdefault(iid,{'item_id':iid,'representative_text':part['raw'],'category':category,'occurrences':[]})
            item['occurrences'].append({'record_id':r['id'],'span':part['span'],'raw':part['raw']})
        if entry.get('non_items'):r['준비물 분류 비항목']=entry['non_items']
    result['metadata']['high_preparation_classification']={'date':'2026-09-23','authorization':'사용자 요청: 중학교처럼 분류해줘',
        'snapshot':snapshot.relative_to(ROOT).as_posix(),'snapshot_sha256':sha(snapshot),'record_count':414,
        'with_preparation_text':238,'without_preparation_text':176,'item_occurrences':dict(counts),'unique_item_count':len(catalog),
        'policy':'기존 중학교 품목 분류·사용자 결정 우선. 명시된 준비물만 분류하며 원문·규격·농도·수량은 보존. 안내문은 비항목으로 기록.'}
    result['metadata']['preparation_classification']['scope']='중학교 862개 기존 분류와 고1 414개 후속 분류. 고1 통계·근거는 high_preparation_classification 참고.'
    assert current==before or current==result,'Subsequent edits detected; refusing overwrite'
    write(TARGET,result);write(REVIEW/'catalogue.json',list(catalog.values()))
    report={'status':'passed','before_sha256':sha(snapshot),'output_sha256':sha(TARGET),'record_count':1276,'classified_high':414,
        'with_preparation_text':238,'without_preparation_text':176,'item_occurrences':dict(counts),'unique_items':len(catalog),
        'manifest_sha256':{n:sha(REVIEW/f'{n}.json') for n in ['miraen_jihaksa','chunjae','visang_donga']}}
    write(HISTORY/'application.json',report);write(OUT/'validation.json',report);print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
