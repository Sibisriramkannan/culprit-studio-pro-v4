from pathlib import Path
import json
from app.config import settings

SCOPES=[
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly',
]

def oauth_flow():
    from google_auth_oauthlib.flow import Flow
    p=Path(settings.YOUTUBE_CLIENT_SECRETS_FILE)
    if not p.exists(): raise RuntimeError(f'YouTube OAuth client file not found: {p}')
    return Flow.from_client_secrets_file(str(p),scopes=SCOPES,redirect_uri=settings.YOUTUBE_REDIRECT_URI)

def auth_url():
    flow=oauth_flow(); return flow.authorization_url(access_type='offline',include_granted_scopes='true',prompt='consent')

def _save(c):
    Path(settings.YOUTUBE_TOKEN_FILE).write_text(json.dumps({'token':c.token,'refresh_token':c.refresh_token,'token_uri':c.token_uri,'client_id':c.client_id,'client_secret':c.client_secret,'scopes':list(c.scopes or SCOPES)},ensure_ascii=False,indent=2),encoding='utf-8')

def exchange(code):
    flow=oauth_flow(); flow.fetch_token(code=code); _save(flow.credentials); return {'connected':True}

def credentials():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    p=Path(settings.YOUTUBE_TOKEN_FILE)
    if not p.exists(): return None
    c=Credentials.from_authorized_user_info(json.loads(p.read_text(encoding='utf-8')),SCOPES)
    if c.expired and c.refresh_token:
        c.refresh(Request()); _save(c); print('[YouTube] Access token refreshed.')
    return c if c.valid else None

def _youtube():
    from googleapiclient.discovery import build
    c=credentials()
    if not c: raise RuntimeError('YouTube is not connected')
    return build('youtube','v3',credentials=c,cache_discovery=False)

def channel_info():
    yt=_youtube(); r=yt.channels().list(part='snippet,statistics',mine=True).execute()
    if not r.get('items'): return None
    x=r['items'][0]; return {'id':x['id'],'title':x['snippet']['title'],'statistics':x.get('statistics',{})}

def upload(video_path,title,description,privacy='private'):
    from googleapiclient.http import MediaFileUpload
    p=Path(video_path)
    if not p.exists(): raise RuntimeError(f'Video file not found: {p}')
    yt=_youtube(); privacy=privacy if privacy in ('private','unlisted','public') else 'private'
    req=yt.videos().insert(part='snippet,status',body={'snippet':{'title':str(title)[:100],'description':str(description)[:5000]},'status':{'privacyStatus':privacy}},media_body=MediaFileUpload(str(p),mimetype='video/mp4',resumable=True))
    res=None
    print('[YouTube] Uploading:',title)
    while res is None:
        progress,res=req.next_chunk()
        if progress: print('[YouTube] Upload:',int(progress.progress()*100),'%')
    print('[YouTube] Upload completed:',res.get('id')); return res
