"""Source-specific candidate extraction; final records require recorded image review."""
import json, pathlib, hashlib, re
import fitz
from PIL import Image, ImageDraw, ImageFont

BASE=pathlib.Path(__file__).parent
RAW=pathlib.Path('C:/Users/USER/Desktop/maintain/textbook_wiki/raw')
FILES=['22개정 고등 통합과학1 연구용 교과서(웹용).pdf','통합과학2_연구용_압축.pdf']

def lines(page):
    return [l for b in page['blocks'] for l in b['lines']]
def txt(line):return ''.join(s['text'] for s in line['spans'])
def bbox(items):
    return [min(i['bbox'][0] for i in items),min(i['bbox'][1] for i in items),max(i['bbox'][2] for i in items),max(i['bbox'][3] for i in items)]
def candidates(v):
    ps=json.loads((BASE/f'IS{v}/scratch/pages.json').read_text(encoding='utf8'))
    found=[]
    for p in ps:
        n=p['pdf_page']
        if not 16<=n<=(163 if v==1 else 159):continue
        ls=lines(p)
        titles=[l for l in ls if any(s['font']=='10X10Bold' or (s['font']=='SDGothicNeoRound-gBd' and s['size']<15) or s['font']=='YanoljaYacheOTFR' for s in l['spans'])]
        if not titles:continue
        titles.sort(key=lambda l:(l['bbox'][1],l['bbox'][0]))
        font=titles[0]['spans'][0]['font'];size=titles[0]['spans'][0]['size']
        typ='해 보기' if font=='10X10Bold' and size<10 else '탐구 활동' if font=='10X10Bold' else '창의융합' if font=='SDGothicNeoRound-gBd' else '토의·토론과 논술'
        title='\n'.join(txt(l).strip() for l in titles)
        labels=[l for l in ls if txt(l).strip()=='준비물' and l['spans'][0]['size']<7]
        supplies=[]
        sb=None
        for label in labels:
            x,y,x1,y1=label['bbox']
            right=418 if x>340 or 150<x<160 else 280 if 195<x<205 else 555 if x>290 else 145
            choices=[l for l in ls if l['bbox'][0]>=x-1 and l['bbox'][2]<=right+1 and y1+2<l['bbox'][1]<y1+110 and any(6.5<s['size']<6.9 and ('YDVYGO' in s['font']) for s in l['spans']) and all(s['size']<7 for s in l['spans'])]
            choices.sort(key=lambda l:(round(l['bbox'][1]/3),l['bbox'][0]))
            chosen=[];end=y1
            for l in choices:
                if l['bbox'][1]-end>17:break
                chosen.append(l);end=max(end,l['bbox'][3])
            supplies.extend(chosen)
            if chosen:sb=bbox([label]+chosen)
        sup='\n'.join(txt(l).strip() for l in supplies) or None
        found.append({'pdf_page':n,'type':typ,'title':title,'title_bbox':bbox(titles),'supplies':sup,'supplies_bbox':sb,'label_count':len(labels)})
    return ps,found

def panels(v,found):
    d=fitz.open(RAW/FILES[v-1]);out=BASE/f'IS{v}/scratch'
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
    pieces=[]
    for c in found:
        n=c['pdf_page'];p=d[n-1]
        title=fitz.Rect(c['title_bbox'])+(-50,-15,10,12)
        title=title & p.rect
        boxes=[title]
        if c['supplies_bbox']:boxes.append((fitz.Rect(c['supplies_bbox'])+(-5,-5,8,8))&p.rect)
        ims=[]
        for b in boxes:
            pm=p.get_pixmap(matrix=fitz.Matrix(2.5,2.5),clip=b)
            im=Image.frombytes('RGB',[pm.width,pm.height],pm.samples)
            if im.width>1000:im.resize((1000,round(im.height*1000/im.width)))
            ims.append(im)
        h=max(100,sum(im.height for im in ims)+38)
        piece=Image.new('RGB',(1100,h),'white');dr=ImageDraw.Draw(piece);dr.text((4,3),f'IS{v} PDF {n} / {c["type"]}',font=font,fill='black')
        yy=32
        for im in ims:piece.paste(im,(8,yy));yy+=im.height
        pieces.append(piece)
    for start in range(0,len(pieces),6):
        batch=pieces[start:start+6];sheet=Image.new('RGB',(1100,sum(i.height+8 for i in batch)), '#bbbbbb');yy=0
        for im in batch:sheet.paste(im,(0,yy));yy+=im.height+8
        sheet.save(out/f'review_{start//6+1:02}.png')

if __name__=='__main__':
    for v in [1,2]:
        ps,cs=candidates(v)
        (BASE/f'IS{v}/scratch/candidates.json').write_text(json.dumps(cs,ensure_ascii=False,indent=2),encoding='utf8')
        panels(v,cs)
        for c in cs:print(v,c['pdf_page'],c['type'],c['title'].replace('\n',' '),'SUPPLIES',repr(c['supplies']))
