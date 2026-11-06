"""Rebuild independently authored high-school science SVGs from factual specifications.

No source image/PDF loading, tracing, raster embedding, or external references.
The review JSON supplies only activity IDs and the number/order of figure slots.
"""
import json, math, re, html, itertools, random
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
FIG = ROOT / 'site/dist/procedure-figures'
rows = json.loads((ROOT/'outputs/review/procedures/high.json').read_text(encoding='utf-8'))
# Facts from the already verified source pages; all geometry below is newly authored.
S={}
def add(i,title,items,kind='cards',note='사실 관계를 정리한 학습 자료'):
 S.setdefault(i,[]).append(dict(title=title,items=items,kind=kind,note=note))
add(9,'빛의 종류에 따른 선의 대응',['백열등: 연속적으로 이어지는 빛','수소: 서로 떨어진 밝은 선','헬륨: 수소와 다른 위치의 선','천체: 연속광 속에서 두 기체에 대응하는 어두운 선'],'spectrum','관측 특징의 개념 모형 · 정량 파장·선 세기 자료 아님')
add(10,'질량으로 비교한 구성 원소',['지구|철 35.0% · 산소 30.0% · 규소 15.0% · 마그네슘 13.0% · 니켈 2.4% · 황 1.9% · 칼슘 1.1% · 알루미늄 1.1% · 기타 0.5%','사람|산소 65.0% · 탄소 18.5% · 수소 9.5% · 질소 3.3% · 칼슘 1.5% · 인 1.0% · 기타 1.2%'])
add(18,'같은 단위체, 서로 다른 접힘',['헤모글로빈|접혀 모인 여러 사슬','케라틴|길게 이어지는 섬유 형태','공통 단위|아미노산'],'protein','단백질 형태의 개념도 · 실제 원자 좌표 아님')
add(20,'두 가닥을 연결하는 방법',['한쪽 골격: 당 → 인산 → 당','반대 골격: 당 ← 인산 ← 당','염기쌍: A–T, G–C'],'dna','테이프로 연결하는 종이 모형')
add(20,'잘라 쓸 DNA 부품',['A','T','G','C'],'dna-template','단위 부품을 복사해 사용 · 선을 따라 잘라 테이프로 연결')
add(26,'극지 환경 관측의 변화',['북극해 얼음|1980년 10월 → 2020년 10월: 분포 면적 감소','남극 상공 오존|1979년 10월 → 2022년 10월: 낮은 농도 영역 확대'],'cards','지도 대신 관측 특징을 요약한 비교 자료')
add(38,'용액과 적혈구의 형태',['생리식염수|기준 상태','증류수|세포가 팽창함','10% 소금물|세포가 수축함'],'cells','삼투 현상의 형태 모형 · 현미경 사진 아님')
add(50,'구리판 표면의 관찰 기록',['가열 전|붉은 갈색','겉불꽃에 가열|표면이 검게 변함','속불꽃에 다시 가열|붉은 갈색 표면이 나타남'],'flame','관찰된 색 변화를 나타낸 개념도')
add(60,'연못의 구성 요소 목록',['환경|빛 · 온도 · 물 · 공기 · 흙','생물|수생 식물 · 나무 · 물고기 · 새 · 세균 · 곰팡이'],'ecosystem','생태계 구성 요소를 분류하기 위한 개념 모형')
add(62,'카이바브 고원의 변화 순서',['1905년|늑대 약 400마리 · 사슴 약 3,800마리','늑대 사냥 허용 이후|늑대 감소 · 1905~1920년 사슴 증가','1920~1930년|먹이 식물 감소 · 사슴 감소'],'cards','관측 추세 요약 · 연도별 실측 곡선 아님')
add(64,'알프스 빙하의 장기 변화',['비교 시기|1908년과 2017년','관측 특징|100여 년 사이 빙하의 절반 이상 감소'],'cards','변화의 크기와 기간을 정리한 자료')
add(64,'아마존 숲의 장기 변화',['비교 시기|2000년과 2019년','관측 특징|약 20년 사이 열대우림 면적 약 7% 감소'],'cards','위성 영상 대신 관측 내용을 정리한 자료')
add(65,'평균 기온과 이산화 탄소 추세',['기온 차이|2023년 − 1950년: 약 +1.17 ℃','30년 평균의 차이|1994~2023년 − 1950~1979년: 약 +0.61 ℃','대기 이산화 탄소|1950년 약 310 ppm → 2023년 약 420 ppm'],'cards','주어진 기간의 관측 요약 · 농도는 도표 눈금의 근삿값')
add(66,'에너지 이동 경로별 장부',['기준|지구로 들어오는 태양 복사 = 100','태양 → 우주 반사|지표 5 + 대기·구름 25 = 30','태양 → 흡수|대기 20 · 지표 50','지표 → 방출|대기 132 · 우주 12','대기 → 방출|지표 94 · 우주 58'],'energy','방향별 수치를 합산하여 각 영역의 유입·유출 비교')
add(68,'2100년을 향한 두 경로',['A · 감축하지 않는 경로|화석 연료 사용 지속 / 배출량 크게 증가 / 기온 상승 폭 큼','B · 감축에 성공하는 경로|온실 기체 배출량 감소 / 기온 상승 폭이 상대적으로 작음'],'cards','시나리오의 추세 비교 · 실제 미래를 단정하는 자료 아님')
add(72,'간이 발전기의 연결 관계',['축에 고정|날개 → 헤드 → 네오디뮴 자석','위치|헤드–코일 3 cm / 헤드–자석 2~3 mm','전기 연결|코일 양 끝 → LED 기판','철판|코일에 연결하고 양 끝을 구부림'],'generator','부품 관계와 지정 간격 · 실제 크기 비례 아님')
add(80,'핵산 검사에서 비교할 변화',['처리 순서|검체 → 핵산 추출 → 증폭 장치 → 측정','증폭 반복|1회 → 2회 → 3회 → … → 30회','사람 3|반복 후 핵산량이 증가','사람 4|반복해도 증가가 나타나지 않음'],'cards','증폭 결과의 정성 요약 · 실제 검사 곡선 아님')
add(93,'모호한 양을 분명하게 말하기',['시간 표현|조금 뒤에 만나자.','거리 표현|여기서 멀지 않은 곳이야.','질량 표현|혼자 들기는 무거운 상자야.','과제|각 표현을 측정값과 단위가 드러나게 바꾸기'],'cards','단위를 배우기 위한 대화 소재')
add(94,'일주일 기상 자료의 단위',['기온|최저 9, 7, 8, 8, 9, 9, 13 ℃ / 최고 17, 16, 18, 20, 21, 24, 26 ℃','강수|확률 5, 5, 5, 5, 5, 5, 20% / 강수량은 모두 1 mm 미만','바람과 습도|풍속 m/s · 상대 습도 %'],'cards','월요일부터 일요일까지의 항목별 자료')
add(101,'천체의 선을 서로 맞춰 보기',['수소|밝은 선의 기준 위치','별 A|밝은 바탕에 어두운 선','성운 B|어두운 바탕에 밝은 선'],'spectrum','관측 특징의 개념 모형 · 정량 파장·선 세기 자료 아님')
add(105,'원자 번호와 전자 껍질',['H 1|1','Li 3|2, 1','B 5|2, 3','F 9|2, 7','Na 11|2, 8, 1','Ar 18|2, 8, 8'],'electrons','중성 원자 · 숫자는 안쪽부터의 전자 수')
add(107,'연결점이 다른 세 단위',['I: 두 연결점','II: 세 연결점','III: 네 연결점'],'connectors','같은 크기 원판의 표시된 연결점만 이용하는 모형')
add(109,'방향이 반대인 두 골격',['한 가닥: 24개 단위 연결','짝짓기: A–T / G–C','반대 가닥: 골격 방향을 반대로'],'dna','테이프로 연결하는 종이 모형')
add(109,'종이 모형의 단위 부품',['A','T','G','C'],'dna-template','24개 단위가 이어지도록 필요한 부품 수를 준비')
add(124,'세 문자씩 읽는 정보 모형',['기준|AUG GCU ACG UUC GAU CCA','한 문자 바꿈|AUG GCU ACG UAC GAU CCA','한 문자 빠짐|AUG CUA CGU UCG AUC CA'],'cards','정보 전달 모형 · 실제 유전자 서열 아님')
add(124,'모형 부호와 비즈의 대응',['AUG|빨간 원','GCU|파란 세모','ACG|초록 네모','UUC|노란 별','GAU|보라 원','CCA|주황 세모','UAC|흰 네모','CUA|검은 원','CGU|주황 별','UCG|보라 세모','AUC|노란 네모'],'cards','실제 유전 암호표가 아닌 활동용 대응표 · 남은 두 문자는 연결하지 않음')
add(126,'시간축에 놓을 출현 시점',['지구 탄생|약 45.67억 년 전','광합성 생물|약 35억 년 전','육상식물|약 4.2억 년 전','육상 척추동물|약 3.8억 년 전','유인원 계통의 화석|약 2520만 년 전 · 최초 출현 확정값 아님','시대 경계|고생대 5.39억 / 중생대 2.52억 / 신생대 0.66억 년 전'])
add(128,'먹이와 부리의 대응',['선인장|길고 가는 부리','단단한 열매·씨|두껍고 튼튼한 부리','작고 부드러운 씨|상대적으로 작은 부리'],'beaks','먹이 이용에 관련된 형태를 단순화한 모형')
add(132,'철 솜을 가열했을 때',['처음|양쪽 철 솜의 질량이 같아 수평','오른쪽 가열 후|검게 변한 오른쪽이 아래로 내려감'],'balance','관찰된 질량 변화를 나타낸 모형')
add(134,'반응을 찾아볼 생활 사례',['주방|불꽃 · 자른 과일 · 금속 표면','욕실|표백과 탈색','야외|손난로 · 부식된 철','거실|식물 · 호흡 · 과산화 수소'],'cards','사례 목록')
add(138,'에너지 출입을 찾아볼 상황',['냉방|액체 냉매의 기화','조리·난방|연료의 연소','식물|빛을 받아 영양분 합성','생물의 체온|세포호흡','음료|차가운 음료와 몸 사이 열 이동'])
add(143,'서로 영향을 주는 구성원',['생물|사람 · 개미 · 나무 · 민들레 · 토양 미생물','비생물|빛 · 온도 · 흙 · 공기','관계 찾기|양쪽 사이의 영향을 화살표로 연결'],'ecosystem','관계 정리용 모형')
add(148,'개발 방식에 따른 기후 전망',['계속 증가하는 화석 연료 사용|2100년 기온 변화 약 +6 ℃ / 강수량 변화 약 +11%','연료 사용을 줄이는 개발|2100년 기온 변화 약 +2 ℃ / 강수량 변화 약 +5%'],'cards','도표의 2100년 눈금을 읽은 근삿값 · 두 전망의 비교용')
add(150,'태양에서 생활까지',['(가) 식물|태양 에너지를 받아 자람','(나) 빨래|햇빛 아래에서 물기가 마름','(다) 태양광 장치|빛을 받아 전기를 만듦'],'cards','에너지 전환의 관계를 정리한 개념 자료')
add(178,'두 별의 선 위치 비교',['수소|뚜렷한 기준 방출선','베가|수소의 선 위치와 맞는 강한 흡수선','알타이르|수소의 선 위치와 맞는 강한 흡수선'],'spectrum','관측된 대응 관계의 개념 모형 · 실제 스펙트럼 사진 아님')
add(181,'2주기 전자 배치',['Li 3|2, 1','Be 4|2, 2','B 5|2, 3','C 6|2, 4','N 7|2, 5','O 8|2, 6','F 9|2, 7','Ne 10|2, 8'],'electrons')
add(181,'3주기 전자 배치',['Na 11|2, 8, 1','Mg 12|2, 8, 2','Al 13|2, 8, 3','Si 14|2, 8, 4','P 15|2, 8, 5','S 16|2, 8, 6','Cl 17|2, 8, 7','Ar 18|2, 8, 8'],'electrons')
add(186,'단백질의 서로 다른 구조',['케라틴|머리카락 / 길게 이어지는 형태','크리스탈린|수정체 / 접혀 모인 형태','콜라젠|피부 / 여러 사슬이 꼬인 형태'],'protein','구조적 특징을 나타낸 모형 · 아미노산 실제 서열·좌표 아님')
add(190,'물과 에너지가 이동하는 현상',['해안|바람이 수면에 파도를 만듦','하늘|구름 사이로 햇빛이 들어옴','논과 수로|물이 지표를 따라 이동함'],'cards','기상 사진의 현상을 글과 관계로 정리한 자료')
add(208,'먹이 종류와 핀치 부리',['씨앗|짧고 두꺼운 부리','곤충|가늘고 뾰족한 부리','선인장|길게 뻗은 부리'],'beaks','먹이 이용과 연결되는 형태의 단순 모형')
add(220,'지구 에너지 이동량',['기준|들어오는 태양 복사 100','우주로 반사|대기·구름 22.7 / 지표 6.7','태양 에너지 흡수|대기 22.6 / 지표 48.0','지표 → 대기|대류·전도 5.4 / 증발 25.4','복사|지표 방출 117 / 대기 재복사 100','우주로 나가는 지구 복사|70.5'],'energy','각 경로의 수치 비교 · 규모는 입사 태양 복사 대비 상대량')
add(226,'하이브리드의 주행별 흐름',['시동|전기 모터로 작동','가속·오르막|엔진 + 전기 모터','감속·내리막|운동 → 전기 → 배터리 충전','정속|효율 좋은 엔진 구간에서 엔진 사용'],'energy','제시된 작동 사례를 단계별로 정리')
add(240,'대기 관측에 쓰이는 양과 단위',['시각|9시 · 10시 · 11시 · 3시 · 4시','농도|미세먼지·초미세먼지: μg/m³','기온|℃','습도|%','풍속|m/s','관찰 기록|11시 환기 1회'],'cards','단위 분류를 위한 항목별 관측 정보')
add(248,'우주 이야기 순서 맞추기',['별의 탄생','우주의 시작','태양계 형성','원자 형성','생명체의 등장','별 내부의 원소 생성'],'timeline','사건 조각 · 잘라서 시간 순서로 배열')
add(248,'배열한 사건에 설명 붙이기',['원소가 언제 만들어졌는가?','먼저 생긴 물질이 다음 사건의 재료가 되는가?','우주와 지구의 역사는 어떻게 이어지는가?'],'cards','완성 그림을 뒤집는 방식 대신 사건–설명 연결 활동')
add(249,'광원과 미지 천체 비교',['수소 방출선','헬륨 방출선','별 A의 흡수선','별 B의 흡수선'],'spectrum','수소·헬륨 선의 대응을 비교하는 개념 모형 · 실측 사진 아님')
add(250,'네 대상의 주요 원소',['우주|수소 · 헬륨','태양계|수소 · 헬륨','지구|철 · 산소 · 규소','바닷물|산소 · 수소'],'cards','대상의 생성 순서와 포함 관계를 연결하는 분류 카드')
for i in [251,252]:add(i,'두 대상의 질량 구성',['사람|산소 65% · 탄소 18.5% · 수소 9.5% · 질소 3.3% · 칼슘 1.5% · 인 1.0% · 기타 1.2%','지구|철 35% · 산소 30% · 규소 15% · 마그네슘 13% · 니켈 2.4% · 기타 4.6%'])
add(252,'시간 순서로 놓을 사건',['초신성 폭발','원자 생성','미행성체 충돌','빅뱅','원시 바다에서 생명체 탄생','별의 진화','원시 태양 생성','태양계 성운 수축'],'timeline','사건 카드 · 사건의 사실 관계로 순서를 결정')
add(255,'같은 주기와 같은 족',['2주기|전자 껍질 2개 / 최외각 전자 1~8개','3주기|전자 껍질 3개 / 최외각 전자 1~8개','같은 족|Li–Na, Be–Mg, B–Al, C–Si, N–P, O–S, F–Cl, Ne–Ar'],'cards')
add(256,'전자 배치를 비교할 네 원자',['H 1|1','O 8|2, 6','Na 11|2, 8, 1','Cl 17|2, 8, 7'],'electrons')
add(259,'변의 표시를 맞추는 조각',['한 변: ●','다른 변: ▲','나머지 변: ■'],'triangles','세 종류 변을 가진 도안 · 같은 표시끼리 연결')
add(261,'두 골격과 상보적 염기 부품',['A','T','G','C'],'dna-template','테이프로 골격을 잇는 도안 · 20쌍 제작')
add(262,'재료 판별 이동판',['출발','종이','구리선','나무','철 클립','고무','알루미늄 포일','유리','연필심','도착'],'board','마른 물체를 대상으로 도체·부도체를 판별')
add(272,'동시 출발을 만드는 위쪽 배치',['A: 책상 밖 자 끝 위','B: 책상 끝에서 자 옆에 접촉','자 가운데: 손가락으로 누름','자 끝을 치면 A 낙하, B 수평 출발'],'ruler','배치 원리 모형 · 사람과 물체의 실제 크기 비례 아님')
add(282,'세 자리 부호로 만든 메시지',['code'],'cipher','활동용 메시지')
add(282,'부호 해독용 대응표',['table'],'cipher-table','세 숫자를 한 묶음으로 읽음 · 실제 유전 암호표 아님')
add(289,'대멸종을 조사할 다섯 경계',['오르도비스기 말','데본기 후기','페름기 말','트라이아스기 말','백악기 말'],'timeline','생물 과의 감소가 나타난 다섯 시기의 조사 카드')
add(292,'섬의 먹이와 부리 특징',['곤충|가늘고 뾰족함','크고 단단한 씨|크고 튼튼함','선인장|가시보다 길게 뻗음','부드러운 열매|큰 부리'],'beaks')
add(294,'반응 전후의 관찰 정보',['가열 전 고체|검은 혼합물','가열 후 고체|붉은색 물질 생성','발생 기체를 통과시킨 석회수|뿌옇게 변함'],'reaction','관찰 사실 정리')
add(300,'물질 변화 낱말판',['연소','광합성','세포호흡','기화','응고','융해'],'wordgrid','9×9 배열 · 가로·세로·대각선 검색')
add(304,'공원 생물 분류 카드',['나무','풀','버섯','새','토끼','세균'],'colorcards','각 카드 테두리에 생산자·소비자·분해자 색을 칠하기')
add(306,'포식자와 피식자의 시간차',['눈신토끼 증가','뒤이어 스라소니 증가','눈신토끼 감소','뒤이어 스라소니 감소','관측 특징: 약 10년 주기의 반복'],'cycle','관측 추세의 관계도 · 실제 개체 수 곡선 아님')
add(308,'기후 변화 캠페인 구상판',['변화 선택|고온 · 해수면 상승 · 가뭄 등','근거 확인|환경 변화와 생물·생활 영향 조사','장면 구상|전달할 메시지와 장소·대상을 직접 결정','제작|직접 그리거나 생성 도구로 이미지 구성'],'cards','캠페인 이미지 제작 안내')
add(311,'기온 상승 시나리오의 조건',['화석 연료 사용 증가|2000년 대비 2050년 약 +2 ℃, 2100년 약 +6 ℃','평균 기온 +3 ℃ 가정|열대우림 변화 · 영구동토 해빙 · 질병 위험 증가','탐구|2050년 상황과 대응책을 구분하여 구성'],'cards','기온 전망은 도표의 근삿값 · +3 ℃는 별도의 가정')
add(319,'선풍기를 한 시간 사용한 뒤',['사용 전|모터 부분에 뚜렷한 고온 영역이 없음','1시간 사용 후|모터 부근이 주변보다 뜨거워짐','비교|전기 에너지의 여러 전환 결과를 생각하기'],'motor','열화상의 관찰 특징을 나타낸 개념도 · 온도 측정 영상 아님')
add(325,'세 식당의 평가 정보',['가 · 별점 4.8|맛 64 / 양 41 / 청결 37 / 모임 22 / 넓이 15 / 화장실 9','나 · 별점 4.6|맛 3648 / 친절 2701 / 신선 1763 / 청결 1189 / 메뉴 1054 / 양 832','다 · 별점 4.2|맛 973 / 친절 702 / 가격 대비 만족 528 / 반찬 341 / 청결 157 / 혼밥 125'],'cards','주어진 응답 수를 항목별로 재정리 · 복수 선택 가능')
add(348,'정사면체 종이 전개도',['Si: 중심','O: 네 꼭짓점'],'tetra','정사면체 전개도 · 네 면을 접어 테이프로 고정')
add(349,'두 가닥으로 만드는 DNA',['A','T','G','C'],'dna-template','종이 부품의 당·인산을 테이프로 잇고 염기를 안쪽으로 연결')
add(362,'막을 지나는 두 경로',['폐포–모세혈관|산소와 이산화 탄소는 반대 방향으로 이동','작은창자 세포|아미노산은 막 단백질을 지나 안으로 이동'],'membrane','이동 경로의 개념도 · 세포의 실제 크기 비례 아님')
add(374,'두 지역의 개체 분포',['가|A A / B B B B / C / D D D / E E E','나|A / B B B B B / C 없음 / D D / E E E E E'],'distribution','A~E는 서로 다른 종 · 같은 기호는 같은 종의 한 개체')
add(386,'해양 생태계 구성 카드',['다시마 · 식물 플랑크톤','동물 플랑크톤 · 성게 · 해삼 · 갑각류','작은 바닥 동물을 먹는 어류 · 플랑크톤을 먹는 어류 · 육식성 어류','해달 · 고래 · 바닷새','세균','비생물 요소: 빛 · 바닷물'],'ecosystem','구성원 분류 자료')
add(391,'1880~2021년 장기 관측 요약',['1800년대 후반|이산화 탄소 약 290 ppm / 기온 편차는 주로 음수','최근|2021년 410 ppm 초과 / 기온 편차는 주로 양수','변화의 속도|농도는 초기의 완만한 증가에서 최근의 가파른 증가로 변화'],'cards','관측 추세·범위의 요약 · 연도별 곡선 아님')
add(392,'복사 에너지의 연결 경로',['태양 → 대기·지표|일부 반사, 일부 흡수','지표 → 대기·우주|지구 복사 방출','대기 → 지표·우주|흡수한 에너지 재방출','비교할 조건|온실 기체가 늘어났을 때 각 경로의 변화'],'energy','화살표 크기는 정량값을 나타내지 않음')
add(393,'기온 상승별 변화 전망',['기준|산업화 이전 1850~1900년 대비','평균 +1.5 ℃|최고 +1.9 ℃ / 가뭄 2.0배 / 강수 1.5배 / 강설 −5% / 태풍 +10%','평균 +2 ℃|최고 +2.6 ℃ / 가뭄 2.4배 / 강수 1.7배 / 강설 −9% / 태풍 +13%','평균 +4 ℃|최고 +5.1 ℃ / 가뭄 4.1배 / 강수 2.7배 / 강설 −26% / 태풍 +30%'],'cards','각 지표를 같은 상승 조건끼리 비교하는 자료')
add(397,'전동기 내부의 두 요소',['축에 연결된 코일|도선이 감긴 회전 부분','겉통 안쪽의 자석|회전 부분 둘레에 배치','발전 시험|양쪽 단자를 LED와 연결하고 축 회전'],'motor','부품 관계를 나타낸 절개 개념도')
add(406,'측정 프로그램의 논리',['A 버튼|기록 시작','B 버튼|기록 중지','A+B 버튼|저장 기록 초기화','측정 반복|LED 제어 → 아날로그 읽기 → 농도 변환 → 저장','예시 간격|300,000 ms = 5분 / 실제 연결 핀 선택'],'cards','블록 화면 대신 직접 설계한 동작 흐름')
# Corrections after inspecting factual labels on source pages.
S[60][0]['items']=['비생물 요소|공기 · 빛 · 온도 · 물 · 토양','생물 요소|나무 · 버섯 · 부들 · 수련 · 부레옥잠 · 검정말 · 오리 · 개구리 · 붕어 · 다슬기 · 짚신벌레']
S[128][0]['items']=['딱딱한 씨·열매|두껍고 튼튼한 부리','곤충|가늘고 뾰족한 부리','선인장|길게 뻗은 부리']
S[150][0]['items']=['(가) 텔레비전|전기 → 빛·소리','(나) 헤어드라이어|전기 → 열·운동','(다) 태양광 장치|빛 → 전기','연결 과제|태양 에너지가 전기에 이르는 경로도 생각하기']
S[208][0]['items']=['식물 잎|잎을 잘라 먹는 부리','나뭇가지로 꺼낸 곤충|가늘고 뾰족한 부리','단단한 씨|두껍고 강한 부리','선인장 꽃·과육|길게 뻗은 부리']
S[249][0]['items']=['수소 방출선','헬륨 방출선','나트륨 방출선','칼슘 방출선','별 A의 흡수선','별 B의 흡수선']
S[304][0]['items']=['나무','풀','수련','버섯','새','토끼','다람쥐','물고기','곤충']
E=html.escape
class Canvas:
 def __init__(self,title,note):
  self.parts=[];self.y=92;self.title=title;self.note=note
 def t(self,x,y,s,size=26,color='#183a4d',weight='400',anchor='start'):
  self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{E(str(s))}</text>')
 def line(self,x1,y1,x2,y2,color='#286d82',width=3,dash=''):
  self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
 def rect(self,x,y,w,h,fill='#edf5f6',stroke='none',rx=10):self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>')
 def circle(self,x,y,r,fill='#dcebed',stroke='#286d82'):self.parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
 def poly(self,points,fill='#dcebed',stroke='#286d82'):self.parts.append(f'<polygon points="{points}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
 def path(self,d,stroke='#286d82',width=4,fill='none'):self.parts.append(f'<path d="{d}" stroke="{stroke}" stroke-width="{width}" fill="{fill}"/>')
 def arrow(self,x1,y1,x2,y2,color='#286d82',width=4):
  self.line(x1,y1,x2,y2,color,width);a=math.atan2(y2-y1,x2-x1);pts=[(x2,y2),(x2-12*math.cos(a-.4),y2-12*math.sin(a-.4)),(x2-12*math.cos(a+.4),y2-12*math.sin(a+.4))];self.poly(' '.join(f'{x:.1f},{y:.1f}' for x,y in pts),color,color)
 def wrap(self,s,width=35):
  # Keep words and numerical tokens intact; fall back only for long Korean text.
  def units(value): return sum(2 if ord(ch)>255 else 1 for ch in value)
  lines=[];line=''
  for token in s.split():
   candidate=(line+' '+token).strip()
   if line and units(candidate)>width: lines.append(line);line=''
   if units(token)>width and not re.search(r'\d',token):
    for ch in token:
     if units(line+ch)>width: lines.append(line);line=''
     line+=ch
   else: line=(line+' '+token).strip()
  if line: lines.append(line)
  return lines
 def block(self,title,body):
  lines=self.wrap(body,41);h=55+35*len(lines)
  self.rect(22,self.y,596,h);self.rect(22,self.y,6,h,'#26748a',rx=0)
  self.t(42,self.y+35,title,27,weight='700')
  for k,line in enumerate(lines):self.t(42,self.y+73+35*k,line,25)
  self.y+=h+14
 def items(self,items):
  for k,s in enumerate(items):
   a,b=s.split('|',1) if '|' in s else (f'{k+1:02}',s)
   self.block(a,b)
 def finish(self):
  titlelines=self.wrap(self.title,37)
  # Normal titles fit on one line; reserve additional header height if necessary.
  note=self.wrap(self.note,48);h=self.y+38+len(note)*32
  body=''.join(self.parts)
  header=f'<rect width="640" height="{h}" fill="#ffffff"/>'
  header+='<rect x="0" y="0" width="640" height="76" fill="#173b4d"/>'
  header+=f'<text x="24" y="48" fill="#ffffff" font-size="28" font-weight="700">{E(self.title)}</text>'
  for k,s in enumerate(note):body+=f'<text x="24" y="{self.y+23+32*k}" font-size="21" fill="#56717d">{E(s)}</text>'
  return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 {h}" role="img"><title>{E(self.title)}</title><desc>{E(self.note)}</desc><g font-family="Malgun Gothic, Noto Sans KR, sans-serif">{header}{body}</g></svg>\n'

def render(sp,i,seq):
 c=Canvas(sp['title'],sp['note']);kind=sp['kind'];items=sp['items']
 if kind=='spectrum':
  hpat=[.08,.18,.38,.93];hepat=[.29,.35,.51,.70,.96];napat=[.69,.71];capat=[.05,.10,.2,.3,.39,.89,.94,.97]
  if i==9:patterns=[[],hpat,hepat,sorted(set(hpat+hepat))];modes=['continuous','emission','emission','absorption']
  elif i==101:patterns=[hpat,hpat,hpat];modes=['emission','absorption','emission']
  elif i==178:patterns=[hpat,hpat,hpat];modes=['emission','absorption','absorption']
  else:patterns=[hpat,hepat,napat,capat,sorted(set(hpat+hepat+napat)),sorted(set(hpat+capat))];modes=['emission']*4+['absorption']*2
  colors=['#7044a5','#5a59aa','#377ea5','#299a8b','#78aa49','#e2b434','#dd8130','#c94138']
  for s,pat,mode in zip(items,patterns,modes):
   c.t(25,c.y+24,s.split('|')[0],25,weight='700');y=c.y+40
   c.rect(25,y,590,48,'#173344',rx=0)
   if mode!='emission':
    for n,col in enumerate(colors):c.rect(25+n*73.75,y,74,48,col,rx=0)
   for p in pat:c.line(25+p*590,y+2,25+p*590,y+46,'#152d3b' if mode=='absorption' else colors[min(int(p*8),7)],5)
   c.y+=115
  c.arrow(38,c.y,600,c.y);c.t(320,c.y+36,'파장이 커지는 방향',24,anchor='middle');c.y+=55
 elif kind=='electrons':
  for s in items:
   lab,v=s.split('|');counts=[int(n) for n in v.split(',')];y=c.y+75;c.t(30,c.y+30,lab,28,weight='700')
   for n,q in enumerate(counts):
    x=135+n*175;c.circle(x,y,43,fill='#f4f8f9');c.t(x,y+9,str(q),27,weight='700',anchor='middle');c.t(x,y+75,f'{n+1}번째',21,anchor='middle')
   c.y+=170
 elif kind=='protein':
  for j,s in enumerate(items[:3]):
   name,body=s.split('|');c.t(28,c.y+28,name,28,weight='700');y=c.y+95
   if '크리스' in name or '헤모' in name:
    for k in range(3):
     pts=[(330+95*math.sin(t*.16+k),y+40*math.cos(t*.23+k)) for t in range(80)];c.path('M '+' L '.join(f'{x:.1f},{y:.1f}' for x,y in pts),['#187d93','#d07d37','#6c699d'][k],5)
   else:
    for k in range(3 if '콜라' in name else 2):
     pts=[(170+t*4,y+22*math.sin(t*.18+k*2)) for t in range(90)];c.path('M '+' L '.join(f'{x:.1f},{yy:.1f}' for x,yy in pts),['#187d93','#d07d37','#6c699d'][k],5)
   c.y+=158;c.items([body])
 elif kind in ['dna','dna-template']:
  if kind=='dna':
   c.arrow(100,130,100,430);c.arrow(540,430,540,130)
   c.t(100,112,'5′',27,anchor='middle');c.t(540,112,'3′',27,anchor='middle');c.t(100,470,'3′',27,anchor='middle');c.t(540,470,'5′',27,anchor='middle')
   for j,(a,b) in enumerate([('A','T'),('G','C'),('T','A'),('C','G')]):
    y=165+j*75;c.circle(100,y,20,'#e1b370');c.circle(540,y,20,'#e1b370');c.rect(130,y-25,160,50,'#d5e9ef');c.rect(350,y-25,160,50,'#e3e0f0');c.t(210,y+10,a,29,anchor='middle');c.t(430,y+10,b,29,anchor='middle');c.line(290,y,350,y,dash='6 5')
   c.y=490;c.items(items)
  else:
   for j,b in enumerate(['A','T','G','C']):
    y=110+j*145;c.rect(25,y,590,125,'#ffffff','#829aa4',rx=0);c.circle(85,y+62,25,'#f1dcad');c.t(85,y+71,'P',25,anchor='middle');c.line(110,y+62,160,y+62);c.poly(f'160,{y+42} 195,{y+22} 230,{y+42} 217,{y+83} 173,{y+83}');c.t(195,y+65,'당',23,anchor='middle');c.line(230,y+62,285,y+62);c.rect(285,y+27,260,70,'#e4eff2','#377e91',rx=0);c.t(415,y+74,b,36,weight='700',anchor='middle')
   c.y=705;c.items(['P는 인산을 뜻함','당–인산을 연결하여 골격을 만들기','염기 A–T, G–C를 서로 연결하기'])
 elif kind=='cells':
  for j,s in enumerate(items):
   lab,body=s.split('|');y=c.y+70;c.t(25,c.y+25,lab,28,weight='700')
   if j==2:
    pts=[]
    for k in range(24):a=2*math.pi*k/24;r=42 if k%2 else 58;pts.append(f'{420+r*math.cos(a):.1f},{y+r*math.sin(a):.1f}')
    c.poly(' '.join(pts),'#edb4b6','#ae4a59')
   else:c.circle(420,y,58 if j==1 else 47,'#edb4b6','#ae4a59');c.circle(420,y,22 if j==0 else 36,'#f4d5d6','#d08c95')
   c.t(28,c.y+110,body,25);c.y+=175
 elif kind=='flame':
  for j,s in enumerate(items):
   lab,body=s.split('|');y=c.y;c.t(28,y+25,lab,28,weight='700');c.rect(405,y+10,160,60,['#b86c48','#34363a','#b86c48'][j],rx=0);c.t(28,y+85,body,25);c.y+=125
 elif kind=='balance':
  for j,s in enumerate(items):
   y=c.y+90;c.t(25,c.y+25,s.split('|')[0],27,weight='700');c.poly(f'300,{y+70} 340,{y+70} 320,{y-5}','#aac3cd');c.line(140,y-(15 if j else 0),500,y+(15 if j else 0),width=6)
   for x,dy in [(160,-15 if j else 0),(480,15 if j else 0)]:c.line(x,y+dy,x,y+dy+50);c.rect(x-45,y+dy+50,90,12,'#98b9c6',rx=0);c.path(f'M{x-32},{y+dy+43} q12,-20 24,-5 t24,-1 t12,6', '#333c42' if j and x==480 else '#9ba4aa',12)
   c.y+=190;c.items([s.split('|')[1]])
 elif kind=='beaks':
  for j,s in enumerate(items):
   lab,body=s.split('|');y=c.y+80;c.t(28,c.y+25,lab,27,weight='700');c.circle(380,y,41,'#e2eced');c.circle(391,y-12,4,'#193746');long=125 if ('길' in body or '가늘' in body) else 65;high=29 if ('두껍' in body or '큰' in body) else 12;c.poly(f'412,{y-high} {412+long},{y+2} 412,{y+high}','#d9ac66','#917343');c.t(28,c.y+145,body,25);c.y+=185
 elif kind=='ruler':
  c.rect(150,125,460,195,'#e9eff2',rx=0);c.line(150,125,150,320,'#254e64',6);c.line(150,320,610,320,'#254e64',6);c.t(330,160,'책상 위',28,anchor='middle');c.rect(45,250,490,30,'#f2d9a1','#9c7c40',rx=0);c.rect(55,215,45,35,'#be8061');c.t(75,205,'A',27,anchor='middle');c.rect(155,285,45,35,'#798ec0');c.t(227,308,'B',27,anchor='middle');c.circle(300,265,13,'#d96553');c.t(306,232,'누르는 점',25);c.arrow(180,325,180,405);c.t(213,389,'B: 수평으로 출발',24);c.circle(75,340,18,'#fff','#ae6c51');c.line(63,328,87,352,'#ae6c51',3);c.line(63,352,87,328,'#ae6c51',3);c.t(28,460,'A: 아래로 낙하 (화면 안쪽)',24);c.t(450,424,'책상 밖',24);c.y=495;c.items(items)
 elif kind=='generator':
  c.rect(25,110,590,220,'#edf5f6');c.t(45,148,'회전하는 부분',27,weight='700')
  c.line(140,245,500,245,'#617e8c',9)
  c.circle(140,245,12,'#476d83')
  for angle in [0,2*math.pi/3,4*math.pi/3]:
   dx,dy=60*math.cos(angle),60*math.sin(angle)
   c.line(140,245,140+dx,245+dy,'#488d9c',15)
  c.rect(420,217,110,56,'#c86c5f','#8e443c',rx=2);c.t(475,253,'자석',23,'#fff',anchor='middle')
  c.t(140,311,'날개',23,anchor='middle');c.t(310,211,'회전축',23,anchor='middle');c.arrow(540,193,568,220)
  c.arrow(475,340,475,405);c.t(300,378,'자기장 변화',24,anchor='middle')
  c.rect(25,420,590,220,'#f5f2e9');c.t(45,458,'고정된 부분',27,weight='700')
  c.rect(340,505,220,50,'#9dabb1',rx=2)
  for x in range(390,511,15):c.path(f'M{x},495 q15,-15 15,0 v70 q-15,15 -15,0 Z','#b77c3f',4)
  c.t(450,610,'철판과 코일',24,anchor='middle')
  c.rect(55,507,150,58,'#d2e3e5','#62838d');c.t(130,544,'LED 기판',23,anchor='middle')
  c.line(205,521,390,521,'#588b70',3);c.line(205,550,390,550,'#588b70',3)
  c.y=665;c.items(items)
 elif kind=='motor':
  y=220;c.rect(195,140,250,185,'#eef3f5','#375f73',rx=45);c.rect(211,160,218,24,'#6492a6');c.rect(211,283,218,24,'#6492a6');c.line(100,y,535,y,'#5c6876',11)
  for x in range(260,393,15):c.path(f'M{x},{y-35} q20,-20 20,0 v70 q-20,20 -20,0 Z','#bd7d3d',4)
  c.t(320,120,'자석 / 겉통',25,anchor='middle');c.t(320,365,'축과 코일',25,anchor='middle');c.arrow(510,175,550,195);c.y=400;c.items(items)
 elif kind=='membrane':
  for j in range(2):
   y=200+j*245;c.t(25,y-80,'폐포 ↔ 모세혈관' if j==0 else '작은창자 세포막',27,weight='700')
   for x in range(40,605,24):c.circle(x,y-10,7,'#b6d2dc');c.circle(x,y+10,7,'#b6d2dc')
   if j==0:c.arrow(205,y-65,205,y+65);c.arrow(440,y+65,440,y-65);c.t(175,y-35,'O₂',25);c.t(410,y+95,'CO₂',25)
   else:c.rect(285,y-40,70,80,'#d4b8d9','#7c5484');c.arrow(320,y-80,320,y+85);c.t(385,y+70,'아미노산',25)
  c.y=570;c.items(items)
 elif kind=='distribution':
  counts=[[2,4,1,3,3],[1,5,0,2,5]]
  for area,ns in zip(['가','나'],counts):
   c.t(25,c.y+30,f'지역 {area}',30,weight='700');c.y+=48
   for typ,n in zip('ABCDE',ns):
    c.t(33,c.y+33,typ,27,weight='700')
    if n==0:c.t(112,c.y+33,'없음',24)
    for k in range(n):c.circle(130+k*90,c.y+23,25,['#cce0d1','#d2e1ec','#e5d2bd','#e0cee9','#d4dcad']['ABCDE'.index(typ)]);c.t(130+k*90,c.y+32,typ,25,anchor='middle')
    c.y+=65
   c.y+=20
 elif kind=='triangles':
  for j in range(6):
   x=50+(j%2)*310;y=110+(j//2)*220;c.poly(f'{x+125},{y} {x+250},{y+190} {x},{y+190}','#fff','#5b7585');c.t(x+45,y+100,'●',26);c.t(x+180,y+100,'▲',26);c.t(x+115,y+175,'■',26)
  c.y=795;c.items(['필요한 장수만큼 인쇄·복사','●–●, ▲–▲, ■–■끼리 변을 연결'])
 elif kind=='connectors':
  for j,n in enumerate([2,3,4]):
   y=180+j*190;c.circle(320,y,68,'#fff');c.t(320,y+10,['I','II','III'][j],30,anchor='middle')
   for k in range(n):a=2*math.pi*k/n;c.circle(320+68*math.cos(a),y+68*math.sin(a),10,'#d17b4b')
  c.y=720;c.items(items)
 elif kind=='tetra':
  c.poly('320,150 170,410 470,410','#f0f5f6');c.poly('320,150 170,410 20,150','#fff');c.poly('320,150 470,410 620,150','#fff');c.poly('170,410 470,410 320,670','#fff')
  for a,b in [((320,150),(170,410)),((170,410),(470,410)),((320,150),(470,410))]:c.line(*a,*b,dash='9 8')
  for x,y in [(320,150),(170,410),(470,410)]:c.circle(x,y,12,'#d7b679')
  c.t(320,330,'중심 Si',26,anchor='middle');c.y=720;c.items(['실선: 자르기 / 점선: 접기','네 삼각형 면을 접어 정사면체 만들기','합쳐지는 꼭짓점마다 O 표시','안쪽 빵 끈으로 다른 모형과 연결'])
 elif kind=='wordgrid':
  rng=random.Random(20261105);grid=[[rng.choice('다로누비무서타고지하') for _ in range(9)] for _ in range(9)];positions=[(0,0,0,1),(0,8,1,0),(3,0,0,1),(5,3,1,1),(7,0,0,1),(2,5,1,0)]
  for word,(r,col,dr,dc) in zip(items,positions):
   for k,ch in enumerate(word):grid[r+k*dr][col+k*dc]=ch
  for r in range(9):
   for col in range(9):x=32+col*64;y=110+r*64;c.rect(x,y,64,64,'#fff','#b5c9d1',rx=0);c.t(x+32,y+43,grid[r][col],29,anchor='middle')
  c.y=720;c.items(['가로 · 세로 · 대각선으로 연결','찾은 변화의 에너지 출입을 분류'])
 elif kind in ['cipher','cipher-table']:
  jamos=list('ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎㅏㅑㅓㅕㅗㅛㅜㅠㅡㅣ');codes=[''.join(z) for z in itertools.product('1234',repeat=3)];codes=codes[17:]+codes[:17];mapping=dict(zip(jamos,codes));message=list('ㄱㅘㅎㅏㄱㅇㅡㄴㅈㅣㄹㅁㅜㄴㅇㅔㅅㅓㅅㅣㅈㅏㄱ');message='ㄱㅗㅏㅎㅏㄱㅇㅡㄴㅈㅣㄹㅁㅜㄴㅇㅓㅣㅅㅓㅅㅣㅈㅏㄱ';encoded=[mapping[ch] for ch in message]
  if kind=='cipher':
   for j in range(0,len(encoded),4):c.block(f'묶음 {j//4+1}','   '.join(encoded[j:j+4]))
   c.items(['자모를 모아 자연스러운 문장으로 읽기'])
  else:
   for j in range(0,len(jamos),3):c.block('대응','  /  '.join(f'{mapping[ch]} = {ch}' for ch in jamos[j:j+3]))
 elif kind=='board':
  # Two independent rows of numbered cells; arrows have explicit destinations.
  for n,s in enumerate(items):
   x=28+(n%2)*310;y=110+(n//2)*126;c.rect(x,y,284,105,'#fff','#7293a3');c.t(x+15,y+32,str(n+1),22);c.t(x+142,y+72,s,25,anchor='middle')
  c.y=765;c.items(['3번 구리선 → 5번','5번 철 클립 → 7번','6번 고무 → 4번','8번 유리 → 6번','합한 눈만큼 이동 · 10번 이상이면 도착'])
 elif kind=='colorcards':
  for n,s in enumerate(items):
   x=25+(n%2)*310;y=110+(n//2)*120;c.rect(x,y,285,100,'#fff','#738e9c',rx=16);c.circle(x+45,y+50,23,'#fff');c.t(x+91,y+60,s,26)
  c.y=110+math.ceil(len(items)/2)*120;c.items(['초록: 생산자 / 빨강: 소비자 / 파랑: 분해자'])
 elif kind in ['ecosystem','energy','timeline','cycle','reaction','cards']:
  c.items(items)
 else:raise ValueError(kind)
 return c.finish()


if __name__ == '__main__':
    count = 0
    for index, specs in S.items():
        row = rows[index]
        figures = [f for g in row['groups'] for f in g.get('figures', [])]
        assert len(figures) == len(specs), row['id']
        for sequence, spec in enumerate(specs, 1):
            filename = f"{row['id']}-original-{sequence:02}.svg"
            assert figures[sequence-1]['file'] == filename
            (FIG / filename).write_text(render(spec, index, sequence), encoding='utf-8', newline='\n')
            count += 1
    print(json.dumps({'figures': count}))
