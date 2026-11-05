"""Independently authored diagrams. Imported by build.py; no textbook input needed."""
from pathlib import Path
from html import escape
import math,json,re
ROOT=Path(__file__).resolve().parents[3]
DATA=Path(__file__).resolve().parent / "data"
OUT=ROOT/'site/dist/procedure-figures'
OUT.mkdir(parents=True,exist_ok=True)
META={}
INK='#24364b'; BLUE='#2563a6'; TEAL='#11756c'; ORANGE='#b84d22'; GRAY='#64748b'
def text(x,y,s,size=23,color=INK,anchor='start',weight='normal'):
 return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{escape(str(s))}</text>'
def rect(x,y,w,h,fill='#f1f5f9',stroke='#b7c7d8',rx=10):return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
def line(x1,y1,x2,y2,color=INK,width=3,dash=None):return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>'
def path(d,fill='none',stroke=INK,width=3,dash=None):return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>'
def circle(x,y,r,fill=BLUE,stroke='none'):return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
def arrow(x1,y1,x2,y2,color=BLUE,width=4):
 a=math.atan2(y2-y1,x2-x1);L=12
 p1=(x2-L*math.cos(a-.4),y2-L*math.sin(a-.4));p2=(x2-L*math.cos(a+.4),y2-L*math.sin(a+.4))
 return line(x1,y1,x2,y2,color,width)+path(f'M {p1[0]} {p1[1]} L {x2} {y2} L {p2[0]} {p2[1]}','none',color,width)
def wrap(s,limit=23):
 lines=[];current=''
 for word in s.split(' '):
  if len(current)+len(word)>limit and current:lines.append(current);current=word
  else:current+=((' ' if current else '')+word)
 if current:lines.append(current)
 return lines
def block(x,y,s,width=23,size=23,color=INK):return ''.join(text(x,y+i*(size+10),v,size,color) for i,v in enumerate(wrap(s,width)))
def save(id,n,title,body,h=520,caption=None,alt=None,footer='직접 구성한 학습용 도식 · 크기와 거리는 실제 비율이 아님'):
 name=f'activity_{id}-original-{n:02}.svg'
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 {h}" role="img"><title>{escape(title)}</title><style>text{{font-family:Arial,"Malgun Gothic",sans-serif}}path,line{{stroke-linecap:round;stroke-linejoin:round}}</style><rect width="640" height="{h}" fill="white"/>'+text(26,40,title,27,INK,weight='bold')+line(26,56,614,56,'#dce5ee',2)+body+text(26,h-16,footer,14,GRAY)+'</svg>'
 (OUT/name).write_bytes(svg.encode('utf-8'))
 META[(f'activity_{id}',n)]={'file':name,'caption':caption or title,'alt':alt or title}
def table(id,n,title,headers,rows,caption=None,alt=None,footer='직접 구성한 비교표 · 제시된 조건을 읽고 판단하기'):
 widths=[150,438] if len(headers)==2 else [196]*3
 y=75;b='';x=26
 for header,w in zip(headers,widths):b+=rect(x,y,w,54,'#e6f0f8',rx=0)+text(x+12,y+35,header,23,weight='bold');x+=w
 y+=54
 for row in rows:
  chunks=[wrap(v,max(6,int(w/23)-2)) for v,w in zip(row,widths)];height=max(map(len,chunks))*31+22;x=26
  for cell,w in zip(chunks,widths):
   b+=rect(x,y,w,height,'white',rx=0)
   for j,t in enumerate(cell):b+=text(x+12,y+30+j*31,t,22)
   x+=w
  y+=height
 save(id,n,title,b,y+50,caption,alt,footer)
