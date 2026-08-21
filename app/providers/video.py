from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import base64, mimetypes, time, uuid, random, requests
from app.config import settings

class VideoProviderError(RuntimeError): pass
class PermanentProviderError(VideoProviderError): pass
class TemporaryProviderError(VideoProviderError): pass

@dataclass
class VideoRouterState:
    disabled_providers:set[str]=field(default_factory=set)
    failures:dict[str,str]=field(default_factory=dict)
    successful_provider:Optional[str]=None

PERM_WORDS=('balance','credit','billing','subscribe','subscription','locked','invalid api','invalid key','unauthorized','not enough','quota exceeded','plan required','exhausted')
DEFAULT_ORDER=['nvidia','pixverse','minimax','fal','replicate','novita','modelslab']
ALIASES={'auto':'auto','nvidia':'nvidia','nvidia-cosmos':'nvidia','cosmos3-nano':'nvidia','pixverse':'pixverse','minimax':'minimax','hailuo':'minimax','fal-wan22':'fal','fal':'fal','replicate':'replicate','novita':'novita','modelslab':'modelslab','kling-direct':'kling','kling':'kling','json2video':'json2video','none':'none'}

def _key(name):
    v=getattr(settings,name,None); return str(v).strip() if v else ''

def _data_uri(path):
    p=Path(path); mime=mimetypes.guess_type(str(p))[0] or 'image/png'
    return f'data:{mime};base64,'+base64.b64encode(p.read_bytes()).decode('ascii')

def _download(url,out):
    p=Path(out); p.parent.mkdir(parents=True,exist_ok=True)
    with requests.get(url,stream=True,timeout=600) as r:
        r.raise_for_status()
        with p.open('wb') as f:
            for c in r.iter_content(1024*1024):
                if c:f.write(c)
    if not p.exists() or p.stat().st_size==0: raise VideoProviderError('downloaded video is empty')
    return str(p)

def _classify(provider,r):
    if r.ok:return
    text=r.text[:1400]; low=text.lower()
    msg=f'{provider} HTTP {r.status_code}: {text}'
    if r.status_code in (401,402,403) or any(w in low for w in PERM_WORDS): raise PermanentProviderError(msg)
    if r.status_code in (408,425,429,500,502,503,504): raise TemporaryProviderError(msg)
    if r.status_code==404: raise PermanentProviderError(msg)
    raise VideoProviderError(msg)

def _semantic_error(provider,data):
    text=str(data); low=text.lower()
    if any(w in low for w in PERM_WORDS): raise PermanentProviderError(f'{provider}: {text[:1400]}')
    raise VideoProviderError(f'{provider}: {text[:1400]}')

def _find_value(payload, keys):
    if isinstance(payload, dict):
        for k in keys:
            v=payload.get(k)
            if isinstance(v,str) and v:
                return v
        for v in payload.values():
            found=_find_value(v,keys)
            if found:return found
    elif isinstance(payload,list):
        for item in payload:
            found=_find_value(item,keys)
            if found:return found
    return None

def _find_http_url(payload):
    if isinstance(payload,dict):
        for v in payload.values():
            if isinstance(v,str) and v.startswith('http'): return v
            found=_find_http_url(v)
            if found:return found
    elif isinstance(payload,list):
        for item in payload:
            found=_find_http_url(item)
            if found:return found
    return None

def _poll_nvidia(resp,headers):
    req_id=resp.headers.get('NVCF-REQID') or resp.headers.get('nvcf-reqid')
    if not req_id:
        try:req_id=(resp.json() or {}).get('reqId')
        except Exception:req_id=None
    if not req_id:
        raise TemporaryProviderError('nvidia returned 202 without NVCF request id')
    status_url=f"{settings.NVIDIA_COSMOS_BASE_URL.rstrip('/')}/status/{req_id}"
    deadline=time.time()+max(60,int(settings.NVIDIA_COSMOS_TIMEOUT))
    while time.time()<deadline:
        time.sleep(3)
        r=requests.get(status_url,headers=headers,timeout=60)
        if r.status_code==202:
            print('[VideoRouter][nvidia] status: in-progress')
            continue
        return r
    raise TemporaryProviderError('NVIDIA Cosmos generation timed out')

