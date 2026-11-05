import os, json, random, re, textwrap
from datetime import datetime, timezone
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageFont

OUT=Path('site'); OUT.mkdir(exist_ok=True)
KEY=os.environ['GEMINI_API_KEY']
model=os.getenv('GEMINI_MODEL','gemini-2.5-flash-lite')
now=datetime.now(timezone.utc)
seed=now.strftime('%Y-%m-%d %H:%M UTC')
prompt=f'''You write short original Instagram meme text for @wistfulforever.
Return ONLY JSON object with keys "quote" and "caption".
The quote must be ONE punchy, funny, flirty, wholesome, relatable or mildly chaotic English line, 3-13 words, no explicit sexual language, no hate, no copied lyrics, no hashtags in quote.
Caption: short, playful, at most 120 characters, may include 1-3 relevant hashtags.
Avoid repeated cliches. Vary tone each time. Use lowercase casual internet tone.
Current scheduled slot: {seed}. Variation seed: {random.randrange(1_000_000)}.'''
r=requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
  headers={'x-goog-api-key':KEY,'Content-Type':'application/json'},
  json={'contents':[{'parts':[{'text':prompt}]}], 'generationConfig':{'responseMimeType':'application/json','temperature':1.05}},timeout=60)
r.raise_for_status()
raw=r.json()['candidates'][0]['content']['parts'][0]['text']
data=json.loads(raw)
quote=str(data['quote']).strip().strip('"')
caption=str(data['caption']).strip()
if not (3 <= len(quote.split()) <= 19) or len(quote)>140:
    raise ValueError('Unusable AI quote; no post created')

W=H=1080
palettes=[((244,135,186),(128,87,226)),((113,137,251),(226,119,190)),((249,155,166),(150,115,244)),((135,178,247),(196,114,237))]
a,b=random.choice(palettes)
im=Image.new('RGB',(W,H)); pix=im.load()
for y in range(H):
 for x in range(W):
  t=min(1,max(0,(0.6*x/W+0.4*y/H)))
  pix[x,y]=tuple(int(a[i]*(1-t)+b[i]*t) for i in range(3))
d=ImageDraw.Draw(im)
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
if not Path(fontpath).exists(): raise FileNotFoundError('Expected Linux font missing')
for size in range(92,43,-3):
 font=ImageFont.truetype(fontpath,size)
 lines=[]; line=''
 for word in quote.split():
  test=(line+' '+word).strip()
  if d.textbbox((0,0),test,font=font,stroke_width=0)[2] <= 910: line=test
  else:
   if line: lines.append(line)
   line=word
 if line: lines.append(line)
 gap=int(size*1.22)
 if len(lines)*gap<=660 and len(lines)<=7:break
start=H/2-(len(lines)-1)*gap/2
for i,line in enumerate(lines):
 bbox=d.textbbox((0,0),line,font=font)
 width=bbox[2]-bbox[0]
 d.text((W/2-width/2,start+i*gap),line,font=font,fill='white',stroke_width=1,stroke_fill=(240,235,255))
name='post-'+now.strftime('%Y%m%d-%H%M%S')+'.jpg'
im.save(OUT/name,'JPEG',quality=93,subsampling=0)
(OUT/'index.html').write_text('<!doctype html><title>wistfulforever posts</title><h1>@wistfulforever</h1>')
(OUT/'.nojekyll').write_text('')
Path('post.json').write_text(json.dumps({'filename':name,'quote':quote,'caption':caption},ensure_ascii=False))
print('Prepared image:',name, 'Quote:',quote)
