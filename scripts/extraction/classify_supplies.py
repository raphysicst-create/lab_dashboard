"""Classify the merged preparation text, preserving exact spans and pending decisions."""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/extraction/combined-20260922'
TARGET = OUT / 'science_experiment_supplies_combined.json'
BACKUP = OUT / 'science_experiment_supplies_combined.unclassified.json'
DECISIONS = OUT / 'classification_decisions.json'
EQUIPMENT, SUPPLIES, PENDING = '실험 기자재', '실험 준비물', '분류 보류'
FIELDS = [EQUIPMENT, SUPPLIES, PENDING, '준비물 분류']

# These are literal phrases inspected in the input, not inferred missing supplies.
# Commas/newlines inside them describe a single named item or compound phrase.
PROTECTED = {
 'activity_0007': ['폴리에틸렌 테레프탈레이트(PET),저밀도 폴리에틸렌(LDPE), 폴리스티렌(PS) 조각이 섞여 있는 플라스틱 혼합물'],
 'activity_0280': ['화산대, 지진대, 판의 경계 자료(KMZ, KML 파일)'],
 'ybm_k8_0002': ['크기가 다른 알루미늄 조각\n두 개와 철 조각 두 개'],
 'ybm_k8_0040': ['양성자, 중성자, 전자 붙임딱지\n(부록 334  쪽)'],
 'ybm_k8_0055': ['아이오딘－아이오딘화 칼륨\n용액'],
 'ybm_k8_0059': ['바닥에 구멍이 뚫린 투명한\n플라스틱 컵'],
 'ybm_k8_0062': ['영양소, 산소, 이산화 탄소,\n노폐물을 표현할 수 있는 물체'],
 'ybm_k8_0067': ['길이가 다른\n니크롬선 두 개'],
 'ybm_k9_0057': ['모양, 표면의 거칠기, 온도, 소리가 다른 다양한 물건'],
 'ybm_k9_0075': ['대립유전자, 표현형 붙임딱지(부록 310 쪽)'],
}