def _nvidia(prompt,image,out):
    key=_key('NVIDIA_API_KEY')
    if not key: raise PermanentProviderError('NVIDIA_API_KEY missing')
    base=str(settings.NVIDIA_COSMOS_BASE_URL or 'https://ai.api.nvidia.com/v1').rstrip('/')
    path=str(settings.NVIDIA_COSMOS_INFER_PATH or '/infer')
    if not path.startswith('/'): path='/'+path
    url=base+path
    body={
        'prompt':prompt[:4000],
        'image':_data_uri(image),
        'resolution':settings.NVIDIA_COSMOS_RESOLUTION,
        'num_output_frames':int(settings.NVIDIA_COSMOS_NUM_FRAMES),
        'fps':int(settings.NVIDIA_COSMOS_FPS),
        'steps':int(settings.NVIDIA_COSMOS_STEPS),
        'guidance_scale':float(settings.NVIDIA_COSMOS_GUIDANCE),
        'seed':random.randint(1,2_147_483_647),
    }
    if settings.NVIDIA_COSMOS_NEGATIVE_PROMPT:
        body['negative_prompt']=settings.NVIDIA_COSMOS_NEGATIVE_PROMPT
    headers={'Authorization':f'Bearer {key}','Content-Type':'application/json','Accept':'application/json'}
    print('[VideoRouter][nvidia] submitting Cosmos3 Nano:',url)
    try:
        r=requests.post(url,headers=headers,json=body,timeout=max(60,int(settings.NVIDIA_COSMOS_TIMEOUT)))
    except requests.Timeout as e:
        raise TemporaryProviderError(f'nvidia request timeout: {e}') from e
    except requests.RequestException as e:
        raise TemporaryProviderError(f'nvidia network error: {e}') from e
    if r.status_code==202:
        r=_poll_nvidia(r,headers)
    _classify('nvidia',r)
    try:data=r.json()
    except Exception as e: raise VideoProviderError(f'nvidia returned non-JSON response: {r.text[:500]}') from e
    b64_video=_find_value(data,('b64_video','b64_json'))
    if b64_video:
        if b64_video.startswith('data:') and ',' in b64_video:b64_video=b64_video.split(',',1)[1]
        try:raw=base64.b64decode(b64_video)
        except Exception as e: raise VideoProviderError(f'nvidia invalid base64 video: {e}') from e
        p=Path(out);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        if not p.exists() or p.stat().st_size==0: raise VideoProviderError('nvidia decoded video is empty')
        return str(p)
    url2=_find_http_url(data)
    if url2:return _download(url2,out)
    raise VideoProviderError(f'nvidia response did not contain video: {str(data)[:800]}')

