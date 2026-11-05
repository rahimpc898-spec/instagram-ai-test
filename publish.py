import json, os, time
from pathlib import Path
import requests

j=json.loads(Path('post.json').read_text())
site=os.environ['PAGES_BASE_URL'].rstrip('/')
image_url=site+'/'+j['filename']
api_version=os.getenv('META_API_VERSION','v24.0')
base=f'https://graph.facebook.com/{api_version}'
acct=os.environ['INSTAGRAM_USER_ID']
token=os.environ['INSTAGRAM_ACCESS_TOKEN']
s=requests.Session()

# Confirm that the JPEG has become publicly reachable on GitHub Pages.
for attempt in range(36):
 try:
  r=s.get(image_url, timeout=15)
  if r.status_code==200 and r.headers.get('content-type','').startswith('image/') and len(r.content)>10000:
   print('Public JPEG is ready.'); break
 except requests.RequestException: pass
 time.sleep(10)
else: raise RuntimeError('Image not publicly available yet; no post was published. Check Pages deployment URL.')

# Create media container via Instagram Login API.
r=s.post(f'{base}/{acct}/media',data={'image_url':image_url,'caption':j['caption'],'access_token':token},timeout=40)
if not r.ok: raise RuntimeError(f'Instagram media creation failed ({r.status_code}): {r.text}')
container=r.json()['id']
# Containers may need time to process.
for i in range(15):
 status=s.get(f'{base}/{container}',params={'fields':'status_code','access_token':token},timeout=30)
 status.raise_for_status(); state=status.json().get('status_code')
 if state=='FINISHED': break
 if state in ('ERROR','EXPIRED'): raise RuntimeError(f'Instagram container state: {state}')
 time.sleep(5)
else: raise RuntimeError('Instagram container not ready; no publish attempted')
r=s.post(f'{base}/{acct}/media_publish',data={'creation_id':container,'access_token':token},timeout=45)
if not r.ok: raise RuntimeError(f'Instagram publishing failed ({r.status_code}): {r.text}')
print('Published Instagram media ID:',r.json().get('id'))
