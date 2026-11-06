"""Generate all 34 legacy inquiry SVGs from independent specifications and public coordinates."""
from basic import *
# Public-domain coordinate datasets, independent presentation and no imported image.
countries=json.loads((DATA/'natural-earth-countries.geojson').read_text(encoding='utf-8'))['features']
def rings(feature):
 geo=feature['geometry'];return [p[0] for p in geo['coordinates']] if geo['type']=='MultiPolygon' else [geo['coordinates'][0]]
def makegeo(rs,project,fill='#cbdedb',stroke='none'):
 out=''
 for ring in rs:
  coords=[project(lon,lat) for lon,lat,*_ in ring]
  d='M '+' L '.join(f'{x:.2f} {y:.2f}' for x,y in coords)+' Z';out+=path(d,fill,stroke,0.5)
 return out
def world():
 proj=lambda lon,lat:(30+(lon+180)*580/360,100+(90-lat)*290/180)
 b=rect(30,100,580,290,'#f4f8fc','#b7c7d8',0)
 for lon in [-120,-60,0,60,120]:
  x,y=proj(lon,0);b+=line(x,100,x,390,'#d5e0e9',1)+text(x,414,str(lon)+'°',14,GRAY,anchor='middle')
 for lat in [-60,0,60]:
  x,y=proj(0,lat);b+=line(30,y,610,y,'#d5e0e9',1)+text(33,y-4,str(lat)+'°',14,GRAY)
 for f in countries:b+=makegeo(rings(f),proj)
 return b,proj
b,proj=world();volcanoes=json.loads((DATA/'volcanoes.json').read_text(encoding='utf-8'))['features']
for f in volcanoes:
 lon,lat=f['geometry']['coordinates'];x,y=proj(lon,lat);b+=path(f'M {x:.2f} {y-2:.2f} l -2.1 4.2 h 4.2 Z',ORANGE,'none',0)
b+=block(30,455,'삼각형은 최근 약 12,000년 동안 분화한 화산의 위치다. 지금 분화 중이라는 뜻은 아니다.',28,21)
b+=text(30,554,'화산: GVP / Smithsonian VOTW 5.4.0 (2026)',16,GRAY)+text(30,577,'지형: Natural Earth',16,GRAY)
save('0019',1,'지진과 비교할 홀로세 화산의 분포',b,625,alt='홀로세 화산 1,214곳의 위치를 삼각형으로 표시한 세계 지도. 지진 자료와 위치 분포를 비교한다.',footer='GVP: volcano.si.edu')
b,proj=world();plates=json.loads((DATA/'plates.json').read_text(encoding='utf-8'))['features']
for f in plates:
 lines=[f['geometry']['coordinates']] if f['geometry']['type']=='LineString' else f['geometry']['coordinates']
 for ls in lines:
  previous=None
  for lon,lat,*_ in ls:
   p=proj(lon,lat)
   if previous and abs(p[0]-previous[0])<290:b+=line(*previous,*p,BLUE,1.8)
   previous=p
b+=text(30,455,'파랑 선: 주요 판의 경계',23,BLUE)+block(30,496,'화산·지진 자료와 같은 지리 위치에서 비교한다. 미세판의 세부 경계는 생략했다.',29,21)+text(30,586,'경계 좌표: USGS / 지형 좌표: Natural Earth',17,GRAY)
save('0209',1,'주요 판의 경계를 그린 세계지도',b,635,alt='주요 판 경계를 파란 선으로 나타낸 세계 지도. 미세판은 표시하지 않는다.',footer='USGS map_plateboundaries · Natural Earth')
# Continental cut-outs: source geography is independent public-domain coordinate data.
def selected(cont=None,name=None):
 return [r for f in countries if (f['properties'].get('CONTINENT')==cont if cont else f['properties'].get('NAME_EN')==name) for r in rings(f)]