def _pixverse(prompt,image,out):
    key=_key('PIXVERSE_API_KEY')
    if not key: raise PermanentProviderError('PIXVERSE_API_KEY missing')
    trace=str(uuid.uuid4()); headers={'API-KEY':key,'Ai-trace-id':trace}
    with open(image,'rb') as f:
        up=requests.post('https://app-api.pixverse.ai/openapi/v2/image/upload',headers=headers,files={'image':(Path(image).name,f)},timeout=90)
    _classify('pixverse',up); uj=up.json()
    if uj.get('ErrCode') not in (0,None): _semantic_error('pixverse',uj)
    img_id=(uj.get('Resp') or {}).get('img_id')
    if not img_id: raise VideoProviderError(f'PixVerse img_id missing: {uj}')
    trace=str(uuid.uuid4()); h={'API-KEY':key,'Ai-trace-id':trace,'Content-Type':'application/json'}
    sub=requests.post('https://app-api.pixverse.ai/openapi/v2/video/img/generate',headers=h,json={'duration':5,'img_id':img_id,'model':settings.PIXVERSE_MODEL,'motion_mode':'normal','prompt':prompt[:2000],'quality':'720p','seed':0},timeout=90)
    _classify('pixverse',sub); sj=sub.json()
    if sj.get('ErrCode') not in (0,None): _semantic_error('pixverse',sj)
    vid=(sj.get('Resp') or {}).get('video_id')
    if not vid: raise VideoProviderError(f'PixVerse video_id missing: {sj}')
    deadline=time.time()+900
    while time.time()<deadline:
        time.sleep(6)
        r=requests.get(f'https://app-api.pixverse.ai/openapi/v2/video/result/{vid}',headers={'API-KEY':key,'Ai-trace-id':str(uuid.uuid4())},timeout=60)
        _classify('pixverse',r); j=r.json()
        if j.get('ErrCode') not in (0,None): _semantic_error('pixverse',j)
        resp=j.get('Resp') or {}; status=resp.get('status')
        print('[VideoRouter][pixverse] status:',status)
        if status==1 and resp.get('url'): return _download(resp['url'],out)
        if str(status).lower() in ('failed','error','-1','5'): _semantic_error('pixverse',j)
    raise TemporaryProviderError('PixVerse timeout')

def _minimax(prompt,image,out):
    key=_key('MINIMAX_API_KEY')
    if not key: raise PermanentProviderError('MINIMAX_API_KEY missing')
    h={'Authorization':f'Bearer {key}','Content-Type':'application/json'}
    sub=requests.post('https://api.minimaxi.com/v1/video_generation',headers=h,json={'model':settings.MINIMAX_VIDEO_MODEL,'prompt':prompt[:2000],'first_frame_image':_data_uri(image),'duration':6,'resolution':'768P','prompt_optimizer':True},timeout=90)
    _classify('minimax',sub); sj=sub.json()
    if (sj.get('base_resp') or {}).get('status_code',0)!=0: _semantic_error('minimax',sj)
    task=sj.get('task_id')
    if not task: raise VideoProviderError(f'MiniMax task_id missing: {sj}')
    deadline=time.time()+900; file_id=None
    while time.time()<deadline:
        time.sleep(8)
        r=requests.get('https://api.minimaxi.com/v1/query/video_generation',headers={'Authorization':f'Bearer {key}'},params={'task_id':task},timeout=60)
        _classify('minimax',r); j=r.json(); status=str(j.get('status',''))
        print('[VideoRouter][minimax] status:',status)
        if status.lower()=='success': file_id=j.get('file_id'); break
        if status.lower() in ('fail','failed','cancelled','canceled'): _semantic_error('minimax',j)
    if not file_id: raise TemporaryProviderError('MiniMax timeout or file_id missing')
    r=requests.get('https://api.minimaxi.com/v1/files/retrieve',headers={'Authorization':f'Bearer {key}'},params={'file_id':file_id},timeout=60)
    _classify('minimax',r); j=r.json(); url=(j.get('file') or {}).get('download_url')
    if not url: raise VideoProviderError(f'MiniMax download_url missing: {j}')
    return _download(url,out)

def _fal(prompt,image,out):
    key=_key('FAL_API_KEY')
    if not key: raise PermanentProviderError('FAL_API_KEY missing')
    model='wan/v2.6/image-to-video'; h={'Authorization':f'Key {key}','Content-Type':'application/json'}
    sub=requests.post(f'https://queue.fal.run/{model}',headers=h,json={'prompt':prompt[:1500],'image_url':_data_uri(image),'resolution':'720p','duration':'5','enable_prompt_expansion':True,'multi_shots':False},timeout=60)
    _classify('fal',sub); j=sub.json(); su,ru=j.get('status_url'),j.get('response_url')
    if not su or not ru: raise VideoProviderError(f'fal queue URLs missing: {j}')
    deadline=time.time()+900
    while time.time()<deadline:
        r=requests.get(su,headers=h,timeout=60); _classify('fal',r); s=r.json(); st=str(s.get('status','')).upper(); print('[VideoRouter][fal]',st)
        if st=='COMPLETED': break
        if st in ('FAILED','CANCELLED'): _semantic_error('fal',s)
        time.sleep(5)
    else: raise TemporaryProviderError('fal timeout')
    r=requests.get(ru,headers=h,timeout=90); _classify('fal',r); x=r.json(); url=(x.get('video') or {}).get('url') if isinstance(x.get('video'),dict) else None
    if not url: raise VideoProviderError(f'fal video URL missing: {x}')
    return _download(url,out)

