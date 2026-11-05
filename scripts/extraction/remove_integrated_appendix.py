"""Remove the user-excluded Integrated Science 2 appendix from active data."""
import copy, hashlib, json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/extraction/combined-20260922'
TARGET=OUT/'science_experiment_supplies_combined.json'
HISTORY=OUT/'decision_history/20260923-remove-appendix'
REMOVED_ID='donga_IS2_045'
def read(p):return json.loads(p.read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    HISTORY.mkdir(parents=True,exist_ok=True);snapshot=HISTORY/TARGET.name;current=read(TARGET)
    if not snapshot.exists():
        assert len(current['data'])==1277 and 'appendix_removal' not in current['metadata']
        snapshot.write_bytes(TARGET.read_bytes())
        (HISTORY/'public-activities.json').write_bytes((ROOT/'site/dist/data/activities.json').read_bytes())
    before=read(snapshot);result=copy.deepcopy(before)
    removed=[r for r in result['data'] if r['id']==REMOVED_ID]
    assert len(removed)==1 and removed[0]['단원 ID']=='high-2-appendix'
    result['data']=[r for r in result['data'] if r['id']!=REMOVED_ID]
    result['units']=[u for u in result['units'] if u['id']!='high-2-appendix']
    for view in result['views'].values():
        if 'record_ids' in view and REMOVED_ID in view['record_ids']:
            view['record_ids'].remove(REMOVED_ID);view['record_count']=len(view['record_ids'])
    m=result['metadata'];m['record_count']=1276;m['publisher_counts']=dict(Counter(r['출판사'] for r in result['data']))
    m['missing_value_counts']={f:sum(r[f] is None for r in result['data']) for f in m['original_columns']}
    m['unit_normalization']['unit_count']=29
    m['integrated_science']['activities']=414;m['integrated_science']['mapping_counts']['unresolved']=3
    ds=m['source_datasets'][-1];ds['record_count']=414;ds['record_index_range_zero_based']=[862,1275]
    m['appendix_removal']={'date':'2026-09-23','reason':'사용자 요청: 고1 통합과학2 부록 없애줘','excluded_ids':[REMOVED_ID],
        'snapshot':snapshot.relative_to(ROOT).as_posix(),'snapshot_sha256':sha(snapshot),'original_extraction_preserved':True}
    assert current==before or current==result,'Subsequent edits detected; refusing overwrite'
    write(TARGET,result);write(HISTORY/'removed_records.json',removed)
    report={'status':'passed','before_sha256':sha(snapshot),'output_sha256':sha(TARGET),'record_count':1276,'high_school_count':414,'unit_count':29,'removed_ids':[REMOVED_ID]}
    write(HISTORY/'application.json',report);write(OUT/'validation.json',report);print(json.dumps(report))
if __name__=='__main__':main()