continents=[('남아메리카',selected('South America'),(-60,-15),(160,270)),('아프리카',selected('Africa'),(20,0),(465,270)),('인도',selected(name='India'),(80,23),(145,602)),('오스트레일리아',selected(name='Australia'),(135,-25),(455,610)),('남극',selected(name='Antarctica'),(0,-90),(320,952))]
b=''
for label,rs,origin,center in continents:
 cx,cy=center;lo,la=origin
 def project(lon,lat,cx=cx,cy=cy,lo=lo,la=la):
  phi=math.radians(lat);phi0=math.radians(la);dl=math.radians(lon-lo)
  return (cx+190*math.cos(phi)*math.sin(dl),cy-190*(math.cos(phi0)*math.sin(phi)-math.sin(phi0)*math.cos(phi)*math.cos(dl)))
 b+=makegeo(rs,project,'#e0ece8','none')
 b+=text(cx,cy-132 if label!='인도' else cy-85,label,24,anchor='middle',weight='bold')
 facts={
  '남아메리카':{'G':(-60,-25),'M':(-65,-35),'빙':(-57,-12),'arrow':(-50,-20,-58,-20)},
  '아프리카':{'G':(25,-20),'M':(20,-30),'빙':(20,0),'arrow':(35,-12,35,2)},
  '인도':{'G':(78,18),'빙':(80,28),'arrow':(72,19,78,25)},
  '오스트레일리아':{'G':(135,-25),'빙':(128,-20),'arrow':(145,-18,145,-29)},
  '남극':{'G':(0,-84),'빙':(110,-82)}
 }[label]
 for sym,loc in facts.items():
  if sym=='arrow':
   x1,y1=project(*loc[:2]);x2,y2=project(*loc[2:]);b+=arrow(x1,y1,x2,y2,BLUE,3)
  else:
   x,y=project(*loc);color=TEAL if sym=='G' else ORANGE if sym=='M' else BLUE
   b+=circle(x,y,12,color)+text(x,y+6,sym,17,'white',anchor='middle')
b+=text(30,1150,'G: 글로소프테리스 / M: 메소사우루스 / 빙: 빙하',21)+block(30,1190,'기호는 해당 대륙에 나타난다는 뜻이다. 실제 분포의 경계선이나 빙하의 면적을 나타내지 않는다.',29,20)
for id in ['0018','0082','0208']:
 save(id,1,'대륙 윤곽과 지질학적 단서의 비교 조각',b,1310,alt='남아메리카·아프리카·인도·오스트레일리아·남극. G 화석은 다섯 지역, M 화석은 남아메리카와 아프리카에 나타남을 기호로 표시한다. 파랑 화살표는 빙하가 이동한 방향의 개념 표시다.',footer='Natural Earth · 모든 조각은 같은 반경의 정사영 · 지형 왜곡 있음')
# Independent biodiversity learning game with completely new route and events.
b=''
for i in range(17):
 row,col=divmod(i,4);x=30+col*150;y=82+row*87
 label='출발' if i==0 else '도착' if i==16 else '사건' if i%3==0 else '이동'
 b+=rect(x,y,137,73,'#fff0e7' if label=='사건' else '#edf5f8')+text(x+12,y+26,i,18,GRAY)+text(x+69,y+55,label,23,anchor='middle')
b+=block(30,562,'0부터 16까지 번호 순서로 이동한다. 3·6·9·12·15번에서는 사건 카드를 한 장 읽는다.',29,22)
save('0359',1,'생물다양성 놀이 경로판',b,690,alt='0번 출발에서 16번 도착으로 이동하는 번호판. 3, 6, 9, 12, 15번에 도착하면 사건 카드를 뽑는다.',footer='교육용 게임 모형 · 실제 생태계의 변화를 수치로 예측하지 않음')
rows=[('오염이 누적됨','식물 카드1장과 동물 카드1장을 반납한다.'),('먹이 자원이 줄어듦','동물 카드1장을 반납한다.'),('식물 서식지 개선','추가 카드에서 식물1장을 가져온다.'),('먹이 연결을 회복함','추가 카드에서 동물1장을 가져온다.'),('생물 카드','감자 · 당근 · 밀 · 벼 · 옥수수 · 콩 · 개구리 · 늑대 · 들쥐 · 매 · 메뚜기 · 뱀 · 사슴 · 참새 · 토끼')]
table('0359',2,'사건과 생물 이름으로 만드는 카드',['카드 종류','내용'],rows,alt='오염·먹이 감소·서식지 개선·먹이 연결 회복을 나타내는 네 사건 카드와 열다섯 생물 카드. 사건 카드마다 반납하거나 가져올 생물 카드가 적혀 있다.',footer='카드 증감은 실제 생태계 변화량이 아닌 놀이 약속')
# Conceptual apparent constellation displacement: synthetic markers, no copied sky photo.
b=''
for i,date in enumerate(['8월 1일','8월 16일','8월 31일']):
 y=84+i*190;b+=rect(28,y,584,170,'#f5f8fb')+text(45,y+31,date,23,weight='bold')+line(75,y+130,575,y+130,GRAY,2)+text(82,y+156,'서쪽 지평선',18,GRAY)
 b+=circle(490,y+147,12,'#e8b64b')+text(520,y+153,'태양',18,GRAY)
 x=215+i*115;yy=y+57+i*34;b+=circle(x,yy,13,BLUE)+text(x-5,yy-19,'사자자리',21,BLUE,anchor='middle')
