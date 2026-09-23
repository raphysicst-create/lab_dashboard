"""Validate and combine ten reviewed high-school Integrated Science books.

This is a structural/source-traceability validator, not an activity detector.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import pathlib
import re
from datetime import datetime, timezone
import fitz

ROOT=pathlib.Path(__file__).resolve().parents[2]
DEFAULT=ROOT/'outputs/extraction/integrated-science-20260923'
PUBLISHERS={'miraen':('미래엔','오현선'),'jihaksa':('지학사','전상학'),'chunjae':('천재교과서','신영준'),'visang':('비상교육','심규철'),'donga':('동아출판','김호련')}
FIELDS=['단원명','성취기준','출판사','쪽','탐구활동','교구']

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def write(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=pathlib.Path,default=DEFAULT)
    ap.add_argument('--source-dir',type=pathlib.Path)
    args=ap.parse_args();out=args.output
    errors=[];warnings=[];books=[];data=[];ids=set();checks=[]
    inventory={r['code']:r for r in read(out/'achievement_mapping/standards_inventory.json')['standards']}
    mappings={r['record_id']:r for pub in PUBLISHERS for r in read(out/f'achievement_mapping/{pub}.json')['mappings']}
    def require(condition,message):
        if not condition:errors.append(message)
    for slug,(publisher,author) in PUBLISHERS.items():
        for volume in [1,2]:
            bid=f'{slug}_IS{volume}';folder=out/slug/f'IS{volume}'
            try:d=read(folder/'activities.json');cov=read(folder/'coverage.json')
            except (OSError,ValueError) as e:errors.append(f'{bid}: input unavailable: {e}');continue
            m=d['metadata'];rows=d['data'];pages=m['pdf_page_count']
            require(m['book_id']==bid,f'{bid}: metadata book id')
            require(m['publisher']==publisher and m['author']==author,f'{bid}: publisher/author')
            require(m['volume']==volume and m['school_level']=='고등학교' and m['grade']==1,f'{bid}: book volume/school level/grade')
            require(len(rows)==m['record_count'] and len(rows)>0,f'{bid}: record count')
            src=pathlib.Path(m['source_file'])
            if args.source_dir:src=args.source_dir/src.name
            actual_hash=digest(src) if src.is_file() else None
            require(actual_hash==m['sha256'],f'{bid}: source SHA-256 differs or source missing: {src}')
            if src.is_file():
                with fitz.open(src) as pdf:require(len(pdf)==pages,f'{bid}: actual PDF page count differs')
            require(cov['book_id']==bid and cov['pdf_page_count']==pages,f'{bid}: coverage book/page count')
            cmap={p['pdf_page']:p for p in cov['pages']}
            require(len(cov['pages'])==pages and set(cmap)==set(range(1,pages+1)),f'{bid}: coverage must contain each PDF page once')
            visual=set(cov['visual_reviewed_pages'])
            require(bool(visual) and all(type(p) is int and 1<=p<=pages for p in visual),f'{bid}: visual page range')
            local_ids={r['id'] for r in rows};reverse=collections.defaultdict(set);standard_reverse=collections.defaultdict(set);duplicate_keys=set()
            for r in rows:
                rid=r['id'];s=r['source']
                require(rid not in ids,f'{bid}: duplicate id {rid}');ids.add(rid)
                require(all(f in r for f in FIELDS),f'{rid}: missing original column')
                require(r['source_row'] is None,f'{rid}: fabricated Excel source row')
                require(r.get('학년')==1 and r.get('학교급')=='고등학교' and r.get('학년표시')=='고1',f'{rid}: user-assigned high-school grade')
                mapping=mappings.get(rid,{})
                codes=mapping.get('codes',[])
                require(s.get('standard_mapping')==mapping and bool(mapping),f'{rid}: reviewed mapping differs')
                require(r.get('성취기준코드')==codes and r['성취기준']==('\n'.join(f'[{c}]' for c in codes) or None),f'{rid}: achievement code fields differ')
                require(r.get('성취기준내용')==[{'code':c,'text':inventory[c]['text']} for c in codes],f'{rid}: achievement text differs from inventory')
                require(r['출판사']==publisher and r['대표저자']==author,f'{rid}: publisher/author differs')
                require(isinstance(r['교과서'],str) and str(volume) in r['교과서'],f'{rid}: book title')
                require(isinstance(r['탐구활동'],str) and bool(r['탐구활동'].strip()),f'{rid}: empty activity title')
                for f in ['단원명','성취기준','교구']:
                    require(r[f] is None or isinstance(r[f],str) and bool(r[f].strip()),f'{rid}: {f} must be nonempty string or null')
                    require(r[f] not in ['미확인','없음','해당 없음','N/A','null',''],f'{rid}: use null instead of placeholder for {f}')
                require(r['쪽'] is None or type(r['쪽']) is int and r['쪽']>0,f'{rid}: printed page')
                require(s['book_id']==bid,f'{rid}: source book')
                pp=s['pdf_pages'];ip=s['printed_pages']
                require(bool(pp) and pp==sorted(set(pp)) and all(type(p) is int and 1<=p<=pages for p in pp),f'{rid}: PDF page range/order')
                require(isinstance(ip,list) and all(type(p) is int and p>0 for p in ip),f'{rid}: printed pages')
                require(r['쪽'] is None or bool(ip) and r['쪽']==ip[0],f'{rid}: first printed page differs')
                require(isinstance(s['title_quote'],str) and s['title_quote'].strip(),f'{rid}: title evidence')
                require(isinstance(s['activity_type'],str) and s['activity_type'].strip(),f'{rid}: activity type')
                require(isinstance(s['review_notes'],list),f'{rid}: review notes type')
                require((r['교구'] is None)==(s['supplies_quote'] is None),f'{rid}: supplies/evidence null mismatch')
                require(r['성취기준'] is None or bool(s['standard_quote']),f'{rid}: standard has no evidence')
                if s.get('standard_evidence'):
                    ev=s.get('standard_evidence',{})
                    ep=ev.get('pdf_page')
                    require(type(ep) is int and 1<=ep<=pages,f'{rid}: standard evidence page')
                    require(ep in visual,f'{rid}: standard evidence has no recorded image review')
                    require(all(c in s['standard_quote'] for c in codes),f'{rid}: standard code absent from quote')
                    standard_reverse[ep].add(rid)
                require(pp[0] in visual,f'{rid}: title page has no recorded image review')
                key=(r['쪽'],re.sub(r'\s+','',r['탐구활동']))
                require(key not in duplicate_keys,f'{rid}: repeated same title on same page');duplicate_keys.add(key)
                for f in ['탐구활동','교구','단원명']:
                    val=r[f] or ''
                    require(not any((ord(c)<32 and c not in '\n\r\t') or 0xE000<=ord(c)<=0xF8FF or c=='\ufffd' for c in val),f'{rid}: undecoded/control glyph in {f}')
                for p in pp:reverse[p].add(rid)
            for p in cov['pages']:
                n=p['pdf_page'];refs=p['record_ids']
                require(set(refs)<=local_ids,f'{bid} page {n}: unknown record')
                require(set(refs)==reverse[n] and len(refs)==len(set(refs)),f'{bid} page {n}: coverage reverse links')
                require(p['decision'] in ['included','continuation','excluded'],f'{bid} page {n}: decision')
                require((p['decision']=='excluded')==(not refs),f'{bid} page {n}: excluded/record mismatch')
                require(bool(p.get('reason')),f'{bid} page {n}: reason missing')
                require(set(p.get('standard_evidence_record_ids',[]))==standard_reverse[n],f'{bid} page {n}: standard evidence reverse links')
            books.append(m);data.extend(rows)
            checks.append({'book_id':bid,'source_sha256':actual_hash,'activity_file_sha256':digest(folder/'activities.json'),'pdf_pages':pages,'records':len(rows),'supplies_present':sum(r['교구'] is not None for r in rows),'supplies_null':sum(r['교구'] is None for r in rows),'visual_reviewed_page_count':len(visual),'activity_types':dict(collections.Counter(r['source']['activity_type'] for r in rows))})
    baseline=read(out/'baseline.json')
    updates_path=out/'protected_original_updates.json'
    updates=read(updates_path) if updates_path.is_file() else {}
    require(set(updates)<=set(baseline),'Protected update references unknown file')
    original_unchanged=True
    for name,sha in baseline.items():
        actual=digest(ROOT/name);original_unchanged=original_unchanged and actual==sha
        update=updates.get(name)
        if update:
            require(update['original_sha256']==sha and bool(update['commit']) and bool(update['reason']),f'Invalid protected update record: {name}')
            expected=update['expected_sha256']
            if update.get('subsequent_application'):
                applied=read(ROOT/update['subsequent_application'])
                require(applied['before_sha256']==expected,f'Invalid protected application baseline: {name}')
                expected=applied['output_sha256']
            require(actual==expected,f'Protected current version changed: {name}')
            warnings.append(f"Separate committed update preserved: {name} ({update['commit']})")
        else:require(actual==sha,f'Protected original changed: {name}')
    references=out/'parent_review/reference_checks.json'
    reference_count=0
    if references.is_file():
        def norm(s):return re.sub(r'\s+','',s or '')
        for check in read(references)['checks']:
            matches=[r for r in data if r['source']['book_id']==check['book_id'] and r['쪽']==check['printed_page'] and norm(r['탐구활동'])==norm(check['title'])]
            require(len(matches)==1,f'Independent reference not found: {check["book_id"]} p{check["printed_page"]} {check["title"]}')
            if len(matches)!=1:continue
            r=matches[0];supply=norm(r['교구'])
            for fragment in check.get('supplies_include',[]):require(norm(fragment) in supply,f'{r["id"]}: reference supply missing {fragment}')
            for fragment in check.get('supplies_exclude',[]):require(norm(fragment) not in supply,f'{r["id"]}: teacher/other content mixed in {fragment}')
            if 'supplies_exact' in check:require(supply==norm(check['supplies_exact']),f'{r["id"]}: reference supply differs')
            reference_count+=1
    else:errors.append('Independent reference_checks.json unavailable')
    require(len(books)==10,'Expected all ten books')
    report={'checked_at':datetime.now(timezone.utc).isoformat(),'passed':not errors,'errors':errors,'warnings':warnings,'books':checks,'record_count':len(data),'independent_reference_checks':reference_count,'protected_originals_unchanged':original_unchanged,'protected_current_versions_preserved':not any(e.startswith(('Protected','Invalid protected')) for e in errors),'protected_update_history':updates,'scope':'Structure, source SHA-256, actual PDF page counts, unique IDs, evidence fields, page coverage, reverse references, recorded image review, independent image reference checks, user grade and reviewed mapping application. Semantic/source quotation checks are recorded in achievement_mapping/validation.json; does not certify every source pixel or official publisher assignment for content alignments.'}
    if not errors:
        combined={'metadata':{'schema_version':'1.0','title':'통합과학 1·2 탐구·해보기 활동 및 준비물 (5개 출판사)','record_count':len(data),'book_count':10,'school_level':'고등학교','grade':1,'grade_label':'고1','achievement_standard_catalog':list(inventory.values()),'achievement_mapping_counts':dict(collections.Counter(r['source']['standard_mapping']['method'] for r in data)),'source_books':books,'original_columns':FIELDS,'missing_value_counts':{f:sum(r[f] is None for r in data) for f in FIELDS},'notes':['기존 중학교 원자료와 별도로 추출한 고등학교 통합과학 자료.','통합과학 1·2는 권수이며 사용자 지정으로 두 권 모두 고1이다.','학생 본문의 제목 있는 독립 수행 활동을 포함. 출판사별 탐구/해보기 외 수행 활동 유형은 source.activity_type과 권별 보고서 참고.','명시되지 않은 준비물은 null. 준비물은 절차·삽화·교사 예시로 추정하지 않음. 성취기준은 직접 연결과 활동 내용 대조를 구분하고, 연결 근거가 부족한 경우 null.','쪽은 교과서 인쇄 쪽, source.pdf_pages는 1부터 시작하는 PDF 쪽.','교구의 줄바꿈은 원자료 목록의 줄바꿈이며 개별 물품 구분자로 단순 해석하지 말 것.','제목과 준비물 근거·추출 한계는 source와 권별 coverage/extraction_report에 보존.','원문 자료 보존용 결과이며 사이트 데이터로 자동 반영하지 않음.']},'data':data,'views':{'기본자료':{'record_count':len(data),'record_ids':[r['id'] for r in data]},'교과서별 활동':{b['book_id']:{'record_count':b['record_count'],'record_ids':[r['id'] for r in data if r['source']['book_id']==b['book_id']]} for b in books}}}
        target=out/'science_experiment_supplies_integrated_science.json';write(target,combined)
        report['combined_sha256']=digest(target)
    write(out/'validation.json',report)
    print(json.dumps({'passed':not errors,'record_count':len(data),'errors':errors,'books':checks},ensure_ascii=False,indent=2))
    return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