def norm(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def split_items(row):
    raw = row['교구']
    if raw is None:
        return [], None
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{row['id']}: invalid preparation text")
    protected = []
    for phrase in PROTECTED.get(row['id'], []):
        if raw.count(phrase) != 1:
            raise ValueError(f"{row['id']}: source phrase changed: {phrase!r}")
        start = raw.index(phrase)
        protected.append((start, start+len(phrase)))
    spans, stack, start, errors = [], [], 0, []
    pairs = {')':'(', ']':'[', '）':'（'}
    def append(a,b):
        while a < b and raw[a].isspace(): a += 1
        while b > a and raw[b-1].isspace(): b -= 1
        if a < b: spans.append((a,b))
    for i,ch in enumerate(raw):
        if ch in '([（': stack.append(ch)
        elif ch in ')]）':
            if not stack or stack.pop() != pairs[ch]: errors.append('괄호 짝 불일치')
        elif not stack:
            if any(a <= i < b for a,b in protected): continue
            # A newline before a parenthesis attaches the specification to its item.
            if ch == '\n' and raw[i+1:].lstrip().startswith(('(', '（')): continue
            separator = ch in ',，\n'
            if row['id'] == 'activity_0363':
                separator = separator or ch == '□' or (ch == '.' and raw[i+1:i+2] == ' ')
            if separator:
                append(start,i)
                start=i+1
    if stack: errors.append('닫히지 않은 괄호')
    append(start,len(raw))
    if errors: return [(0,len(raw))], '; '.join(errors)
    return spans, None


def classify(text, parse_error=None):
    n=norm(text)
    # Keep words after parenthesized specs, e.g. 엘이디(LED) 전구.
    head=n
    while re.search(r'\([^()]*\)',head):head=re.sub(r'\([^()]*\)','',head)
    if parse_error:
        return PENDING, '원문 항목 경계 확인 필요: '+parse_error
    # Composite content and unknown choice of materials cannot be decided by substrings.
    if re.search(r'모래가담긴|증류수를넣고얼린|비커\(물\)|원소기호판과붙임딱지|그밖에필요한재료', n):
        return PENDING, '용기·내용물 또는 서로 다른 종류가 한 항목에 함께 적혀 있어 분리 판단 필요'
    if re.search(r'모둠|나만의준비물|설계에따른|선택한물체|표현할수있는물체|다양한물건|제작을위한물품|꾸밈|촬영소품|상황극소품|촬영용소품|그림도구|색칠도구', n):
        return PENDING, '구체적인 구성 물품이 정해져 있지 않거나 혼합되어 있음'
    if re.search(r'프로그램|애플리케이션|앱|KMZ|공유문서', n) and not re.search(r'스마트기기|컴퓨터', n):
        return PENDING, '소프트웨어·디지털 자료를 기자재에 포함할지 사용자 판단 필요'
    if '감지기전용방수천' in n:
        return PENDING, '센서 자체가 아닌 방수 천이며 소모·재사용 여부 확인 필요'
    # Explicit user examples take precedence, including all named glove variants.
    if re.search(r'비커|시험관|스마트기기|눈금실린더|핀셋|전자저울|장갑|보안경|실험복|유리병|약숟가락', head):
        return EQUIPMENT, '사용자가 지정한 기자재 또는 그 규격·형태 변형'
    if re.search(r'일회용', n):
        return SUPPLIES, '원문에 일회용으로 명시된 물품'
    if '영구표본' in head:
        return EQUIPMENT, '반복 관찰하도록 보존된 영구표본'
    if '또는아크릴' in n:
        return PENDING, '대체 재료의 재질·가공·재사용 여부 확인 필요'
    if head=='사포':
        return PENDING, '사용하면서 닳는 재료이지만 반복 사용할 수도 있어 사용자 판단 필요'
    if re.search(r'종이찍개|감압용기|밀폐용기|센서전용투명용기|질량측정용기|가열할수있는다른종류의용기|바이오챔버|LED등|엘이디등|적외선등|고정막대|고정핀|고리나사못|흡착판|태양투영판|태양광선차단판|니크롬선저항판|실리콘관|실리콘튜브|고무관|고무링|대류관|Y자관|자전극',head) or head in {'마개','동전','압정','침핀'}:
        return EQUIPMENT, '반복 사용하는 실험 용기·부품·교구'
    if re.search(r'붙임딱지|붙임쪽지|테이프|접착제|리트머스종이|염화코발트종이|시약포지|거름종이|유산지|휴지|면봉|검사지|사포', head):
        if '거름종이틀' in head:
            return PENDING, '부록으로 만드는 틀의 재질·반복 사용 여부 확인 필요'
        return SUPPLIES, '부착·여과·검출·도포 등에 쓰는 소모 재료'
    if re.fullmatch(r'풀(?:\d+개)?|풀또는양면테이프|솜|거즈|성냥|초|향', head):
        return SUPPLIES, '접착·흡수·연소 과정에 사용하는 소모 재료'
    if re.search(r'용액|수용액|소독제|검출시약|희석액|원액|색소|글리세|잉크|물감|밀랍|석고반죽|향수|비눗물', head) or head=='탄산수':
        return SUPPLIES, '실험에 투입하는 액체·시약·혼합물 재료'
    if re.search(r'과망가니즈산|질산(칼륨|구리|암모늄)|황산(구리|나트륨)|수산화나트륨|탄산수소나트륨|염화나트륨|에탄올|아세톤|붕산|로르산|리놀레산|스테아르산|팔미트산|묽은염산|제빵소다', head):
        return SUPPLIES, '실험에 투입하는 명시된 화학 물질'
    if re.search(r'물과.*혼합물|드라이아이스|얼음|증류수|정제수|찬물|따뜻한물|뜨거운물|차가운물|미지근한물|상온의물|실온의물', head) or re.fullmatch(r'(?:약)?[\d.~°℃C]+의?물|물', head):
        if '틀' not in head and '사탕' not in head:
            return SUPPLIES, '실험에 투입하는 물·얼음·혼합물'
    if re.search(r'과자|초콜릿|사탕|우유|두유|음료|주스|달걀흰자|식용유|대두유|올리브유|카놀라유|코코넛기름|음식물|설탕|소금|식초|녹말|양파즙|곤약|세가지맛젤리', head) or head in {'밥','빵','콩'}:
        return SUPPLIES, '실험에 투입하는 식품·식재료'
    if re.search(r'시금치|시금칫잎|식물의잎|고정된호밀이삭|우무조각|인공소변|레몬1/2개', head):
        return SUPPLIES, '채취·가공되어 실험에 투입되는 시료'
    if re.search(r'풍선|전지|배터리|플라스틱컵|플라스틱숟가락|플라스틱접시|페트병|플라스틱병|생수병|요구르트병|알루미늄(깡통|캔)|일회|비닐|지퍼백|마스크|면도날|덮개유리|받침유리|끓임쪽', head):
        if not re.search(r'끼우개|풍선펌프', head):
            return PENDING, '소모·폐기·재사용 여부가 품목명만으로 확정되지 않음'
    if re.search(r'붙임|부록|도면|기록표|활동지|모식도|그래프|기록장|확인표|관측일지|계획서|카드|놀이판|그림|딱지|종이|도화지|용지|색지|공책|달력|이름표|번호표', head) or '부록' in n:
        return PENDING, '기록·제작에 소모하는 자료인지 반복 사용하는 교구인지 확인 필요'
    if re.search(r'고무줄|고무찰흙|색점토|점토|스티로폼|스타이로폼|스타일로폼|우드록|폼보드|종이컵|수수깡|빨대|나무막대|나무판|나무젓가락|알루미늄포일|알루미늄박|은박지|필름|셀로판지|에나멜선|니크롬선|철사|리본|털실|고무판|천|키트|검정말|모종|양파', head):
        if not re.search(r'저항판|실험장치|천체|방수천', head):
            return PENDING, '실험·제작 방식에 따라 가공·소모하거나 재사용할 수 있는 물품'
    if re.search(r'비커|플라스크|주사기|스포이트|피펫|바이알|시약병|점적병|집기병|스프레이병|보온병|유리컵|금속컵|알루미늄컵|수조|물통|페트리접시|시계접시|증발접시|질량접시|유리막대|유리관|유리판|깔때기|홈판|홈통|막자|숟가락|약수저', head):
        return EQUIPMENT, '반복 사용하는 실험 용기·기구'
    if re.search(r'온도계|체온계|저울|센서|감지기|전류계|전압계|전도계|측정기|열량계|초시계|시계|각도기|줄자|눈금자|곡선자|나침반|검전기|조흔판|확대경|돋보기|현미경|망원경|렌즈|거울|루페', head) or re.fullmatch(r'(?:\d+cm)?자', head):
        return EQUIPMENT, '반복 사용하는 측정·관찰 기구'
    if re.search(r'장치|스탠드|스텐드|삼각대|삼발이|거치대|집게|받침대|고정대|고정장치|지지대|클램프|받침판|보드|스위치|전선|코일|전구|전등|광원|레이저|핫플레이트|교반기|가습기|드라이어|말리개|전자레인지|선풍기|마이크로컨트롤러|전동기|펌프|주입기|봉합기|용수철|자석|고무마개|실리콘마개|주사기마개|끼우개', head):
        return EQUIPMENT, '반복 사용하는 장치·전기 부품·고정 기구'
    if re.search(r'스마트폰|컴퓨터|노트북|카메라|액션캠|가상현실체험기기|회전의자|도서', head) or head == '책':
        return EQUIPMENT, '반복 사용하는 전자 기기·비품·도서'
    if re.search(r'가위|종이찍개|구멍뚫이|니퍼|송곳|해부침|점화기|커팅매트|컷팅매트|컴퍼스|핸드벨|칼림바|실로폰|글로켄슈필|리코더|소리굽쇠|악기|손전등|안경|눈가리개|고무망치', head) or head == '칼':
        return EQUIPMENT, '반복 사용하는 작업 도구·보호 도구·악기'
    if re.search(r'펜|연필|필기구|필기도구', head):
        return EQUIPMENT, '실험 후에도 남아 반복 사용하는 필기 도구'
    if re.search(r'영구표본|지구본|조절식|털가죽|줄넘기|바둑알|주사위|탁구공|쇠구슬|바이메탈|플라스틱막대|고리달린나무도막|고리가있는나무도막|탑쌓기용나무도막|시멘트저항', head) or re.fullmatch(r'(?:\d+g|금속)?추(?:\d+개)?|추|추[\d]+개|클립|철클립|링|고리|쇠고리|종|말', head):
        return EQUIPMENT, '형태를 유지하며 반복 사용하는 실험 도구·교구'
    return PENDING, '사용 후 남는지 또는 재사용하는 물품인지 추가 판단 필요'


def review_group(item):
    text=norm(item['representative_text'])
    reason=item['reason']
    if '함께' in reason: return '복합 항목·용기와 내용물'
    if '구성 물품' in reason: return '구체적인 물품이 정해지지 않은 항목'
    if '소프트웨어' in reason: return '프로그램·앱·디지털 자료'
    if re.search(r'마스크|면도날|덮개유리|받침유리|방수천',text): return '보호용품·현미경 소모품'
    if re.search(r'풍선',text): return '풍선'
    if re.search(r'전지',text) and '도화지' not in text:return '건전지·전지'
    if re.search(r'컵|페트병|플라스틱병|요구르트병|생수병|그릇|접시|용기|깡통|캔|플라스틱통',text): return '컵·병·통·용기류'
    if re.search(r'카드|부록|놀이|활동판|별자리|위상변화판|모식도|그림|지도|모형|자료|도면|판',text) and not re.search(r'철판|구리판|나무판|금속판|물질판|플라스틱판|우드록',text): return '카드·모형·부록·학습 자료'
    if re.search(r'종이|도화지|용지|색지|공책|달력|이름표|번호표|골판지',text):return '일반 종이·문구 재료'
    if re.search(r'모종|검정말|양파|표본|암석|광물',text):return '생물·암석·광물 시료'
    if re.search(r'구리|철|알루미늄|금속|니크롬선|에나멜선|마그네슘',text):return '금속·금속선·포일'
    if re.search(r'고무줄|찰흙|점토|고무판',text):return '고무줄·고무판·점토'
    if re.search(r'비닐|지퍼백|뽁뽁이',text):return '봉지·포장재'
    if re.search(r'실|끈|리본|천|그물|수건',text):return '실·끈·천·그물'
    if re.search(r'스타이로폼|스타일로폼|스티로폼|우드록|폼|나무|수수깡|빨대|필름|셀로판|이쑤시개',text):return '제작 재료·막대·빨대·필름'
    if re.search(r'물체|물건|소품|도구|재료|지우개',text):return '물체·도구·소품의 구체적 용도'
    return '그 밖의 재사용 여부 확인 항목'


def main():
    if not BACKUP.exists():
        current=json.loads(TARGET.read_text(encoding='utf8'))
        if 'preparation_classification' in current['metadata']:
            raise ValueError('분류 전 백업이 없으므로 현재 결과를 덮어쓸 수 없음')
        with BACKUP.open('xb') as stream: stream.write(TARGET.read_bytes())
    source=json.loads(BACKUP.read_text(encoding='utf8'))
    source_checks=[]
    for dataset in source['metadata']['source_datasets']:
        input_path=ROOT/dataset['input_file']
        assert sha(input_path)==dataset['sha256'],dataset['label']
        original=json.loads(input_path.read_text(encoding='utf-8-sig'))
        a,b=dataset['record_index_range_zero_based']
        assert source['data'][a:b+1]==original['data'],dataset['label']
        source_checks.append({'dataset':dataset['label'],'record_count':len(original['data']),
                              'records_exactly_preserved':True,'input_file_unchanged':True})
    current=json.loads(TARGET.read_text(encoding='utf8'))
    stripped=deepcopy(current)
    stripped['metadata'].pop('preparation_classification',None)
    for row in stripped['data']:
        for field in FIELDS: row.pop(field,None)
    if stripped != source:
        raise ValueError('통합본의 원래 내용이 백업 이후 변경됨. 덮어쓰기 전에 대조 필요')
    decisions=json.loads(DECISIONS.read_text(encoding='utf8')) if DECISIONS.exists() else {}
    result=deepcopy(source)
    catalogue={}
    counts=Counter()
    for row in result['data']:
        raw=row['교구']
        if raw is None:
            for field in FIELDS: row[field]=None
            continue
        for field in FIELDS: row[field]=[]
        spans,error=split_items(row)
        for index,(start,end) in enumerate(spans,1):
            text=raw[start:end]
            key=norm(text)
            item_id='ITEM-'+hashlib.sha256(key.encode('utf8')).hexdigest()[:16]
            category,reason=classify(text,error)
            origin='사용자 예시 및 명확한 품목 기준' if category != PENDING else '사용자 판단 대기'
            decision=decisions.get(item_id)
            if decision and decision.get('category') is not None:
                if decision['category'] not in (EQUIPMENT,SUPPLIES):
                    raise ValueError(f'{item_id}: invalid user category')
                category=decision['category']; reason=decision.get('note') or '사용자 확정'; origin='사용자 지정'
            entry=catalogue.setdefault(item_id, {'item_id':item_id,'representative_text':text,'raw_variants':[],
                'category':category,'reason':reason,'decision_source':origin,'occurrences':[]})
            if entry['category'] != category:
                raise ValueError(f'{item_id}: conflicting categories')
            if text not in entry['raw_variants']:entry['raw_variants'].append(text)
            occurrence={'activity_id':row['id'],'activity_title':row['탐구활동'],'publisher':row['출판사'],
                'page':row['쪽'],'item_index':index,'raw_text':text,'span':[start,end]}
            entry['occurrences'].append(occurrence)
            row[category].append(text)
            row['준비물 분류'].append({'item_id':item_id,'원문':text,'원문_범위':[start,end],
                '분류':category,'근거':reason,'판단출처':origin})
            counts[category]+=1
    # Independently reconstruct every source item's span and partition before writing.
    for old,row in zip(source['data'],result['data']):
        restored={k:v for k,v in row.items() if k not in FIELDS}
        assert restored == old, row['id']
        if row['교구'] is None:
            assert all(row[f] is None for f in FIELDS)
            continue
        used=set()
        for item in row['준비물 분류']:
            a,b=item['원문_범위']; assert row['교구'][a:b] == item['원문']
            assert not used.intersection(range(a,b)); used.update(range(a,b))
        leftovers=''.join(c for i,c in enumerate(row['교구']) if i not in used)
        allowed=',，\n\r\t '
        if row['id']=='activity_0363':allowed+='□.'
        assert all(c in allowed for c in leftovers), (row['id'],leftovers)
        for category in (EQUIPMENT,SUPPLIES,PENDING):
            assert row[category] == [i['원문'] for i in row['준비물 분류'] if i['분류']==category]
    assert source['views']==result['views']
    pending=sorted([x for x in catalogue.values() if x['category']==PENDING],key=lambda x:(-len(x['occurrences']),x['representative_text']))
    for item in pending:item['review_group']=review_group(item)
    metadata={
        'schema_version':'1.0','unclassified_backup':BACKUP.name,'unclassified_sha256':sha(BACKUP),
        'policy':'사용자가 정한 기준: 실험 후에도 남아 반복 사용하는 물품은 실험 기자재, 투입·소모 재료는 실험 준비물. 불명확하면 분류 보류.',
        'original_field':'교구','added_fields':FIELDS,
        'notes':['장갑·보안경·실험복은 사용자 지정에 따라 기자재로 분류한다.',
            '원문·규격·농도·수량은 변경하지 않고 분류 필드만 추가한다.',
            '약품규정의 약품명 목록 일치 여부는 이 분류의 조건이 아니다.',
            '미확인 원문(null)은 세 분류도 null이며, 명시된 목록에 해당 분류가 없으면 빈 배열이다.',
            '분류 보류는 임의로 어느 쪽에도 넣지 않았으며 classification_review.md에서 판단할 수 있다.',
            '일반 명칭의 펜·연필은 반복 사용하는 도구로 분류한다. 기본 규칙보다 classification_decisions.json의 사용자 확정 분류를 우선한다.',
            '2026-09-23 사용자 결정: 부록 표기가 있는 항목과 프로그램·앱·디지털 자료는 기자재. 나머지 그룹·개별 지정 결정과 적용 범위는 decision_history/20260923/applied_decisions.json에 기록했다.',
            '후속 사용자 지시에 따라 남은 62개 표기는 일단 실험 준비물로 분류했다. 이는 추후 변경 가능한 사용자 임시 지정이며 decision_history/20260923-remaining-to-supplies/applied_decisions.json에 기록했다.'],
        'record_count':len(result['data']),'records_without_preparation_text':sum(r['교구'] is None for r in result['data']),
        'item_occurrences':{k:counts[k] for k in (EQUIPMENT,SUPPLIES,PENDING)},'unique_item_count':len(catalogue),'pending_unique_items':len(pending),
        'unique_items_by_category':{k:sum(i['category']==k for i in catalogue.values()) for k in (EQUIPMENT,SUPPLIES,PENDING)},
        'records_with_pending_items':sum(bool(r[PENDING]) for r in result['data'])}
    result['metadata']['preparation_classification']=metadata
    write(TARGET,result)
    write(OUT/'preparation_item_catalogue.json',{'metadata':metadata,'items':sorted(catalogue.values(),key=lambda x:x['representative_text'])})
    write(OUT/'classification_review.json',{'instructions':'각 item_id를 classification_decisions.json의 키로 사용하고 category에 실험 기자재 또는 실험 준비물을 입력한다. 미결정은 null. 참고 문맥은 occurrences에 있다.', 'item_count':len(pending),'items':pending})
    for item in pending:
        decisions.setdefault(item['item_id'],{'raw_text':item['representative_text'],'category':None,'note':None})
    pending_ids={i['item_id'] for i in pending}
    decisions={k:v for k,v in decisions.items() if k in pending_ids or v.get('category') is not None}
    write(DECISIONS, decisions)
    def cell(text):return re.sub(r'\s+',' ',str(text)).replace('|','\\|')
    lines=['# 사용자 판단이 필요한 준비물','',f'미결정 {len(pending)}항목. 같은 이름의 반복 출현을 묶었다. 규격·농도·형태가 다른 항목은 임의로 합치지 않았다.',
        '', '각 행의 `ITEM-…` ID와 함께 **실험 기자재** 또는 **실험 준비물**로 알려주면 반영할 수 있다. 특정 활동에서만 다른 분류가 필요하면 활동 ID도 함께 지정한다.',
        '', '원문 전체와 모든 사용 활동은 `classification_review.json`에 있으며, 판단 입력 파일은 `classification_decisions.json`이다.',
        '', '| 번호 | 물품 원문 | 출현 수 | 보류 이유 | 예시 활동 | 항목 ID |','|---:|---|---:|---|---|---|']
    for i,item in enumerate(pending,1):
        example=item['occurrences'][0]
        lines.append(f"| {i} | {cell(item['representative_text'])} | {len(item['occurrences'])} | {cell(item['reason'])} | {cell(example['activity_title'])} · {cell(example['publisher'])} {example['page']}쪽 · {example['activity_id']} | {item['item_id']} |")
    (OUT/'classification_review.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    groups={}
    for i,item in enumerate(pending,1):
        group=groups.setdefault(item['review_group'],{'group':item['review_group'],'item_ids':[], 'review_row_numbers':[], 'occurrences':0,'examples':[]})
        group['item_ids'].append(item['item_id']);group['review_row_numbers'].append(i)
        group['occurrences']+=len(item['occurrences'])
        if len(group['examples'])<5:group['examples'].append(cell(item['representative_text']))
    group_list=sorted(groups.values(),key=lambda g:-len(g['item_ids']))
    write(OUT/'classification_review_groups.json',{'group_count':len(group_list),'item_count':len(pending),'groups':group_list})
    overview=['# 준비물 분류 판단 목록 요약','',f'판단이 필요한 **{len(pending)}개 품목 표기**를 **{len(group_list)}개 유형**으로 묶었다. 유형은 검토 편의를 위한 묶음이며 아직 기자재·준비물 분류를 확정한 것은 아니다.',
        '', '[전체 판단 목록](classification_review.md)에는 항목별 보류 이유와 사용 활동이 있다. 규격·부록 쪽·재질이 다른 표기를 임의로 합치지 않아 같은 계열의 물품이 여러 행에 나올 수 있다.',
        '', '| 유형 | 품목 표기 수 | 활동 내 출현 수 | 대표 항목 |','|---|---:|---:|---|']
    for group in group_list:
        overview.append(f"| {group['group']} | {len(group['item_ids'])} | {group['occurrences']} | {' / '.join(group['examples'])} |")
    overview += ['', '그룹 전체에 같은 결정을 적용할 수도 있고, 전체 판단 목록의 번호·물품명·활동 ID를 지정해 개별 결정할 수도 있다. 이미 사용자 결정으로 확정한 항목은 이 보류 목록에서 제외했다.',
        '', '명시된 준비물 목록 자체가 없는 103개 활동은 별도 미확인 상태로 유지했다. 이 목록에 없는 준비물을 추정해 추가하지 않았다.']
    (OUT/'classification_review_groups.md').write_text('\n'.join(overview)+'\n',encoding='utf8')
    saved=json.loads(TARGET.read_text(encoding='utf8'))
    assert saved==result
    report={'status':'passed','source_fields_exactly_preserved':True,'all_nonseparator_characters_accounted_for':True,
        'each_occurrence_assigned_once':True,'nulls_preserved':True,'views_preserved':True,
        'output_sha256':sha(TARGET),'sources':source_checks,'counts':metadata}
    write(OUT/'classification_validation.json',report)
    merge_validation=OUT/'validation.json'
    historical=OUT/'merge_validation_unclassified.json'
    if not historical.exists() and merge_validation.exists():
        with historical.open('xb') as stream:stream.write(merge_validation.read_bytes())
    write(merge_validation,{'status':'passed','record_count':len(saved['data']),
        'unique_id_count':len({r['id'] for r in saved['data']}),'output_sha256':sha(TARGET),'sources':source_checks,
        'preparation_classification':metadata,'classification_validation_file':'classification_validation.json',
        'prior_merge_validation_file':historical.name,'scope':'원래 행과 파일 보존, 항목 원문·분류 일관성 검사. 보류 항목은 사용자 판단 대기.'})
    print(json.dumps(metadata,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
