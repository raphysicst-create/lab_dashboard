"""Append reviewed high-school activities without changing the 862 middle-school rows."""
import copy, hashlib, json, re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'outputs/extraction/combined-20260922'
TARGET = OUT/'science_experiment_supplies_combined.json'
INPUT = ROOT/'outputs/extraction/integrated-science-20260923/science_experiment_supplies_integrated_science.json'
HISTORY = OUT/'decision_history/20260923-integrated-science'
def read(p): return json.loads(p.read_text('utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    HISTORY.mkdir(parents=True,exist_ok=True)
    snapshot=HISTORY/TARGET.name
    current=read(TARGET)
    if not snapshot.exists():
        assert len(current['data'])==862 and 'integrated_science' not in current['metadata']
        snapshot.write_bytes(TARGET.read_bytes())
        (HISTORY/'prior-validation.json').write_bytes((OUT/'validation.json').read_bytes())
        for name in ['activities','achievements','textbooks','materials','chemicals','chemical_guidelines']:
            (HISTORY/f'public-{name}.json').write_bytes((ROOT/f'site/dist/data/{name}.json').read_bytes())
    before=read(snapshot); high=read(INPUT);result=copy.deepcopy(before)
    assert len(high['data'])==415 and high['metadata']['grade']==1
    chapter_names={1:['과학의 기초','물질과 규칙성','시스템과 상호작용'],2:['변화와 다양성','환경과 에너지','과학과 미래 사회']}
    added=[]
    for s in high['metadata']['achievement_standard_catalog']:
        volume,unit,seq=map(int,re.fullmatch(r'10통과(\d)-(\d+)-(\d+)',s['code']).groups())
        added.append({'code':s['code'],'raw_text':s['text'],'display_text':f'{unit}-{seq}. '+s['text'],
          'unit':f'통합과학 {volume} · {unit}. {chapter_names[volume][unit-1]}','unit_number':unit,
          'sequence':seq,'volume':volume,'sort_order':100+volume*10+unit,'school_level':'고등학교','source':s['source']})
    result['achievement_standards'].extend(added);bycode={s['code']:s for s in added}
    for original in high['data']:
        r=copy.deepcopy(original);codes=r['성취기준코드']
        r['성취기준 원문']=r['성취기준'];r['성취기준 코드']=codes or None
        r['성취기준']='\n'.join(bycode[c]['display_text'] for c in codes) or None
        r['성취기준 연결']={'status':r['source']['standard_mapping']['method'],'evidence':r['source']['standard_mapping']}
        r.update({'실험 기자재':None,'실험 준비물':None,'분류 보류':None,'준비물 분류':None,'준비물 표시 방식':'원문'})
        result['data'].append(r)
    ids=[r['id'] for r in result['data']];assert len(ids)==len(set(ids))==1277
    result['views']['기본자료']={'record_count':1277,'record_ids':ids}
    result['views']['통합과학']={'record_count':415,'record_ids':[r['id'] for r in high['data']]}
    result['metadata']['record_count']=1277
    result['metadata']['publisher_counts']=dict(Counter(r['출판사'] for r in result['data']))
    result['metadata']['preparation_classification']['scope']='기존 중학교 862개만 분류 완료. 고1 415개는 원문 표시이며 분류 배열은 null.'
    result['metadata']['source_datasets'].append({'dataset_id':'integrated_science','label':'고1 통합과학 1·2',
        'input_file':INPUT.relative_to(ROOT).as_posix(),'sha256':sha(INPUT),'record_count':415,
        'record_index_range_zero_based':[862,1276],'view':'통합과학','original_metadata':high['metadata']})
    result['metadata']['missing_value_counts']={f:sum(r[f] is None for r in result['data']) for f in result['metadata']['original_columns']}
    result['metadata']['integrated_science']={'applied_date':'2026-09-23','authorization':'사용자 요청: json이랑 사이트에 반영해줘',
        'activities':415,'grade':'고1','mapping_counts':high['metadata']['achievement_mapping_counts'],
        'pre_application_snapshot':snapshot.relative_to(ROOT).as_posix(),'pre_application_sha256':sha(snapshot),
        'materials_policy':'준비물 원문 그대로 표시. 미확인 분류는 null이며 임의 분류하지 않음.'}
    assert result['data'][:862]==before['data']
    assert current==before or current==result,'Subsequent changes detected; refusing overwrite'
    write(TARGET,result)
    report={'status':'passed','record_count':1277,'high_school_count':415,'middle_school_rows_unchanged':True,
        'standard_count':118,'unconfirmed_achievements':42,'output_sha256':sha(TARGET),
        'input_sha256':sha(INPUT),'before_sha256':sha(snapshot),'independent_validation':'output/validation/integrated-site-20260923/data-validation.json'}
    write(HISTORY/'application.json',report);write(OUT/'validation.json',report)
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
