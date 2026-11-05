"""Apply reviewed high-school grade and achievement mappings, preserving activity originals.

The mappings are human/agent source comparisons, not a keyword classifier.
Use --check to validate inputs without rewriting activities.
"""
from __future__ import annotations
import argparse,collections,copy,hashlib,json,re,unicodedata
from pathlib import Path
from datetime import datetime,timezone
import fitz

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/extraction/integrated-science-20260923'
MAP=BASE/'achievement_mapping'
PUBS=['miraen','jihaksa','chunjae','visang','donga']
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return ''.join(c for c in s if not c.isspace() and unicodedata.category(c) not in ['Cf','Cc'])
def quote_matches(quote,text):
    parts=re.split(r'\[\s*…\s*\]',quote)
    return all(norm(p) and norm(p) in norm(text) for p in parts)

def inspect():
    errors=[];rows={};books={};current={};mappings={};proof=[]
    def req(ok,msg):
        if not ok:errors.append(msg)
    inv=read(MAP/'standards_inventory.json');catalog={s['code']:s for s in inv['standards']}
    req(len(catalog)==31,'Expected 31 distinct Integrated Science standards')
    for rel,digest in read(MAP/'baseline.json').items():
        req(sha(MAP/'before_mapping'/rel)==digest,f'Backup hash changed: {rel}')
    for pub in PUBS:
        for v in [1,2]:
            rel=f'{pub}/IS{v}/activities.json';book=read(MAP/'before_mapping'/rel)
            books[book['metadata']['book_id']]=book
            current[book['metadata']['book_id']]=read(BASE/rel)
            for r in book['data']:rows[r['id']]=r
        path=MAP/f'{pub}.json'
        if not path.exists():errors.append(f'Missing mapping: {pub}');continue
        for m in read(path)['mappings']:
            rid=m['record_id'];req(rid not in mappings,f'Duplicate mapping: {rid}');mappings[rid]=m
    req(set(rows)==set(mappings),'Mapping record IDs must cover all 415 activities exactly')
    docs={};texts={}
    def page(bid,n):
        if bid not in books or type(n) is not int or not 1<=n<=books[bid]['metadata']['pdf_page_count']:
            errors.append(f'Invalid evidence page: {bid} {n}');return ''
        if bid not in docs:docs[bid]=fitz.open(books[bid]['metadata']['source_file'])
        if (bid,n) not in texts:texts[bid,n]=docs[bid][n-1].get_text()
        return texts[bid,n]
    for code,s in catalog.items():
        ev=s['source'];q=ev['quote'];t=page(ev['book_id'],ev['pdf_page'])
        req(code in q and norm(q) in norm(t),f'Inventory quote missing from source: {code}')
        req(norm(s['text']) in norm(q),f'Inventory text differs from quote: {code}')
    for rid,m in mappings.items():
        if rid not in rows:continue
        r=rows[rid];codes=m['codes'];method=m['method'];bid=r['source']['book_id']
        req(isinstance(codes,list) and len(codes)==len(set(codes)) and set(codes)<=set(catalog),f'{rid}: invalid codes')
        req(method in ['direct','content_alignment','unresolved'],f'{rid}: invalid mapping method')
        req((method=='unresolved')==(not codes),f'{rid}: unresolved/codes mismatch')
        req(bool(m['rationale'].strip()),f'{rid}: rationale required')
        ae=m['activity_evidence'];t='\n'.join(page(bid,n) for n in ae['pdf_pages'])
        req(bool(ae['quote'].strip()),f'{rid}: activity quote required')
        match=quote_matches(ae['quote'],t)
        if not match:
            # Only explicit recorded visual transcriptions can bypass a broken PDF text layer.
            req(ae.get('verification')=='image_transcription',f'{rid}: activity quote not found in cited pages')
            req(all((MAP/'images'/f'{bid}_{n}.png').is_file() for n in ae['pdf_pages']),f'{rid}: image transcription proof missing')
        proof.append({'record_id':rid,'activity_quote_verification':'pdf_text' if match else 'image_transcription','codes':codes,'method':method})
        se=m['standard_evidence'];req({e['code'] for e in se}==set(codes),f'{rid}: code evidence incomplete')
        for ev in se:
            t=page(ev['book_id'],ev['pdf_page'])
            req(ev['code'] in ev['quote'] and quote_matches(ev['quote'],t),f'{rid}: standard evidence quote differs from source')
        if method=='direct':
            image_proof=any(e.get('verification')=='image_reviewed' and norm(r['탐구활동']) in norm(e['quote']) and (MAP/'images'/f"{e['book_id']}_{e['pdf_page']}.png").is_file() for e in se)
            req(bool(r['source'].get('standard_evidence')) or image_proof,f'{rid}: direct assignment lacks explicit activity table proof')
    for doc in docs.values():doc.close()
    # Only the grade and achievement fields may change; one independently found continuation is documented.
    for bid,book in current.items():
        for r in book['data']:
            orig=rows.get(r['id'])
            if not orig:errors.append(f'Unknown current activity: {r["id"]}');continue
            for field in ['id','source_row','단원명','출판사','쪽','탐구활동','교구','교과서','대표저자']:
                req(r[field]==orig[field],f'{r["id"]}: protected activity field changed: {field}')
            for field in ['title_quote','supplies_quote']:
                req(r['source'][field]==orig['source'][field],f'{r["id"]}: protected source quote changed: {field}')
    return errors,books,mappings,catalog,proof

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--check',action='store_true');args=ap.parse_args()
    errors,books,mappings,catalog,proof=inspect()
    if errors:
        write(MAP/'validation.json',{'passed':False,'errors':errors,'checked_at':datetime.now(timezone.utc).isoformat()})
        print(json.dumps({'passed':False,'errors':errors},ensure_ascii=False,indent=2));return 1
    if not args.check:
        for bid,original in books.items():
            b=copy.deepcopy(original);m=b['metadata'];m['grade']=1;m['grade_label']='고1';m['grade_basis']='사용자 지정: 통합과학 1·2 모두 고1 (2026-09-23)'
            m['achievement_mapping']={'source':'achievement_mapping/standards_inventory.json','policy':'교과서 직접 연결 및 활동 내용·단원 대조 연결. 판단 근거는 source.standard_mapping에 보존.','mapped_count':sum(bool(mappings[r['id']]['codes']) for r in b['data'])}
            m['notes']=[('초기 추출 시점의 기록(후속 매핑 전): '+n) if '건만 성취기준을 기록' in n else n for n in m.get('notes',[])]
            if isinstance(m.get('extraction_policy'),dict):m['extraction_policy']['standards']='2026-09-23 후속 연결 반영. 교과서 표 직접 연결과 활동 내용 대조 연결을 구분하여 source.standard_mapping에 보존.'
            for r in b['data']:
                mp=copy.deepcopy(mappings[r['id']]);codes=mp['codes'];s=r['source']
                r['학교급']='고등학교';r['학년']=1;r['학년표시']='고1'
                r['성취기준']='\n'.join(f'[{c}]' for c in codes) or None
                r['성취기준코드']=codes;r['성취기준내용']=[{'code':c,'text':catalog[c]['text']} for c in codes]
                s['standard_mapping']=mp;s['original_standard_quote']=s['standard_quote']
                s['standard_quote']='\n\n'.join(e['quote'] for e in mp['standard_evidence']) or None
                s['original_review_notes']=s['review_notes']
                s['review_notes']=[n for n in s['review_notes'] if '성취기준' not in n]
                s['review_notes'].append('성취기준은 2026-09-23 후속 매핑 반영. 직접/내용 대조/미확인 구분과 근거는 source.standard_mapping 참고.')
                if r['id']=='jihaksa_is1_0016':
                    s['pdf_pages']=[72,73];s['printed_pages']=[72,73]
                    s['review_notes'].append('성취기준 대조 중 원본 이미지에서 73쪽 학생 활동·정리 문항이 이어짐을 확인해 연속 쪽을 보완.')
            pub,vol=bid.split('_');rel=Path(pub)/vol
            write(BASE/rel/'activities.json',b)
            cov=read(MAP/'before_mapping'/rel/'coverage.json')
            if bid=='jihaksa_IS1':
                p=cov['pages'][72];p.update({'record_ids':['jihaksa_is1_0016'],'decision':'continuation','reason':'72쪽 원자의 전자배치와 주기율표 활동의 학생 수행·정리가 이어짐. 2026-09-23 후속 이미지 확인.'})
                cov['visual_reviewed_pages']=sorted(set(cov['visual_reviewed_pages'])|{73})
            write(BASE/rel/'coverage.json',cov)
    unresolved=[{'record_id':rid,'reason':m['rationale'],'review_note':m['review_note']} for rid,m in mappings.items() if not m['codes']]
    counts=dict(collections.Counter(m['method'] for m in mappings.values()))
    report={'passed':True,'checked_at':datetime.now(timezone.utc).isoformat(),'errors':[],'activity_count':len(mappings),'grade':'고1','standard_count':len(catalog),'mapping_counts':counts,'mapped_count':len(mappings)-len(unresolved),'unresolved_count':len(unresolved),'code_links':sum(len(m['codes']) for m in mappings.values()),'cross_volume_count':sum(any(f'10통과{rid.lower().split("_is")[1][0]}-' not in c for c in m['codes']) for rid,m in mappings.items()),'source_verification':proof,'limits':'Codes and quotations checked against textbook_wiki PDFs; semantic mappings are reviewed content alignments, not a claim of publisher-assigned official activity labels. Some are partial/supporting connections.','protected_fields':'Original activity IDs/titles/chapters/publishers/pages/supplies and title/supplies quotes remain unchanged. One continuation range extended: jihaksa_is1_0016 to pp72–73.'}
    write(MAP/'validation.json',report);write(MAP/'review_needed.json',unresolved)
    print(json.dumps({k:v for k,v in report.items() if k!='source_verification'},ensure_ascii=False,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
