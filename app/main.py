from fastapi import FastAPI,HTTPException,UploadFile,File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse,RedirectResponse,Response
from pathlib import Path
from datetime import datetime
import json,shutil
from app.config import settings
from app.models import StoryRequest,GenerateRequest,ScheduleRequest,ScheduleUpdateRequest
from app.providers.llm import build_story
from app.providers.tts import synth
from app.providers.youtube import auth_url,exchange,channel_info
from app.pipeline import run
from app.db import init_db,conn,list_jobs,stats
from app.scheduler import start as scheduler_start,reload_schedules,execute_schedule

app=FastAPI(title='Culprit Studio Pro',version='4.0')
CAT=json.loads(Path('app/data/catalog.json').read_text(encoding='utf-8'))

def has(n): return bool(getattr(settings,n,None))
def state(key,implemented=True,reason=None):
    if not key:return {'configured':False,'enabled':False,'status':'NOT_CONFIGURED','reason':reason or 'API key missing'}
    if not implemented:return {'configured':True,'enabled':False,'status':'NOT_IMPLEMENTED','reason':reason or 'Adapter not implemented'}
    return {'configured':True,'enabled':True,'status':'READY','reason':reason}

@app.on_event('startup')
def startup():
    init_db(); scheduler_start(); print('[Culprit] V4 scheduler ready')

@app.get('/api/health')
def health():return {'ok':True,'name':'Culprit Studio Pro','version':'4.0'}
@app.get('/api/catalog')
def catalog():return CAT

@app.get('/api/providers/status')
def providers_status():
    llm={k:state(has(v), k not in ('cohere','cloudflare')) for k,v in {'gemini':'GEMINI_API_KEY','groq':'GROQ_API_KEY','mistral':'MISTRAL_API_KEY','together':'TOGETHER_API_KEY','openai':'OPENAI_API_KEY','cohere':'COHERE_API_KEY','cloudflare':'CLOUDFLARE_API_KEY'}.items()}
    image={'huggingface':state(has('HUGGINGFACE_API_KEY')),'openai':state(has('OPENAI_API_KEY')),'deepai':state(has('DEEPAI_API_KEY'),False),'segmind':state(has('SEGMIND_API_KEY'),False),'stability':state(has('STABILITY_API_KEY'),False)}
    voice={'edge':state(True),'elevenlabs':state(has('ELEVENLABS_API_KEY')),'deepgram':state(has('DEEPGRAM_API_KEY')),'cartesia':state(has('CARTESIA_API_KEY'),False)}
    video={
      'auto':state(True,True,'Automatic AI failover router'),
      'nvidia':state(has('NVIDIA_API_KEY'),True,'NVIDIA Cosmos3 Nano hosted Preview API'),
      'none':state(True,True,'Local FFmpeg safety fallback'),
      'pixverse':state(has('PIXVERSE_API_KEY'),True,'PixVerse V6 image-to-video'),
      'minimax':state(has('MINIMAX_API_KEY'),True,'MiniMax/Hailuo image-to-video'),
      'fal-wan22':state(has('FAL_API_KEY'),True),
      'replicate':state(has('REPLICATE_API_KEY'),True),
      'novita':state(has('NOVITA_API_KEY'),True),
      'modelslab':state(has('MODELSLAB_API_KEY'),True),
      'kling-direct':state(bool(settings.KLING_ACCESS_KEY and settings.KLING_SECRET_KEY),False,'Legacy single KLING_API_KEY is retained, but current direct adapter requires verified access/secret auth before enabling.'),
      'json2video':state(has('JSON2VIDEO_API_KEY'),False,'Cloud rendering/composition provider; not used as generative-motion AI in V3 router.')
    }
    hf=bool(settings.HF_TOKEN and settings.HF_REPO_ID); storage={'download':state(True),'huggingface':state(hf)}
    yt={'configured':Path(settings.YOUTUBE_CLIENT_SECRETS_FILE).exists(),'connected':False,'enabled':False,'status':'AUTH_REQUIRED'}
    try:
        ch=channel_info(); yt.update({'connected':bool(ch),'enabled':bool(ch),'status':'READY' if ch else 'AUTH_REQUIRED','channel':ch})
    except Exception as e:yt['reason']=str(e)
    return {'llm':llm,'image':image,'voice':voice,'video':video,'storage':storage,'youtube':yt}