# Nine material cards: quantitative facts, new text-first arrangement; no photographs.
rows=[('A · 흰 가루','50 g과 100 g을 각각 가열하면 녹는 온도는 모두 185 ℃이다.'),('B · 투명 고체','20 g과 50 g의 가열 곡선에서 녹는 동안의 온도는 모두 0 ℃이다.'),('C · 투명 액체','냉각 중 얼기 시작한 이후에도 온도가 계속 내려간다.'),('D · 투명 액체','10 mL와 45 mL의 끓는점은 모두 78.5 ℃이다.'),('E · 투명 액체','페트병 뚜껑을 열면 기포가 많이 생긴다.'),('F · 투명 액체','78.5 ℃에서 끓기 시작한 뒤에도 온도가 계속 올라간다.'),('G · 주황 액체','위층 20 mL는 25 g, 건더기가 내려앉은 아래층 20 mL는 28 g이다.'),('H · 흰 가루','16.4 g의 부피는 10 mL, 32.8 g의 부피는 20 mL이다.'),('I · 흰 가루','물 50 g에 최대로 18 g이 녹는다. 물 100 g에 80 g을 넣으면 44 g이 녹지 않는다.')]
table('0006',1,'분류 카드 A–I',['카드','비교에 사용할 사실'],rows,alt='아홉 물질의 녹는점, 끓는점, 밀도와 용해도 정보를 글로 정리한 카드. 그래프나 사진을 복사하지 않았다.')
# New game route, simple numbered grid; no former illustration or route geometry.
labels=['출발','질문','지권 찾기','암석','질문','기권 찾기','공기','질문','수권 찾기','바닷물','질문','생물권 찾기','나무','질문','외권 찾기','태양','질문','질문','질문','도착']
b=''
for i,label in enumerate(labels):
 row,col=divmod(i,4);x=26+col*149;y=78+row*99
 b+=rect(x,y,140,83,'#eef7f4' if label in ['암석','공기','바닷물','나무','태양'] else '#f2f5fa')+text(x+10,y+25,i,17,GRAY)+text(x+70,y+58,label,21,anchor='middle')
b+=block(30,605,'번호가 커지는 방향으로 이동한다. 찾기 칸에서는 해당 영역의 예가 적힌 빈자리로 이동한다.',31,21)
save('0011',1,'지구계 분류 놀이 · 새로 구성한 판',b,730,alt='0부터 19까지 번호 순서로 진행하는 새 놀이판. 암석, 공기, 바닷물, 나무, 태양 칸은 각각 지권, 기권, 수권, 생물권, 외권의 예다.',footer='독립 설계한 놀이 모형 · 질문 카드는 조사하여 작성')
table('0017',1,'실물 암석 관찰 기록지',['표본','돋보기·염산 관찰 기록'],[(str(i),'색: ______  알갱이: ______ 무늬: ______  염산 반응: ______') for i in range(1,7)],alt='여섯 실물 표본의 색, 알갱이, 무늬, 염산 반응을 직접 적는 빈 기록지.',footer='실물 표본으로 관찰하기 · 사진을 대신하는 예시 결과가 아님')
# Electrophoresis strip.
b=path('M 75 130 H 220 V 220 H 420 V 130 H 565 V 380 H 420 V 290 H 220 V 380 H 75 Z','#e8f3ef',TEAL)
for x in [290,320,350]:b+=line(x,220,x,290,INK,2)
b+=text(320,110,'받침 유리 위에 놓을 거름종이',23,anchor='middle')+text(320,332,'평행한 연필선 3개',22,anchor='middle')+arrow(320,355,320,288)+text(320,398,'가운데 선에 시료',23,anchor='middle')+text(95,425,'전원 집게',22)+text(438,425,'전원 집게',22)
save('0040',1,'이온 이동을 볼 종이의 구조',b,480,alt='가운데가 좁고 양끝이 넓은 종이에 세 평행선을 그린다. 시료는 가운데 선, 전원 집게는 양끝에 연결한다.')
# Digestion: completely new worksheet layout with text cards.
b='';heads=['기관','녹말','단백질','지방']
for i,h in enumerate(heads):b+=rect(26+i*147,78,147,48,'#e6f0f8',rx=0)+text(99+i*147,109,h,23,anchor='middle')
for j,organ in enumerate(['입을 지난 뒤','위를 지난 뒤','작은창자 끝']):
 for i in range(4):
  b+=rect(26+i*147,126+j*78,147,78,'white',rx=0)
  b+=text(99+i*147,171+j*78,organ if i==0 else '카드 놓기',20,anchor='middle')
