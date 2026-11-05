from pathlib import Path
import json, math, html, textwrap

ROOT=Path(__file__).resolve().parents[3]
INPUT=Path(__file__).resolve().parent
OUT=ROOT/'site/dist/procedure-figures'
rows=json.loads((INPUT/'activity-ids.json').read_text(encoding='utf-8'))
manifest={}
W=600

def esc(s): return html.escape(str(s),quote=True)
def txt(x,y,s,size=23,color='#21394a',anchor='start',weight='normal'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{esc(s)}</text>'
def rect(x,y,w,h,fill='#eaf2f4',stroke='none',rx=12):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>'
def line(x1,y1,x2,y2,c='#416b7d',dash='',width=3):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>'
def arrow(x1,y1,x2,y2,c='#1c7a88'):
    a=math.atan2(y2-y1,x2-x1);r=11
    p=[(x2,y2),(x2-r*math.cos(a-.45),y2-r*math.sin(a-.45)),(x2-r*math.cos(a+.45),y2-r*math.sin(a+.45))]
    return line(x1,y1,x2,y2,c)+f'<polygon points="'+ ' '.join(f'{x:.1f},{y:.1f}' for x,y in p)+f'" fill="{c}"/>'
def circle(x,y,r,fill,stroke='none'):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>'
def path(d,c='#416b7d',fill='none',width=3):
    return f'<path d="{d}" fill="{fill}" stroke="{c}" stroke-width="{width}"/>'
def para(x,y,s,chars=24,size=23,gap=33):
    parts=[]
    for j,a in enumerate(textwrap.wrap(s,width=chars,break_long_words=False,break_on_hyphens=False) or ['']):parts.append(txt(x,y+j*gap,a,size))
    return ''.join(parts), max(1,len(parts))*gap
def save(i,title,body,h,caption,alt,n=1):
    name=f"{rows[i]['id']}-original-{n:02}.svg"
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" role="img" aria-labelledby="title desc"><title id="title">{esc(title)}</title><desc id="desc">{esc(alt)}</desc><rect width="{W}" height="{h}" fill="#fff"/><g font-family="Malgun Gothic, Apple SD Gothic Neo, sans-serif">'+txt(28,44,title,28,weight='bold')+body+'</g></svg>\n'
    (OUT/name).write_bytes(svg.encode('utf-8'))
    manifest.setdefault(str(i),[]).append(dict(file=name,caption=caption,alt=alt))
def cards(i,title,items,caption=None,alt=None,footer=None):
    y=75;body=''
    for head,content in items:
        a,height=para(44,y+65,content,chars=24,size=23)
        h=height+80;body+=rect(25,y,550,h)+txt(44,y+33,head,24,weight='bold')+a;y+=h+14
    if footer:
        p,hh=para(30,y+20,footer,chars=30,size=19,gap=28);body+=p;y+=hh+32
    save(i,title,body,y+15,caption or title,alt or ' '.join(f'{a}: {b}' for a,b in items))

# Cell representations use elementary geometry, not the source illustration.
b=txt(30,93,'동물 세포',25,weight='bold')+txt(330,93,'식물 세포',25,weight='bold')
b+=f'<ellipse cx="150" cy="210" rx="116" ry="92" fill="#eff4fa" stroke="#4582ab" stroke-width="4"/>'
b+=rect(320,115,245,192,'#f1f8ed','#629457',24)+rect(331,126,223,170,'none','#4582ab',19)
b+=circle(143,203,33,'#e3cbed','#86569b')+circle(433,210,33,'#e3cbed','#86569b')
for x,y in [(83,190),(213,245),(380,165),(500,258)]:b+=f'<ellipse cx="{x}" cy="{y}" rx="19" ry="10" fill="#efb584"/>'
for x,y in [(363,250),(510,165),(469,145)]:b+=f'<ellipse cx="{x}" cy="{y}" rx="17" ry="10" fill="#81b66b"/>'
for y,color,label in [(350,'#e3cbed','핵'),(393,'#efb584','미토콘드리아'),(436,'#81b66b','엽록체')]:b+=circle(45,y-7,10,color)+txt(70,y,label)
b+=txt(28,485,'파란 경계: 세포막 / 식물의 바깥 경계: 세포벽',20)+txt(28,523,'비율과 개수는 실제 세포와 다른 구조 모형',19)
save(10,'세포에서 찾아볼 구조',b,550,'동물·식물 세포의 구조 모형','공통 구조는 핵·세포막·미토콘드리아이며 식물 세포에는 세포벽과 엽록체도 표시한 독립 개념도. 실제 크기·개수 비율은 아니다.')
cards(72,'태양 관측 기록 안내',[('관측 영상 선택','우주환경센터에서 같은 관측 방식의 서로 다른 시각 영상을 찾는다.'),('각 영상에 남길 정보','촬영 시각, 밝은 영역과 어두운 영역, 표면·대기 현상 여부를 기록한다.'),('비교할 항목','같은 영역의 밝기와 무늬가 시점에 따라 달라지는지 비교한다.')],caption='태양 영상 비교를 위한 기록 틀',footer='관측 사진이 아닌 조사 안내 도식')

b=circle(300,285,43,'#ffe5a4')+txt(300,294,'전등',22,anchor='middle')+f'<circle cx="300" cy="285" r="125" fill="none" stroke="#b8cbd3" stroke-dasharray="9 7" stroke-width="3"/>'
for x,y,label in [(300,112,'물고기자리'),(490,291,'쌍둥이자리'),(300,491,'처녀자리'),(102,291,'궁수자리')]:b+=txt(x,y,label,22,anchor='middle')
b+=circle(300,160,13,'#258d98')+arrow(300,160,300,234)+arrow(300,160,300,122)+txt(300,544,'네 자리는 90° 간격 · 눈높이 동일',22,anchor='middle')
b+=txt(300,581,'관찰자는 안쪽 원을 따라 이동',22,anchor='middle')
save(76,'계절에 따른 관찰 자리',b,610,'위에서 내려다본 공전 관찰 모형','중앙 전등 주위 네 방향에 별자리 표지를 두고 관찰자는 그 안쪽 원을 따라 90도씩 이동한다. 별자리 그림 자체는 제공하지 않는다.')

cards(88,'물질별 특성 기록',[('구리선','물에 녹지 않음 / 밀도 8.96 g/cm³ / 녹는점 1085 ℃ / 끓는점 2562 ℃'),('간장','물과 섞임 / 밀도는 성분 비율에 따라 다름 / 녹는점·끓는점 일정하지 않음'),('산소','물 100 g에 0.0044 g 용해 / 밀도 1.429 g/L / 녹는점 −219 ℃ / 끓는점 −183 ℃'),('동전','물에 녹지 않음 / 밀도는 성분 비율에 따라 다름 / 녹는점·끓는점 일정하지 않음')],footer='용해도: 20 ℃의 물 기준 / 밀도: 0 ℃ 기준. 물질 특성값을 비교하는 자료이며 사진·실측 결과표가 아니다.')

b='';ys=[95,280,465]
for k,(y,label) in enumerate(zip(ys,['제주 대포 해안: 기둥 모양의 암석','부안 채석강: 나란히 이어진 층','화성 우음도: 굽어 있는 줄무늬'])):
    b+=rect(25,y,550,165)+txt(43,y+34,label,22,weight='bold')
    if k==0:
        for j in range(7):b+=path(f'M {75+j*64} {y+140} V {y+80} l 22 -16 l 22 16 V {y+140}',fill='#afc0c7')
    elif k==1:
        for z in range(5):b+=path(f'M 50 {y+67+z*17} L 180 {y+62+z*17} L 340 {y+71+z*17} L 550 {y+65+z*17}',width=6)
    else:
        for z in range(5):b+=path(f'M 50 {y+70+z*15} C 170 {y+160+z*8}, 260 {y+35+z*8}, 365 {y+91+z*12} S 485 {y+135+z*5}, 550 {y+70+z*15}',width=4)
b+=txt(30,665,'사진의 관찰 특징을 비교하는 비축척 모형',20)
save(98,'암석에서 구별할 형태',b,695,'세 지역 암석의 특징을 나타낸 개념도','대포 해안의 기둥 모양, 채석강의 층, 우음도의 굽은 줄무늬를 각각 추상 도형으로 표현한 모형이며 현장 사진이나 원본 구도를 재현한 그림이 아니다.')

cards(99,'암석의 변화 경로',[('마그마 → 화성암','냉각되어 굳음'),('암석 → 퇴적물','풍화·침식·운반'),('퇴적물 → 퇴적암','퇴적물이 굳음'),('암석 → 변성암','높은 열과 압력'),('암석 → 마그마','녹음')],caption='암석 순환 경로를 읽는 연결표',footer='놀이판 배열을 대신한 독립 경로표. 해당 경로를 설명하며 말을 상태 사이에서 옮긴다.')
cards(101,'암석에서 토양까지',[('관찰 대상 1 · 산 사면','크기가 서로 다른 암석 조각들이 모여 있다. 조각이 생기는 과정을 생각한다.'),('관찰 대상 2 · 제주 밭','흑갈색 토양이 분포한다. 주변 암석과의 관계를 생각한다.'),('설명에 포함할 변화','암석의 풍화, 조각의 생성, 토양의 형성을 세 장면으로 연결한다.')],caption='암석·토양 특징을 비교하는 설명 자료',footer='실제 사진을 재현하지 않은 관찰 특징 정리')

# Public-domain geographic coordinates. Do not reproduce textbook fossil/color bands.
geo=json.loads((INPUT/'natural-earth-countries.json').read_text(encoding='utf-8'))
def polys(features):
    for f in features:
        g=f['geometry']
        if g['type']=='Polygon':yield g['coordinates'][0]
        elif g['type']=='MultiPolygon':
            for p in g['coordinates']:yield p[0]
def geopath(ps,x,y,w,h):
    coords=[(a,b) for p in ps for a,b,*_ in p]
    xmin=min(z[0] for z in coords);xmax=max(z[0] for z in coords);ymin=min(z[1] for z in coords);ymax=max(z[1] for z in coords)
    scale=min(w/(xmax-xmin),h/(ymax-ymin));ox=x+(w-(xmax-xmin)*scale)/2;oy=y+(h-(ymax-ymin)*scale)/2
    return ''.join('M '+' L '.join(f'{ox+(a-xmin)*scale:.1f},{oy+(ymax-b)*scale:.1f}' for a,b,*_ in p)+' Z ' for p in ps)
parts=[('아프리카',lambda p:p.get('CONTINENT')=='Africa'),('남아메리카',lambda p:p.get('CONTINENT')=='South America'),('인도',lambda p:p.get('NAME_EN')=='India'),('오스트레일리아',lambda p:p.get('NAME_EN')=='Australia'),('남극',lambda p:p.get('CONTINENT')=='Antarctica')]
b=''
for j,(label,test) in enumerate(parts):
    yy=82+j*185;b+=rect(25,yy,550,172)+txt(45,yy+40,label,24,weight='bold')
    ps=list(polys([f for f in geo['features'] if test(f['properties'])]))
    if label=='남극':
        ps=[[(math.cos(math.radians(lon))*(90+lat),math.sin(math.radians(lon))*(90+lat)) for lon,lat,*_ in p] for p in ps]
    b+=path(geopath(ps,270,yy+15,270,145),'none','#89b1bd',0)
b+=txt(27,1050,'조각별 표시 크기는 서로 같은 축척이 아님',20)+txt(27,1082,'공개 지리 좌표: Natural Earth (public domain)',18)
save(102,'자연 해안선 비교 자료',b,1110,'대륙 윤곽 비교용 독립 자료','Natural Earth 공개 지리 좌표로 구성한 아프리카·남아메리카·인도·오스트레일리아·남극 윤곽. 원본의 색띠나 화석 분포는 포함하지 않으며 서로 다른 축척의 비교 자료다.')

b=line(80,320,510,320,'#4c6d89',width=8)+line(300,120,300,460,'#98a8b5','9 6')+txt(300,96,'법선',23,anchor='middle')+txt(300,492,'거울면',23,anchor='middle')
for ang,col,lab in [(30,'#d57636','30°'),(60,'#a35b85','60°')]:
    a=math.radians(ang);x=300-170*math.sin(a);y=320-170*math.cos(a);b+=arrow(x,y,300,320,col)+txt(x-6,y-14,lab,24,col,anchor='middle')
b+=rect(450,148,65,95,'#fff1d4','#ba8a4b',4)+txt(482,184,'과녁',20,anchor='middle')+txt(300,550,'입사각과 반사각은 법선을 기준으로 잰다.',21,anchor='middle')
save(106,'평면거울 실험의 기준',b,580,'위에서 본 거울·법선·입사 방향','거울의 중앙을 지나는 수직선이 법선이다. 법선에 대한 입사각 30도와 60도를 구분한 배치 개념도. 과녁은 거울 앞쪽 옆에 둔다.')

b=''
for k,flip in enumerate([False,True]):
    cy=270+k*440;b+=txt(28,95+k*440,'공기 → 물' if not flip else '물 → 공기',25,weight='bold')
    d=f'M 120 {cy} A 180 180 0 0 {1 if flip else 0} 480 {cy} Z';b+=path(d,'#5e9cae','#d9edf4')+line(300,cy-150,300,cy+145,'#8296a4','8 6')
    b+=txt(460,cy+(55 if not flip else -50),'물',24)+txt(460,cy+(-70 if not flip else 70),'공기',24)
    for ang in ([30,45] if not flip else [30]):
        a=math.radians(ang);x=300-165*math.sin(a);y=cy-165*math.cos(a)
        b+=arrow(x,y,300,cy,'#c87336' if ang==30 else '#9868a0')+txt(x-20,y-10,str(ang)+'°',23)
    b+=circle(300,cy,5,'#21394a')
b+=txt(30,910,'곧은 면의 중점 = 각도판 중심',23)+txt(30,950,'물에 우유 두세 방울 · 레이저 눈 노출 금지',21)
save(107,'반원형 물통의 두 배치',b,980,'굴절 실험의 경계면과 입사 방향','공기에서 물로 진행할 때와 물에서 공기로 진행할 때의 독립 배치도. 곧은 면의 중점에 빛을 비추며 법선 기준 각도를 사용한다. 굴절 경로는 측정할 대상이므로 표시하지 않았다.')

b=rect(85,245,430,210,'#e4f1f5','#678b9b',8)+txt(300,423,'황산 나트륨 수용액',23,anchor='middle')
for x in [205,395]:
    b+=rect(x-28,120,56,220,'#d8eef2','#52778b',4)+rect(x-32,112,64,15,'#596c79',rx=2)+line(x,310,x,365,'#8e755e',width=5)
b+=line(205,365,205,540)+line(395,365,395,540)+rect(203,515,194,75,'#faf0d6','#a88a55',6)+txt(300,561,'9 V 전지',25,anchor='middle')+txt(221,542,'+',20)+txt(366,542,'−',20)
b+=txt(300,84,'마개가 위 · 용액으로 채운 빨대',23,anchor='middle')+txt(300,480,'침핀끼리 닿지 않도록 분리',22,anchor='middle')+txt(300,636,'기체는 두 빨대에 따로 모인다.',22,anchor='middle')
save(120,'물 분해 기체 수집 장치',b,670,'기체를 분리 수집하는 연결 개념도','수용액 속에 거꾸로 세운 두 빨대 아래의 침핀을 전지의 서로 다른 극에 연결한다. 빨대의 마개는 위에 있고 두 핀은 서로 닿지 않는다. 용기 실제 형태를 재현하지 않은 연결도.')

cards(151,'냉장고의 에너지 표시 비교',[('냉장고 A · 1등급','월간 43.0 kWh / 시간당 CO₂ 25 g / 연간 예상 전기 요금 83,000원'),('냉장고 B · 2등급','월간 46.7 kWh / 시간당 CO₂ 27 g / 연간 예상 전기 요금 90,000원')],footer='비교 활동에 제공된 표시값. 현재 판매 제품이나 현행 요금 안내가 아니다.')

b=rect(150,270,150,65,'#c45d61',rx=0)+rect(300,270,150,65,'#5e82ab',rx=0)+txt(225,314,'N',29,'#fff','middle')+txt(375,314,'S',29,'#fff','middle')
for offset in [60,110,160]:
    b+=path(f'M 150 300 C {150-offset} {300-offset*2}, {450+offset} {300-offset*2}, 450 300')
    b+=path(f'M 150 305 C {150-offset} {305+offset*2}, {450+offset} {305+offset*2}, 450 305')
    b+=arrow(282,300-offset*1.5,320,300-offset*1.5)
b+=txt(300,585,'곡선은 자기장의 방향을 나타내는 개념선',21,anchor='middle')+txt(300,619,'나침반 N극의 실제 방향을 관찰해 비교',21,anchor='middle')
save(152,'막대자석 바깥의 자기장',b,650,'자기장 방향 개념도','자석 바깥에서 N극을 나와 S극으로 향하는 자기장을 독립 곡선으로 나타냈다. 철가루 사진이나 실제 관측 분포가 아니다.')

b=''
for j,label in enumerate(['시작','6개월 뒤','1년 뒤']):
    y=90+j*160;b+=rect(25,y,550,144)+txt(45,y+32,label,24,weight='bold')
    b+=line(125,y+80,540,y+80,'#c2cfd5','5 5')
    for x,l,col in [(210+(100 if j==1 else 0),'A','#cf783e'),(410+(35 if j==1 else 0),'B','#288e9b')]:b+=circle(x,y+80,9,col)+txt(x,y+117,l,23,anchor='middle')
b+=txt(30,615,'가상 위치 모형 · 실제 각도/거리 자료 아님',20)+txt(30,650,'배경을 기준으로 옮겨 보인 정도를 비교한다.',21)
save(158,'관측 시점에 따른 겉보기 위치',b,680,'연주 시차를 비교하는 가상 위치 모형','동일한 배경에서 시작·6개월 뒤·1년 뒤의 위치를 보이는 독립 모형. A의 위치 차이가 B보다 크고 1년 뒤에는 처음 위치로 돌아온다. 이동량은 측정값이 아니다.')
cards(161,'별의 색과 온도 조사',[('프로키온','관찰 자료에서 색을 확인하고 표면 온도를 조사한다.'),('베텔게우스','관찰 자료에서 색을 확인하고 표면 온도를 조사한다.'),('시리우스','관찰 자료에서 색을 확인하고 표면 온도를 조사한다.')],caption='세 별의 비교 기록 안내',footer='별 사진을 대체한 조사 기록 틀. 확인한 색·온도와 자료 출처를 함께 적는다.')

b=rect(170,145,260,290,'#eef4f5','#63808c',45)+rect(242,100,116,54,'#8bb5c1',rx=8)+txt(300,81,'앞: 병뚜껑',23,anchor='middle')
b+=line(140,175,140,530,'#aa815b',width=12)+line(460,175,460,530,'#aa815b',width=12)+line(140,490,460,490,'#c69936',width=5)+rect(252,462,96,58,'#a9cdd9','#477b8d',4)
b+=txt(300,571,'뒤: 고무줄과 노',24,anchor='middle')+txt(300,617,'노를 돌려 고무줄을 감고 놓는다.',21,anchor='middle')+txt(300,651,'놓였을 때 노가 물을 뒤로 밀도록 감는다.',21,anchor='middle')
save(211,'고무줄 배의 부품 배치',b,680,'위에서 본 고무줄 배의 독립 설계도','병 양옆의 긴 막대가 뒤로 뻗고 그 사이 고무줄에 두 플라스틱 조각의 노를 끼운다. 풀릴 때 노가 물을 뒤로 밀도록 감는다. 원본 사진의 화살표에 의존하지 않는 설명이다.')

cards(241,'가열·냉각에서 비교할 온도',[('물','가열 중 녹는 구간: 0 ℃ / 냉각 중 어는 구간: 0 ℃'),('아세트산','가열 중 녹는 구간: 16.6 ℃ / 냉각 중 어는 구간: 16.6 ℃')],caption='두 물질의 상태 변화 온도 비교 자료',footer='원자료의 상태 변화 온도를 정리한 독립 표. 시간에 따른 실측 곡선을 복제한 그림이 아니다.')
cards(244,'물질별 밀도와 상태 변화 온도',[
 ('구리','밀도 8.96 g/cm³ / 녹는점 1084.6 ℃ / 끓는점 2562 ℃'),('올리브기름','밀도 0.91~0.93 g/cm³ / 녹는점 −6~−2 ℃ / 끓는점 약 300 ℃'),('청동','밀도 8.4~8.9 g/cm³ / 녹는점 850~1000 ℃ / 끓는점 2300~2400 ℃'),('아세톤','밀도 0.78 g/cm³ / 녹는점 −94.7 ℃ / 끓는점 56.5 ℃'),('공기','밀도 0.00120~0.00129 g/cm³ / 녹는점 −220~−210 ℃ / 끓는점 −196~−183 ℃'),('산소','밀도 0.0013 g/cm³ / 녹는점 −218.8 ℃ / 끓는점 −183 ℃')],caption='여섯 물질의 특성값을 정리한 비교 카드',footer='제공된 수치의 단위와 범위를 유지하여 새로 구성한 자료')
cards(249,'두 천체의 표면 환경',[('지구에서 보이는 요소','구름, 산, 호수, 풀밭'),('달에서 보이는 요소','어두운 하늘, 식생이 없는 지표')],caption='지구·달 표면의 관찰 특징 비교',footer='원자료에서 읽을 수 있는 요소를 정리한 개념 자료. 실제 촬영 영상이 아니다.')

b=rect(25,90,550,300,'#e5f2f8')
for f in geo['features']:
 for p in polys([f]):
    segments=[];previous=None
    for x,y,*_ in p:
        px=25+(x+180)/360*550;py=90+(90-y)/180*300
        if previous is not None and abs(x-previous)>180:segments.append('M')
        elif not segments:segments.append('M')
        else:segments.append('L')
        segments.append(f'{px:.1f},{py:.1f}');previous=x
    b+=path(' '.join(segments)+' Z','none','#88af9a',0)
b+=txt(300,435,'현재 위치 → 조각 이동 → 배열 비교',24,anchor='middle')+txt(30,480,'자연 해안선 자료: Natural Earth (public domain)',18)
save(257,'대륙 위치를 비교하는 세계 지도',b,510,'공개 지리 데이터로 만든 대륙 분포도','Natural Earth의 공개 지리 좌표로 새로 그린 현재 대륙 분포. 이 도식은 과거 해안선이나 특정 판게아 재구성을 제공하지 않는다.')

elements=['Ne','B','Ca','H','Al','O','Ar','Li','Si','C','He','P','Mg','N','Cl','Be','K','F','Na','S'];b=''
for j,name in enumerate(elements):
 x=30+j%4*137;y=100+j//4*86;b+=rect(x,y,125,74,'#edf5f4','#95b4bb',7)+txt(x+62,y+48,name,30,anchor='middle')
b+=line(45,585,550,585,'#c28941',width=4)+txt(300,624,'아래 선 뒤에서 바둑알을 튕긴다.',23,anchor='middle')+txt(300,665,'독립 배열의 1~20번 원소 이름 연습판',20,anchor='middle')
save(273,'원소 이름 연습판',b,695,'새 배열로 만든 원소 기호 놀이판','원자번호 1부터 20까지의 원소 기호를 독립적으로 배치한 4열 5행 놀이판. 아래쪽의 출발선에서 바둑알을 튕겨 멈춘 칸의 원소 이름을 말한다.')

b=''
for j,(label,col) in enumerate([('처리 전','#84ad65'),('처리 후','#343e5e')]):
 y=110+j*230;b+=txt(38,y-17,label,25,weight='bold')+rect(160,y,285,140,'#eff7ed','#7da46f',10)
 for x,z in [(180,25),(215,112),(260,20),(305,112),(360,24),(420,100)]:b+=f'<ellipse cx="{x}" cy="{y+z}" rx="14" ry="9" fill="{col}"/>'
b+=txt(300,615,'색이 달라진 위치를 비교하는 모형',23,anchor='middle')+txt(300,653,'현미경 사진이 아니며 크기·개수는 비축척',20,anchor='middle')
save(282,'검정말잎의 색 변화 위치',b,685,'녹말 반응 전후의 위치 비교 모형','아이오딘-아이오딘화 칼륨 용액 처리 뒤 엽록체 부근에 나타난 짙은 색을 개념적으로 표현했다. 실제 현미경 사진을 모사하거나 새 측정 결과로 제시하지 않았다.')
cards(314,'오리온자리 세 별의 비교',[('베텔게우스','색과 표면 온도를 확인한 자료를 찾아 기록한다.'),('민타카','색과 표면 온도를 확인한 자료를 찾아 기록한다.'),('리겔','색과 표면 온도를 확인한 자료를 찾아 기록한다.')],caption='색·온도를 비교할 세 별의 조사 틀',footer='천체 관측 자료나 천문 자료에서 값을 조사하여 빈 기록을 채우는 안내')

heights=[0,4,8,10,15,20,25,30,35,40,45,50,60,70,80,84.9,100.4,110]
temps=[15,-11,-37,-50,-56.5,-56.5,-51.5,-46.5,-36.1,-22.1,-8.1,-2.5,-27.7,-55.7,-76.5,-86.3,-73.6,-9.2]
b=txt(100,94,'높이 (km)',24)+txt(350,94,'기온 (℃)',24)
for j,(z,t) in enumerate(zip(heights,temps)):
 y=115+j*49;b+=rect(40,y,520,44,'#edf4f6' if j%2==0 else '#f8fafb',rx=4)+txt(150,y+31,z,24,anchor='middle')+txt(423,y+31,t,24,anchor='middle')
b+=txt(28,1045,'제공된 수치만 옮긴 독립 세로형 표',20)
save(334,'대기권의 높이별 기온',b,1080,'높이·기온 쌍을 재배열한 자료표','0에서 110 km까지 18개 높이와 기온 자료를 한 줄에 한 쌍씩 배치한 새 표. 값은 제공 자료와 동일하며 새 관측값을 만들지 않았다.')

b=arrow(90,400,550,400)+arrow(90,400,90,100)+txt(320,448,'시간 경과',23,anchor='middle')+txt(45,250,'온도',22)+path('M 96 365 C 170 230, 240 177, 345 165 C 415 162, 480 162, 540 162','#cb753e',width=5)
b+=txt(300,510,'처음 상승 → 변화가 작아지는 구간',22,anchor='middle')+txt(300,550,'적외선등: 태양 / 검은 컵: 지구',22,anchor='middle')+txt(300,590,'정성적 변화 모형 · 실측 시간·온도 없음',20,anchor='middle')
save(335,'복사 평형을 생각하는 변화 모형',b,620,'컵 온도의 정성적 변화 모형','처음 상승하다가 일정한 수준에 가까워지는 온도 경향을 새 곡선으로 표현했다. 원본 관측점·눈금·실측 곡선의 재현이 아니다.')
cards(339,'기온·습도·이슬점의 변화',[('비교 조건','맑은 날이며 하루 동안 공기의 수증기량은 거의 유지되는 경우'),('기온이 높아지는 때','상대습도는 낮아지는 경향'),('기온이 낮아지는 때','상대습도는 높아지는 경향'),('이슬점','하루 중 변화가 비교적 작음')],caption='하루 동안의 변화 경향을 정리한 개념표',footer='실측 시각·값이 없는 정성 자료. 제시된 세 경향의 관계와 이유를 설명한다.')
cards(347,'계절별 기압 배치 읽기',[('봄 자료의 특징','우리나라 남쪽 바다에 전선을 동반한 저기압. 그 서쪽과 동쪽에 고기압.'),('여름 자료의 특징','우리나라 남동쪽 해상에 고기압. 북쪽과 서쪽에는 저기압. 등압선은 겨울보다 넓은 간격.'),('가을 자료의 특징','한반도 부근에 고기압. 그 서쪽과 북동쪽에 저기압.'),('겨울 자료의 특징','북서쪽 대륙에 강한 고기압, 동쪽 일본 부근에 저기압. 우리나라 주변 등압선 간격이 좁음.')],caption='기압 배치의 위치 관계를 새로 정리한 자료',footer='지도·등압선 도형을 복제하지 않은 관계표. 풍향·바람 세기·구름·강수를 추론한다.')
cards(355,'해역별 염분의 상대적 차이',[('위도대 비교','태평양·대서양의 적도 해역 0°~20°보다 중위도 해역 20°~30°의 표층 염분이 높다.'),('태평양 안에서의 비교','같은 위도에서 담수가 들어오는 연안은 중앙 해역보다 표층 염분이 낮다.')],caption='해역 사이의 염분 비교 관계',footer='관측 분포에서 확인한 정성 관계를 새 표로 구성했다. 색 지도나 새 염분 측정값은 제공하지 않는다.')
cards(358,'북태평양 순환의 단서',[('북반구 저위도 바람','북동 무역풍: 동쪽에서 서쪽으로 치우쳐 분다.'),('북반구 중위도 바람','편서풍: 서쪽에서 동쪽으로 치우쳐 분다.'),('연안의 상대적 수온','서쪽 연안은 같은 위도의 동쪽 연안보다 따뜻한 경향이 나타난다.'),('그릴 내용','바람에 따른 동서 흐름과 연안의 남북 흐름을 연결한다.')],caption='바람과 수온을 이용한 해류 추론 자료',footer='실측 8월 수온 지도를 모사하지 않은 정성 관계표')
cards(359,'북적도 해류가 강한 경우',[('열 수송 방향','적도 부근에서 동쪽의 따뜻한 물을 서쪽으로 운반'),('동태평양','평상시보다 낮은 수온'),('주변 지역 사례','호주: 집중호우·홍수 / 북아메리카: 한파 / 북태평양 적도 해역: 강한 태풍 / 아르헨티나: 가뭄·화재')],caption='해류 강화 시 보고된 지역별 현상',footer='원자료의 현상만 독립 항목으로 정리. 모든 사례를 항상 일어나는 결과로 일반화하지 않는다.')
# second comparison card uses different independent row order and data structure.
def second_card(i):
 items=[('동태평양','평상시보다 높은 수온, 주변 지역의 집중호우'),('서태평양 주변','인도네시아 산불, 호주 가뭄'),('미국','12월 벚꽃 개화 사례')];y=80;b=''
 for h,t in items:
    a,hh=para(42,y+70,t,29);b+=rect(25,y,550,hh+90)+txt(42,y+34,h,25,weight='bold')+a;y+=hh+110
 b+=txt(28,y+15,'지역별 사례이며 항상 발생하는 법칙은 아니다.',20)
 save(i,'북적도 해류가 약한 경우',b,y+50,'해류 약화 시 보고된 지역별 현상','동태평양 수온 상승과 주변 강수, 인도네시아 산불·호주 가뭄·미국 12월 개화 사례를 지리 지도 없이 새 카드로 정리했다.',n=2)
second_card(359)

b=txt(120,130,'응시점',24,anchor='middle')+txt(450,130,'관찰 표지',24,anchor='middle')
b+=line(100,260,140,260,'#2e586d',width=7)+line(120,240,120,280,'#2e586d',width=7)+circle(450,260,20,'#bc743c')
b+=txt(300,370,'왼쪽 눈을 가리고 오른쪽 눈으로 +를 본다.',21,anchor='middle')+txt(300,415,'시선을 고정한 채 그림과의 거리를 바꾼다.',21,anchor='middle')+txt(300,462,'오른쪽 원이 계속 보이는지 관찰한다.',22,anchor='middle')
save(374,'맹점을 찾는 두 표지',b,500,'기하 도형으로 새로 만든 맹점 관찰표','왼쪽에는 십자 응시점, 오른쪽에는 원형 관찰 표지를 두었다. 왼쪽 눈을 가리고 오른쪽 눈으로 십자를 보면서 거리를 바꾼다.')

cards(379,'중추신경계 구조 조사 틀',[('뇌의 부분','대뇌 · 사이뇌 · 중간뇌 · 소뇌 · 숨골'),('뇌와 연결되는 부분','척수'),('조사하여 표시할 내용','각 부분의 위치, 이웃한 구조, 맡은 기능'),('모둠의 결과물','해부 구조 자료를 확인하며 각자 독립적으로 그린 부분을 합친다.')],caption='중추신경계 공동 모형 제작 안내',footer='해부 단면 그림을 대체한 구성 안내. 위치는 조사 자료에서 확인하며 임의로 정하지 않는다.')

b='';labs=[('감각기관',90),('감각뉴런',175),('척수 또는 뇌',260),('운동뉴런',345),('운동기관',430)]
for j,(l,y) in enumerate(labs):
 b+=rect(165,y,270,58)+txt(300,y+39,l,25,anchor='middle')
 if j<len(labs)-1:b+=arrow(300,y+59,300,y+84)
b+=txt(300,545,'무조건반사와 의식적 반응의 예를 골라',22,anchor='middle')+txt(300,582,'중추의 위치와 연결 경로를 따로 완성한다.',22,anchor='middle')
save(382,'자극에서 반응까지의 연결 틀',b,620,'신경 신호 경로를 비교하는 독립 흐름도','감각기관에서 감각뉴런, 중추, 운동뉴런, 운동기관으로 이어지는 기본 틀. 특정 반사의 중추와 의식적 반응의 경로는 사례에 맞게 학습자가 완성한다.')

cards(398,'가상 가족의 혈액형 조건',[('첫 세대 · 아버지 쪽','할아버지 O형, 할머니 A형 → 아버지 A형'),('첫 세대 · 어머니 쪽','외할아버지 O형, 외할머니 B형 → 어머니 B형'),('둘째·셋째 세대','아버지 A형과 어머니 B형 사이에 O형 아들과 B형 딸이 있다.'),('추론할 대상','이 가족의 다음 자녀, 그리고 B형 딸과 AB형 배우자 사이의 자녀')],caption='독립적으로 구성한 가상 가족의 조건표',footer='새 교육용 가상 사례. 실제 가족·교과서 가족이 아니다. A·B·O의 대립유전자 관계를 적용한다.')

(INPUT/'manifest.json').write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print('activities',len(manifest),'figures',sum(map(len,manifest.values())))