@app.get('/api/dashboard')
def dashboard():
    try:yt=channel_info()
    except:yt=None
    return {'jobs':stats(),'youtube':yt,'recent_jobs':list_jobs(10)}

@app.post('/api/story')
def story(req:StoryRequest):
    try:return build_story(req.user_input,provider=req.llm_provider,mode=req.mode,language=req.language)
    except Exception as e:raise HTTPException(500,str(e))

@app.get('/api/voice-preview/{voice}')
def voice_preview(voice:str,language:str='en'):
    allowed={x['id'] for x in CAT['voices']}
    if voice not in allowed:raise HTTPException(404,'Unknown voice')
    p=Path(settings.DATA_DIR)/f'voice-{language}-{voice}.mp3'
    if not p.exists():synth('Welcome to Culprit Studio Pro. This is a voice preview.',str(p),'edge',voice,language)
    return Response(p.read_bytes(),media_type='audio/mpeg')

@app.post('/api/upload/music')
async def upload_music(file:UploadFile=File(...)):
    safe=Path(file.filename or 'music.mp3').name; dest=Path(settings.UPLOAD_DIR)/safe
    with dest.open('wb') as f:shutil.copyfileobj(file.file,f)
    return {'path':str(dest),'name':safe}

@app.post('/api/generate')
def generate(req:GenerateRequest):
    try:return run(req.config.model_dump())
    except Exception as e:raise HTTPException(500,str(e))
@app.get('/api/jobs')
def jobs():return list_jobs(100)
@app.get('/api/schedules')
def schedules():
    c=conn(); rows=[dict(x) for x in c.execute('SELECT * FROM schedules ORDER BY id DESC').fetchall()]; c.close()
    for r in rows:r['config']=json.loads(r.pop('config_json'))
    return rows
@app.post('/api/schedules')
def create_schedule(req:ScheduleRequest):
    c=conn(); cur=c.execute('INSERT INTO schedules(name,enabled,preset,local_time,second_local_time,weekday,custom_cron,config_json,created_at,last_status) VALUES(?,?,?,?,?,?,?,?,?,?)',(req.name,int(req.enabled),req.preset,req.local_time,req.second_local_time,req.weekday,req.custom_cron,json.dumps(req.config.model_dump(),ensure_ascii=False),datetime.now().isoformat(),'never')); sid=cur.lastrowid;c.commit();c.close();reload_schedules();return {'id':sid,'ok':True}
@app.post('/api/schedules/{sid}/run')
def run_schedule(sid:int):execute_schedule(sid);return {'ok':True}
@app.patch('/api/schedules/{sid}')
def update_schedule(sid:int,req:ScheduleUpdateRequest):
    vals=req.model_dump(exclude_none=True)
    if not vals:return {'ok':True}
    if 'enabled' in vals:vals['enabled']=int(vals['enabled'])
    c=conn();cols=', '.join(f'{k}=?' for k in vals);c.execute(f'UPDATE schedules SET {cols} WHERE id=?',(*vals.values(),sid));c.commit();c.close();reload_schedules();return {'ok':True}
@app.delete('/api/schedules/{sid}')
def delete_schedule(sid:int):
    c=conn();c.execute('DELETE FROM schedules WHERE id=?',(sid,));c.commit();c.close();reload_schedules();return {'ok':True}
@app.get('/auth/youtube/start')
def youtube_start():url,_=auth_url();return RedirectResponse(url)
@app.get('/auth/youtube/callback')
def youtube_callback(code:str):exchange(code);return RedirectResponse('/?youtube=connected')
@app.get('/api/youtube/status')
def youtube_status():
    try:return {'connected':bool(channel_info()),'channel':channel_info()}
    except Exception as e:return {'connected':False,'error':str(e)}
app.mount('/static',StaticFiles(directory='app/static'),name='static')
@app.get('/')
def home():return FileResponse('app/static/index.html')