def _replicate(prompt,image,out):
    key=_key('REPLICATE_API_KEY')
    if not key: raise PermanentProviderError('REPLICATE_API_KEY missing')
    h={'Authorization':f'Bearer {key}','Content-Type':'application/json','Prefer':'wait=10','Cancel-After':'15m'}
    endpoint=f'https://api.replicate.com/v1/models/{settings.REPLICATE_VIDEO_OWNER}/{settings.REPLICATE_VIDEO_MODEL}/predictions'
    r=requests.post(endpoint,headers=h,json={'input':{'image':_data_uri(image),'prompt':prompt}},timeout=60); _classify('replicate',r); pred=r.json(); status=pred.get('status'); poll=(pred.get('urls') or {}).get('get')
    deadline=time.time()+900
    while status not in ('succeeded','failed','canceled'):
        if time.time()>deadline: raise TemporaryProviderError('Replicate timeout')
        time.sleep(3); r=requests.get(poll,headers={'Authorization':f'Bearer {key}'},timeout=60); _classify('replicate',r); pred=r.json(); status=pred.get('status'); print('[VideoRouter][replicate]',status)
    if status!='succeeded': _semantic_error('replicate',pred)
    o=pred.get('output'); url=o[0] if isinstance(o,list) and o else o if isinstance(o,str) else (o or {}).get('url') if isinstance(o,dict) else None
    if not url: raise VideoProviderError(f'Replicate output URL missing: {pred}')
    return _download(url,out)

def _novita(prompt,image,out):
    key=_key('NOVITA_API_KEY')
    if not key: raise PermanentProviderError('NOVITA_API_KEY missing')
    h={'Authorization':f'Bearer {key}','Content-Type':'application/json'}
    # Existing Novita adapter retained as best-effort. Provider errors fail over automatically.
    r=requests.post('https://api.novita.ai/v3/async/wan-2.2-i2v',headers=h,json={'prompt':prompt,'image':_data_uri(image)},timeout=60); _classify('novita',r); j=r.json(); task=j.get('task_id') or (j.get('task') or {}).get('task_id')
    if not task: _semantic_error('novita',j)
    deadline=time.time()+900
    while time.time()<deadline:
        time.sleep(5); p=requests.get('https://api.novita.ai/v3/async/task-result',params={'task_id':task},headers=h,timeout=60); _classify('novita',p); x=p.json(); t=x.get('task',x); st=str(t.get('status','')).upper(); print('[VideoRouter][novita]',st)
        if st in ('SUCCESS','SUCCEEDED','COMPLETED','FINISHED'):
            v=x.get('videos') or x.get('video') or t.get('videos') or t.get('video'); url=None
            if isinstance(v,list) and v: url=(v[0].get('video_url') or v[0].get('url')) if isinstance(v[0],dict) else v[0]
            elif isinstance(v,dict): url=v.get('video_url') or v.get('url')
            elif isinstance(v,str):url=v
            if url:return _download(url,out)
            raise VideoProviderError(f'Novita completed without URL: {x}')
        if st in ('FAILED','ERROR','CANCELLED'):_semantic_error('novita',x)
    raise TemporaryProviderError('Novita timeout')

