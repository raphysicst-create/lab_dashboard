"""Finalize the individually image-reviewed Jihaksa activity candidates."""
import json, pathlib, hashlib, re, collections
from build_jihaksa import BASE, RAW, FILES

CORRECTIONS={
 (1,126):'동시 낙하 실험 장치\n쇠구슬 2개(지름 약 1.5 cm)\n스마트 기기\n우드락\n검은색 배경의 모눈종이(간격 2 cm)',
 (2,42):'알루미늄(Al) 판\n염화 구리(II)(CuCl₂) 수용액\n접착용 필름\n페트리 접시\n가위\n실험복\n보안경\n실험용 장갑',
 (2,50):'묽은 염산\n수산화 나트륨(NaOH) 수용액\nBTB 용액\n15 mL 눈금 시험관 7개\n시험관대\n디지털 온도계\n스포이트\n실험복\n보안경\n실험용 장갑',
 (2,58):'산화 칼슘 발열 팩 50 g\n물\n메추리알\n모둠별로 결정한 재료\n스마트 기기\n실험복\n보안경\n면장갑',
 (2,107):'에나멜선(지름 0.2 mm)\n원통형 네오디뮴 자석\n4개(지름 15 mm,\n높이 5 mm)\n나무 막대\n빨간색 발광 다이오드\n페트병 (지름 3 cm)\n빨대\n집게 달린 전선 2개\n글루건\n칼이나 사포\n면장갑',
}
CONT={1:{30,58,70,86,126,134,146},2:{22,26,50,58,82,86,92,134,140,150}}
def chapter(v,p):
    if v==1:
        return 'Ⅰ. 과학의 기초' if p<44 else 'Ⅱ. 물질과 규칙성' if p<100 else 'Ⅲ. 시스템과 상호작용'
    return 'Ⅰ. 변화와 다양성' if p<68 else 'Ⅱ. 환경과 에너지' if p<126 else 'Ⅲ. 과학과 미래 사회'