b+=text(26,400,'잘라 쓸 글자 카드 · 필요한 수만큼 준비',22,weight='bold')
cards=['녹말','엿당','포도당','단백질','짧은 단백질 조각','아미노산','지방','지방산·모노글리세리드']
for i,c in enumerate(cards):
 x=26+(i%2)*294;y=422+(i//2)*60;b+=rect(x,y,282,50,'#f4f8f6')+text(x+141,y+33,c,21,anchor='middle')
save('0047',1,'영양소가 지나온 기관별로 카드 놓기',b,720,alt='입, 위, 작은창자 이후의 상태를 녹말·단백질·지방별로 채우는 빈 표와 여덟 종류의 글자 카드.',footer='독립 설계한 학습 놀이 · 같은 카드를 여러 칸에 쓸 수 있음')
# Parallax board from scratch, view from above.
b=rect(76,106,488,350,'#f7fafc')+rect(76,106,488,40,'#d8e6ed')+text(320,135,'뒤쪽 벽 · 보이는 위치 표시',22,anchor='middle')+rect(76,416,488,40,'#d8e6ed')
b+=circle(236,436,11,'white',INK)+circle(404,436,11,'white',INK)+text(320,490,'앞쪽 벽의 두 관찰 구멍',22,anchor='middle')+circle(320,330,11,ORANGE)+text(345,337,'가까운 S',23)+circle(320,225,11,TEAL)+text(345,232,'먼 T',23)+line(320,152,320,410,GRAY,2,'6 7')
save('0060',1,'별 모형과 두 관찰 구멍 · 위에서 본 배치',b,540,alt='앞 벽의 두 구멍 중간에서 뒤벽으로 향하는 선 위에 가까운 S와 먼 T를 배치한다. 뒤벽에 각각 보이는 위치를 표시한다.')
table('0062',1,'계절별 은하수 사진 비교 기록',['확인할 것','각 사진에 적을 내용'],[('촬영 조건','우리나라 촬영 여부와 날짜·계절을 확인한다.'),('여름 자료','은하수 띠의 밝기·폭·보이는 방향을 기록한다.'),('겨울 자료','같은 항목을 기록하고 여름 자료와 대조한다.')],alt='직접 수집한 은하수 사진의 촬영 계절과 띠의 밝기·폭을 기록하는 안내표.',footer='실제 사진은 출처와 촬영 계절을 확인하여 직접 조사')
table('0062',2,'사진을 비교할 때 확인할 조건',['조건','비교할 내용'],[('관측 장소','우리나라에서 촬영한 자료인지'),('관측 시기','여름·겨울 중 어느 계절인지'),('보이는 띠','상대적인 밝기와 넓이'),('사진 정보','촬영·보정 조건이 달라 보일 가능성')],alt='여름·겨울 은하수 사진을 비교할 때 점검하는 빈 관찰 안내. 관측 사진이나 측정 결과가 아니다.',footer='직접 구성한 관찰 안내 · 실제 관측값을 제시한 그림이 아님')
# Star colors, representing categories not recreating photographs.
stars=[('스피카','청백색','#d5eaff'),('리겔','청백색','#d5eaff'),('베가','흰색','#fafafa'),('알데바란','주황색','#ed9a44'),('베텔게우스','붉은빛','#d65837'),('안타레스','붉은빛','#c94432')]
b=''
for i,(name,col,fill) in enumerate(stars):
 y=80+i*67;b+=rect(26,y,588,57,'#fafbfd')+circle(66,y+28,19,fill,'#8b98a7')+text(106,y+36,name,24)+text(360,y+36,col,23)
save('0122',1,'별의 색을 나타낸 비교 모형',b,540,alt='스피카·리겔은 청백색, 베가는 흰색, 알데바란은 주황색, 베텔게우스·안타레스는 붉은빛으로 나타낸 색 범주표.',footer='색 범주의 개념 표시 · 실제 천체 사진이나 정밀 색 측정값이 아님')
# Qualitative solubility curve, anchored to visible chart facts.
b=arrow(82,395,594,395,GRAY,2)+arrow(82,395,82,105,GRAY,2)+text(338,449,'온도 증가 →',24,anchor='middle')+text(36,86,'용해도',23)+text(95,115,'물 100 g에 녹는 질량',20,GRAY)
b+=path('M 98 360 C 220 325 330 250 424 118','none',BLUE,5)+path('M 98 301 C 270 298 430 293 580 288','none',TEAL,5)
b+=text(402,180,'질산 칼륨',23,BLUE)+text(395,333,'염화 나트륨',23,TEAL)+block(110,490,'기울기와 상대적인 변화량을 비교한다. 정확한 용해도 값은 이 개념도에서 읽지 않는다.',23,21)
save('0133',1,'온도가 변할 때 두 용질의 용해도 경향',b,600,alt='질산 칼륨의 용해도는 온도에 따라 크게 증가하고 염화 나트륨은 조금 증가하는 경향을 표시한 개념 그래프. 눈금값은 제시하지 않는다.',footer='정량 측정 그래프가 아닌 경향 모형')
# Temperature-color concept.
b=arrow(70,123,566,123,GRAY,3)+text(320,101,'가열이 진행되는 방향',24,anchor='middle')
for i,(color,name) in enumerate([('#ad3826','붉은빛'),('#e77c27','주황빛'),('#fff2b0','황백색 빛')]):
 x=44+i*200;b+=rect(x,160,180,190,'#e8eef4')
 pts=' '.join(f'{x+26+j*12},{245+30*math.sin(j*math.pi/2)}' for j in range(11));b+=f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="11"/>'+text(x+90,389,name,23,anchor='middle')
save('0184',1,'니크롬선이 내는 빛의 색 변화 모형',b,465,alt='가열이 진행되며 붉은빛에서 주황빛, 황백색 빛으로 바뀌는 경향만 표시한 모형. 실제 전기난로 사진이나 온도 측정값이 아니다.',footer='원자료에서 확인한 색 변화의 개념 표시 · 온도 눈금 없음')
# Ethanol heating graph with new separate panels rather than copied path.
b=''
for i,(lab,xend) in enumerate([('10 mL',265),('20 mL',365)]):
 y0=248+i*205;b+=arrow(90,y0,580,y0,GRAY,2)+arrow(90,y0,90,y0-150,GRAY,2)+text(30,y0-145,'온도',18)+text(320,y0+35,'가열 시간 →',21,anchor='middle')+line(90,y0-112,580,y0-112,GRAY,1,'5 5')+text(31,y0-104,'78 ℃',19)
 b+=path(f'M 98 {y0-20} L {xend} {y0-112} H 570','none',BLUE if i==0 else TEAL,5)+text(450,y0-135,lab,24,BLUE if i==0 else TEAL)
save('0194',1,'서로 다른 양의 에탄올 가열 경향',b,520,alt='10 mL는 20 mL보다 먼저 온도 상승이 멈추지만 두 경우 모두 78 ℃에서 평평해지는 경향을 별도 패널로 나타냈다.',footer='시간 눈금 없는 경향 모형 · 두 패널의 가로 시간 범위는 같음')
# Rays, reflection and refraction; no outgoing answer ray.
for n,water in [(1,False),(2,True)]:
 b=''
 if water:b+=path('M 100 280 A 220 180 0 0 0 540 280 Z','#d9eff6',BLUE,3)+text(450,360,'물',25,BLUE)
 b+=line(95,280,545,280,INK,6)+line(320,90,320,455,GRAY,2,'8 7')+text(330,90,'법선 · 0°',23)+text(475,250,'공기',23)
 for angle,ylab,col in [(60,180,ORANGE),(30,125,TEAL)]:
  length=220;xx=320-length*math.sin(math.radians(angle));yy=280-length*math.cos(math.radians(angle));b+=arrow(xx,yy,320,280,col,4)+circle(xx,yy,9,col)+text(xx-9,yy-20,f'{angle}°',23,col,anchor='middle')
 b+=circle(320,280,7,INK)+text(320,490,'두 빛 모두 면의 가운데 한 점으로 향하게 한다.',21,anchor='middle')
 save('0210',n,'반원형 접시의 입사 위치' if water else '평면거울의 입사 위치',b,540,alt=('곧은 면 아래는 물, 위는 공기다. ' if water else '평면거울 앞쪽에 광원을 놓는다. ')+'면과 수직인 법선에서 각각 60°, 30°인 방향의 빛이 중앙점으로 들어간다. 반사광·굴절광은 직접 관찰한다.')
# Idealized tone wave, no fake measured sound.
b=arrow(65,270,590,270,GRAY,2)+arrow(65,400,65,110,GRAY,2)+text(430,315,'같은 시간 범위',23)+text(50,93,'진동',23)
points=' '.join(f'{80+i*2.4:.1f},{270-75*math.sin(i*2*math.pi/50):.1f}' for i in range(201))
b+=f'<polyline points="{points}" fill="none" stroke="{BLUE}" stroke-width="4"/>'+block(80,445,'이상화한 솔 파형을 기준으로 진폭과 진동수를 비교한다. 실제 악기의 녹음 파형은 아니다.',31,21)
save('0220',1,'소리 비교를 위한 기준 파동 모형',b,560,alt='한 시간 범위에 네 주기가 들어 있는 이상화한 주기파. 진폭과 진동수 비교를 위한 모형이며 실측 음원 파형이 아니다.')
# Periodic tables by true coordinates.
b='';groups=[1,2,13,14,15,16,17,18];names={(1,18):'He',(2,1):'Li',(2,16):'O',(2,17):'F',(2,18):'Ne',(3,1):'Na',(3,13):'Al',(3,18):'Ar',(4,1):'K'}
for i,g in enumerate(groups):b+=text(100+i*68,109,str(g),22,anchor='middle')
for p in range(1,5):
 b+=text(30,140+p*67,f'{p}',23)
 for i,g in enumerate(groups):
  if p==1 and g not in [1,18]:continue
  x=68+i*68;y=110+p*67;b+=rect(x,y,63,58,'#eef4f8')+text(x+31,y+38,names.get((p,g),''),24,anchor='middle')
b+=text(320,465,'가로줄: 주기 / 세로줄: 족',23,anchor='middle')
save('0225',1,'원소 카드의 주기와 족',b,520,alt='He 1주기18족, Li 2주기1족, O 2주기16족, F 2주기17족, Ne 2주기18족, Na 3주기1족, Al 3주기13족, Ar 3주기18족, K 4주기1족.',footer='주기율표의 과학적 위치 관계를 새로 배열한 도식')
table('0226',1,'같은 족에서 위아래로 이어지는 원소',['주기','1족 / 18족'],[('1','수소 / 헬륨'),('2','리튬 / 네온'),('3','나트륨 / 아르곤'),('4','칼륨 / 크립톤'),('5','루비듐 / 제논'),('6','세슘 / 라돈')],alt='1족과18족 원소의 위치만 뽑아 비교한 독립 표.')
# Heart circuit, new functional rather than anatomical tracing.
b=rect(188,80,264,65,'#eef4f8')+text(320,122,'허파',27,anchor='middle')+rect(188,450,264,65,'#eef4f8')+text(320,492,'온몸',27,anchor='middle')
for name,x,y,col in [('우심방',80,310,BLUE),('우심실',80,210,BLUE),('좌심방',392,210,ORANGE),('좌심실',392,310,ORANGE)]:
 b+=rect(x,y,168,65,'white',col)+text(x+84,y+42,name,26,anchor='middle')+circle(x+84,y+13,5,col)
b+=arrow(188,481,164,375,BLUE)+arrow(164,310,164,275,BLUE)+arrow(164,210,228,145,BLUE)+arrow(412,145,476,210,ORANGE)+arrow(476,275,476,310,ORANGE)+arrow(476,375,450,481,ORANGE)
b+=text(53,430,'대정맥',21,BLUE)+text(51,170,'폐동맥',21,BLUE)+text(490,170,'폐정맥',21,ORANGE)+text(495,430,'대동맥',21,ORANGE)
save('0239',1,'혈액 이동을 실로 연결하는 경로판',b,575,alt='온몸에서 대정맥을 지나 우심방·우심실·폐동맥·허파로 이어지고, 폐정맥·좌심방·좌심실·대동맥을 거쳐 온몸으로 돌아오는 순환 경로. 각 점에 실을 꿰어 연결한다.',footer='실제 심장 형태와 다른 경로 모형 · 점에 구멍을 내어 실로 연결')
# Three tangent circles with deleted inner arcs explicitly distinguished.
b='';cx,cy=320,270;r=82;centers=[(320,175),(238,317),(402,317)]
b+=circle(cx,cy,177,'none','#d6dfe8')
for x,y in centers:b+=circle(x,y,r,'none',BLUE)
b+=text(320,80,'세 작은 원이 서로 닿게 배치',23,anchor='middle')+text(320,493,'바깥 원과 중심 틈 쪽의 호를 지운다.',23,anchor='middle')
# Cover and distinguish central arcs to erase, not an invented contour.
b+=path('M 279 246 A 82 82 0 0 0 361 246 M 279 246 A 82 82 0 0 1 320 317 M 361 246 A 82 82 0 0 0 320 317','none',ORANGE,5,'6 5')
b+=f'<circle cx="{cx}" cy="{cy}" r="177" fill="none" stroke="{ORANGE}" stroke-width="3" stroke-dasharray="6 6"/>'+text(320,529,'주황 점선: 지울 선 / 파랑: 남길 테두리',20,anchor='middle')
save('0240',1,'같은 바깥 크기에서 테두리 길이 비교',b,580,alt='작은 원 세 개가 서로 외접한다. 바깥의 큰 원과 작은 원들이 둘러싼 가운데 틈의 호는 지울 부분이다.')
# Bottle cross section for rings / tape.
b=rect(170,145,300,255,'#f4f8fa',BLUE,60)+rect(273,92,94,58,'#e1eaf2',BLUE,8)+line(320,67,320,235,TEAL,12)
b+=f'<ellipse cx="320" cy="280" rx="55" ry="76" fill="#fde5cf" stroke="{ORANGE}" stroke-width="3"/>'
for y in [198,248,298,348]:b+=f'<ellipse cx="320" cy="{y}" rx="166" ry="27" fill="none" stroke="#798797" stroke-width="4"/>'
b+=rect(450,176,22,199,'#cbd5e1',GRAY,1)+circle(176,275,9,'white',BLUE)+text(27,119,'빨대',23)+arrow(85,116,306,107,TEAL,2)+text(24,450,'옆면 구멍',23)+arrow(92,420,173,288,BLUE,2)+text(418,450,'반대쪽 테이프',21)+arrow(480,420,464,372,GRAY,2)+text(320,503,'마지막에 병과 고리 위로 실험용 장갑을 씌운다.',20,anchor='middle')
save('0241',1,'호흡 모형의 고리와 고정 위치',b,555,alt='세운 병 안에 빨대와 풍선을 놓고 몸통을 쇠고리로 감싼다. 옆면 구멍 반대쪽에서 여러 고리를 테이프로 고정한 뒤 장갑을 씌운다.')
# New portrait parallax construction: observing baseline below, reference plane above.
b=line(65,120,575,120,GRAY,2)+text(320,91,'멀리 있는 기준 배경',23,anchor='middle')+line(175,430,465,430,TEAL,2)+circle(175,430,10,TEAL)+circle(465,430,10,TEAL)+text(175,472,'첫 관측점',23,anchor='middle')+text(465,472,'둘째 관측점',23,anchor='middle')+circle(320,430,12,ORANGE)+text(320,466,'태양',21,anchor='middle')
# First viewpoint is left; A1 right, A2 left. Rays intersect at central nearer A, farther B.
for lab,x in [('A₂',90),('B₂',220),('B₁',420),('A₁',550)]:b+=circle(x,120,8,BLUE)+text(x,159,lab,24,anchor='middle')
b+=block(75,525,'각 관측점에서 같은 번호의 A, B 표식을 향해 선을 그어 별의 위치를 찾는다.',30,21)
save('0256',1,'관측 위치가 달라질 때 보이는 방향',b,620,alt='아래에 첫 관측점과 둘째 관측점, 위 배경에 왼쪽부터 A₂,B₂,B₁,A₁이 있다. 같은 번호끼리 선을 연결하면 A의 교점이 B보다 관측자 가까이에 놓인다.')
# Dropper schematic, no photo.
b=rect(292,100,56,130,'#e4eff7',BLUE,10)+path('M 304 230 L 320 278 L 336 230','#e4eff7',BLUE)+circle(320,323,9,BLUE)+f'<ellipse cx="320" cy="415" rx="190" ry="48" fill="#eaf3f8" stroke="{BLUE}" stroke-width="3"/>'+rect(281,355,78,68,'#eed9a4','#9e8246',6)+text(400,162,'물',25,BLUE)+text(400,391,'사탕',25)+text(320,502,'접시 속 사탕에 물방울이 닿는 상황',22,anchor='middle')
save('0277',1,'물과 사탕으로 생각하는 변화',b,550,alt='스포이트에서 나오는 물방울이 접시 안의 사탕에 떨어지는 상황을 단순 도형으로 나타냈다. 변화 결과는 그리지 않았다.')
# Helicopter assembled shape: own front/oblique sketch.
b=path('M 320 220 L 80 170 L 80 112 L 320 160 L 560 112 L 560 170 Z','#dcefe9',TEAL,3)+rect(290,220,60,200,'#dcefe9',TEAL,2)+rect(306,392,28,76,'none',INK,11)+text(81,90,'왼쪽 날개',23)+text(438,90,'오른쪽 날개',23)+text(382,318,'꼬리',23)+text(382,441,'클립',23)+text(320,517,'두 날개는 반대 방향으로 접어 펼친다.',22,anchor='middle')
save('0419',1,'종이 헬리콥터의 구성 요소',b,565,alt='양쪽으로 펼친 두 날개 아래로 꼬리가 내려오고, 꼬리 끝에는 클립을 끼운 독립 구조도.')