def _modelslab(prompt,image,out):
    key=_key('MODELSLAB_API_KEY')
    if not key: raise PermanentProviderError('MODELSLAB_API_KEY missing')
    r=requests.post('https://modelslab.com/api/v6/video/img2video',json={'key':key,'model_id':'wan2.2','init_image':_data_uri(image),'prompt':prompt,'negative_prompt':'blurry, distorted, watermark','temp':False},timeout=60); _classify('modelslab',r); j=r.json()
    if str(j.get('status','')).lower()=='error': _semantic_error('modelslab',j)
    o=j.get('output')
    if isinstance(o,list) and o:return _download(o[0],out)
    fetch=j.get('fetch_result') or ((j.get('future_links') or [None])[0])
    if not fetch: _semantic_error('modelslab',j)
    deadline=time.time()+900
    while time.time()<deadline:
        time.sleep(5); p=requests.get(fetch,timeout=60); _classify('modelslab',p); x=p.json(); o=x.get('output')
        if isinstance(o,list) and o:return _download(o[0],out)
        if str(x.get('status','')).lower() in ('failed','error'):_semantic_error('modelslab',x)
    raise TemporaryProviderError('ModelsLab timeout')

def configured_provider_order(preferred=None):
    keys={'nvidia':'NVIDIA_API_KEY','pixverse':'PIXVERSE_API_KEY','minimax':'MINIMAX_API_KEY','fal':'FAL_API_KEY','replicate':'REPLICATE_API_KEY','novita':'NOVITA_API_KEY','modelslab':'MODELSLAB_API_KEY'}
    order=[x for x in DEFAULT_ORDER if _key(keys[x])]
    p=ALIASES.get((preferred or '').lower(),(preferred or '').lower())
    if p in order: order.remove(p); order.insert(0,p)
    return order

def generate_scene(prompt,reference_image,out,provider=None,router_state=None):
    state=router_state or VideoRouterState(); preferred=ALIASES.get((provider or '').lower(),(provider or '').lower())
    if preferred=='none':return None
    if preferred=='kling':
        # The user's legacy single KLING_API_KEY does not match the current verified access/secret-key auth contract.
        state.failures['kling']='Kling adapter requires current official access/secret credentials; skipped safely.'
    if preferred=='json2video':
        state.failures['json2video']='JSON2Video is a cloud renderer, not the primary generative-motion adapter; skipped in AI generation chain.'
    adapters={'nvidia':_nvidia,'pixverse':_pixverse,'minimax':_minimax,'fal':_fal,'replicate':_replicate,'novita':_novita,'modelslab':_modelslab}
    order=configured_provider_order(preferred)
    # Stick to the last provider that actually succeeded, so later scenes avoid
    # repeatedly touching slower/broken providers before the working one.
    if state.successful_provider in order and state.successful_provider not in state.disabled_providers:
        order.remove(state.successful_provider); order.insert(0,state.successful_provider)
    print('[VideoRouter] Provider order:',order)
    for name in order:
        if name in state.disabled_providers:
            print(f'[VideoRouter] Skipping {name}: disabled for this job'); continue
        try:
            print('[VideoRouter] Trying',name); path=adapters[name](prompt,reference_image,out); state.successful_provider=name; return {'path':path,'provider':name,'ai_generated':True}
        except PermanentProviderError as e:
            state.disabled_providers.add(name); state.failures[name]=str(e); print(f'[VideoRouter] PERMANENT FAILURE {name}: {e}')
        except TemporaryProviderError as e:
            state.failures[name]=str(e); print(f'[VideoRouter] TEMP FAILURE {name}: {e}')
        except Exception as e:
            # Unknown provider/model contract error: disable for this job to avoid repeating it every scene.
            state.disabled_providers.add(name); state.failures[name]=repr(e); print(f'[VideoRouter] ERROR {name}: {e}; disabled for job')
    print('[VideoRouter] All configured AI video providers failed; local motion fallback will be used.')
    return None