b+=block(30,685,'세 표시를 투명 종이에 옮겨 시간 순서대로 겹친다. 점은 별자리의 상대 위치를 나타낸다.',30,22)
save('0381',1,'해 진 직후의 서쪽 하늘 · 위치 변화 모형',b,790,alt='8월 1일·16일·31일 해 진 직후 서쪽 하늘에서 서쪽 지평선과 사자자리 표식의 위치를 차례로 보여 주는 세 패널.',footer='방향 변화의 학습 모형 · 실제 관측 사진·각도 자료가 아님')
# Zodiac names at equal conceptual spacing; astronomy names are facts, no drawn constellation art.
zodiac=[('처녀자리',0),('사자자리',30),('게자리',60),('쌍둥이자리',90),('황소자리',120),('양자리',150),('물고기자리',180),('물병자리',210),('염소자리',240),('궁수자리',270),('전갈자리',300),('천칭자리',330)]
b=''
for i,(name,deg) in enumerate(sorted(zodiac,key=lambda x:x[1])):
 row,col=divmod(i,2);x=30+col*300;y=84+row*79;b+=rect(x,y,280,64,'#edf4f9')+text(x+140,y+40,name,25,anchor='middle')
b+=block(30,606,'이름 카드를 오려 바탕 판의 같은 이름 자리에 세운다. 글씨는 관측자가 있는 안쪽으로 향하게 한다.',30,22)
save('0382',1,'별자리 이름 카드',b,720,alt='황도를 따라 만나는 열두 별자리의 이름을 적은 카드.',footer='카드의 배치 순서는 바탕 판에 따름')
def zodiac_model(id,title):
 b=circle(320,365,238,'none','#b7c7d8')+circle(320,365,117,'none',GRAY)+circle(320,365,36,'#efd278')+text(320,374,'태양',23,anchor='middle')
 for name,deg in zodiac:
  a=math.radians(deg);x=320+250*math.cos(a);y=365+250*math.sin(a)
  b+=circle(320+235*math.cos(a),365+235*math.sin(a),4,GRAY)
  if deg in [0,180]:b+=text(x,y+30,name,19,anchor='middle')
  else:b+=text(x,y+8,name,19,anchor='middle')
 for name,deg in [('3월',0),('6월',270),('9월',180),('12월',90)]:
  a=math.radians(deg);x=320+117*math.cos(a);y=365+117*math.sin(a);b+=circle(x,y,16,TEAL)+text(x,y+41,name,22,TEAL,anchor='middle')
 b+=block(30,675,'관측자에서 태양을 향한 방향과 그 반대 방향을 각각 비교한다. 카드 이름이 안쪽을 향하게 세운다.',31,21)
 save(id,2 if id=='0382' else 1,title,b,785,alt='가운데에 태양이 있고 오른쪽에 3월, 위에 6월, 왼쪽에 9월, 아래에 12월 관측점이 있다. 바깥 별자리 중 물고기자리는 왼쪽, 쌍둥이자리는 아래, 처녀자리는 오른쪽, 궁수자리는 위에 있다. 실제 별자리 폭과 달리 같은 간격으로 놓은 위치 관계 모형이다.',footer='별자리 폭·공전 궤도의 축척을 단순화한 학습 모형')
zodiac_model('0382','태양과 관측자 · 이름 카드 배치')
zodiac_model('0416','계절에 따라 달라지는 관측 방향')

assert len(META)==34
manifest={f'{k[0]}:{k[1]}':v for k,v in META.items()}
(Path(__file__).resolve().parent/'manifest.json').write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(f'Generated {len(META)} independent SVGs in {OUT}')