def section(v,p):
    ranges=([(16,'1. 자연 세계의 이해'),(48,'1. 원소의 형성'),(66,'2. 물질의 구조와 성질'),(104,'1. 지구시스템'),(124,'2. 역학적 시스템'),(142,'3. 생명 시스템')] if v==1 else [(16,'1. 생물다양성'),(38,'2. 화학 반응의 다양성'),(72,'1. 생태계와 환경'),(100,'2. 에너지와 지속가능한 발전'),(130,'1. 과학과 인간')])
    return next(name for start,name in reversed(ranges) if p>=start)
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for v in [1,2]:
    out=BASE/f'IS{v}'
    ps=json.loads((out/'scratch/pages.json').read_text(encoding='utf8'))
    cs=json.loads((out/'scratch/candidates.json').read_text(encoding='utf8'))
    if v==2:
        # Independently found in the student reading page; six explicit project steps.
        cs.append({'pdf_page':153,'type':'과학과 기술 · 프로젝트','title':'과학관 탐방 프로젝트','title_bbox':[154.9097,272.6191,228.0866,282.1238],'supplies':None,'supplies_bbox':None})
        cs.sort(key=lambda c:c['pdf_page'])
    data=[];bid=f'jihaksa_IS{v}'
    for i,c in enumerate(cs,1):
        n=c['pdf_page']; pp=[n,n+1] if n in CONT[v] else [n]
        supplies=CORRECTIONS.get((v,n),c['supplies'])
        notes=[]
        if supplies is None:notes.append('학생 본문에 명시된 준비물 목록 없음. 절차·삽화·교사용 자료로 추정하지 않음.')
        if (v,n) in CORRECTIONS:notes.append('원본 렌더 이미지 대조로 준비물 순서·화학식 첨자·항목 경계를 교정함. 자동 후보 원문은 별도 보존.')
        if (v,n)==(1,70):notes.append('71쪽 분홍색 예시 답안의 리튬·나트륨·칼륨 등 목록은 교사용 예시이므로 제외.')
        if (v,n)==(1,156):notes.append('비즈와 실은 절차·삽화에 나타나지만 명시 준비물 목록은 없어 null.')
        if (v,n)==(2,153):notes.append('독립 교차 검토에서 발견. 학생 본문에 별도 프로젝트 제목과 목표 설정·선정·계획서 작성·평가 계획 등 6단계 수행이 명시되어 포함. 일반 읽을거리 말미 질문과 구별.')
        source={'book_id':bid,'pdf_pages':pp,'printed_pages':pp,'activity_type':c['type'],'chapter_label':chapter(v,n).split('.')[0],'section_title':section(v,n),'title_quote':c['title'],'supplies_quote':('준비물\n'+supplies) if supplies else None,'standard_quote':None,'review_notes':notes,'title_bbox':c['title_bbox'],'supplies_bbox':c['supplies_bbox'],'visual_review':{'title':True,'supplies':supplies is not None},'raw_extraction':{'title':c['title'],'supplies_candidate':c['supplies']}}
        if (v,n)==(2,107):source['supplies_bbox']=[344.7,196.0,418,336.4]
        if (v,n)==(2,42):source['supplies_bbox']=[295.6,403.1,523,435]
        if (v,n)==(2,58):source['supplies_bbox']=[295.6,178.3,547,211]
        data.append({'id':f'jihaksa_is{v}_{i:04}','source_row':None,'단원명':chapter(v,n),'성취기준':None,'출판사':'지학사','쪽':n,'탐구활동':re.sub(r'\s+',' ',c['title']).strip(),'교구':supplies,'교과서':f'통합과학 {v}','대표저자':'전상학','source':source})
    sha=hashlib.sha256((RAW/FILES[v-1]).read_bytes()).hexdigest()
    metadata={'schema_version':'1.0','book_id':bid,'publisher':'지학사','author':'전상학','title':f'통합과학 {v}','volume':v,'school_level':'고등학교','grade':None,'source_file':str(RAW/FILES[v-1]),'sha256':sha,'pdf_page_count':len(ps),'record_count':len(data),'identity_evidence':{'pdf_page':180 if v==1 else 170,'quote':'지은이  전상학 외 12명 / 발행인  (주)지학사','visual_reviewed':True},'extraction_policy':{'included':'학생 본문의 해 보기, 탐구 활동, 창의융합, 토의·토론과 논술, 명시된 독립 프로젝트','excluded':'도입 질문, 평가, 일반 읽을거리, 목차 및 교사용 반복/추가 활동, 예시 답안','supplies':'학생 본문 명시 목록만 보존, 미기재는 null','standards':'개별 활동과 직접 연결된 원문 근거가 없으므로 null'},'notes':['본문 활동 구간은 PDF쪽과 인쇄쪽이 같음. 같은 페이지의 숨은 이전 쪽 번호 텍스트는 채택하지 않음.','전체 페이지 텍스트·좌표 조사; 모든 포함 활동 제목과 명시 준비물 영역, 모든 연속 지면 이미지를 확인. 전체 페이지 모든 픽셀의 전수 판독은 아님.','원문 체크박스 항목은 줄바꿈으로 분리하고 표제·목록 원문은 source에 보존.']}
    save(out/'activities.json',{'metadata':metadata,'data':data})
    visual=sorted({p for r in data for p in r['source']['pdf_pages']}|{180 if v==1 else 170})
    cov=[]
    for p in ps:
        n=p['pdf_page'];rows=[r for r in data if n in r['source']['pdf_pages']]
        decision='included' if any(n==r['source']['pdf_pages'][0] for r in rows) else 'continuation' if rows else 'excluded'
        reason='학생 본문의 독립 수행 활동' if decision=='included' else '앞쪽 탐구 활동의 연속 지면' if rows else '표지·목차·활용법·안전 안내·판권·부록' if n<12 or n>(163 if v==1 else 159) else '본문 개념 설명·도입·평가·읽을거리 또는 교사용 지도 계획/주석. 대상 독립 활동 제목 없음.'
        cov.append({'pdf_page':n,'printed_page':n if 12<=n<=(178 if v==1 else 169) else None,'record_ids':[r['id'] for r in rows],'decision':decision,'reason':reason})
    save(out/'coverage.json',{'book_id':bid,'source_file':str(RAW/FILES[v-1]),'sha256':sha,'pdf_page_count':len(ps),'visual_reviewed_pages':visual,'visual_review_scope':'포함 활동 제목/준비물 영역, 연속 지면, 판권. 영역 검토와 전면 검토 혼합.','pages':cov})
    nulls=sum(r['교구'] is None for r in data);counts=collections.Counter(r['source']['activity_type'] for r in data)
    (out/'extraction_report.md').write_text(f'# 지학사 통합과학 {v} 추출 보고\n\n- 전상학 외 12명, (주)지학사: 판권 PDF {180 if v==1 else 170}쪽 이미지 확인.\n- PDF {len(ps)}쪽 텍스트·좌표 조사, 활동 {len(data)}개. 준비물 명시 {len(data)-nulls}개, 미기재 null {nulls}개.\n- 유형: {dict(counts)}.\n- 제목·준비물 영역 및 연속 지면 검토: {visual}. 포함 활동의 제목과 존재하는 준비물 목록은 전부 이미지 대조. 모든 PDF 픽셀을 전수 판독한 것은 아님.\n- 본문 PDF/인쇄 쪽 일치. 교사용 숨은 과거 페이지 번호가 일부 겹쳐 있어 실제 하단 인쇄 번호를 사용.\n- 성취기준은 활동별 직접 연결 근거가 없어 모두 null. 원제목을 보존하고 검색용 제목은 연속 공백/줄바꿈만 정리.\n- 중단원·대단원 도입 질문, 일반 문제와 평가, 과학과 생활/직업 등 일반 읽을거리, 교사 추가 질문과 분홍색 예시 답안 제외.\n- 2권 153쪽 과학관 탐방 프로젝트는 읽을거리 지면 안의 별도 제목 및 6단계 학생 수행으로 확인하여 포함.\n- 준비물은 원문 체크박스 목록만. 예시 답안이나 절차에서 도구를 유추하지 않음.\n- 수동 교정: 1권 126쪽 목록의 위치 순서; 2권 42쪽 화학식 첨자로 누락된 염화 구리(II)(CuCl₂) 수용액 및 활동 표제 혼입; 50쪽 목록 순서; 58쪽 조사하기 표제 혼입; 107쪽 길게 이어진 목록의 칼이나 사포·면장갑 누락을 이미지에서 교정. 후보 원문은 source.raw_extraction에 보존.\n- 출력은 기존 중학교 원자료·공개 사이트와 별도.\n',encoding='utf8')
    print(bid,len(data),nulls)
