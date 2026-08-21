import json, re, time, requests
from typing import Any, Dict, List
from app.config import settings

GEMINI_BASE='https://generativelanguage.googleapis.com/v1beta'
_GEMINI_CACHE=[]
_GEMINI_CACHE_AT=0.0
_GEMINI_WORKING=None
CACHE_TTL=3600
LANG_NAMES={'en':'English','ta':'Tamil','hi':'Hindi'}

def _key(name):
    v=getattr(settings,name,None)
    if not v: raise RuntimeError(f'{name} is not configured in .env')
    return str(v).strip()

def _json(text):
    text=re.sub(r'^```(?:json)?\s*|\s*```$','',str(text).strip(),flags=re.I|re.M)
    a,b=text.find('{'),text.rfind('}')
    if a<0 or b<a: raise RuntimeError('LLM returned non-JSON output')
    return json.loads(text[a:b+1])

def _gemini_models(force=False):
    global _GEMINI_CACHE,_GEMINI_CACHE_AT
    if _GEMINI_CACHE and not force and time.time()-_GEMINI_CACHE_AT<CACHE_TTL:
        return _GEMINI_CACHE[:]
    r=requests.get(f'{GEMINI_BASE}/models',params={'key':_key('GEMINI_API_KEY'),'pageSize':1000},timeout=30)
    r.raise_for_status(); items=[]
    for m in r.json().get('models',[]):
        if 'generateContent' not in m.get('supportedGenerationMethods',[]): continue
        n=m.get('name','').replace('models/',''); low=n.lower()
        if 'gemini' not in low or any(x in low for x in ['embedding','imagen','veo','tts','live','image','robotics','computer-use']): continue
        items.append(n)
    def score(n):
        l=n.lower(); s=0
        if 'flash' in l:s+=200
        if 'lite' in l:s+=20
        if any(x in l for x in ['preview','exp']):s-=100
        # prefer 3.x family over retired 2.x where available
        if '3.' in l:s+=80
        if '3.7' in l:s+=30
        elif '3.6' in l:s+=25
        elif '3.5' in l:s+=20
        elif '3.1' in l:s+=15
        if 'latest' in l:s-=5
        return s
    items=sorted(dict.fromkeys(items),key=score,reverse=True)
    _GEMINI_CACHE,_GEMINI_CACHE_AT=items,time.time()
    print('[Gemini] Available ranked models:',items)
    return items[:]

def _gemini(prompt):
    global _GEMINI_WORKING
    models=_gemini_models()
    if _GEMINI_WORKING in models: models=[_GEMINI_WORKING]+[x for x in models if x!=_GEMINI_WORKING]
    errors=[]
    for model in models[:8]:
        try:
            print('[Gemini] Trying:',model)
            r=requests.post(f'{GEMINI_BASE}/models/{model}:generateContent',params={'key':_key('GEMINI_API_KEY')},json={
                'contents':[{'role':'user','parts':[{'text':prompt}]}],
                'generationConfig':{'temperature':0.8,'topP':0.95,'maxOutputTokens':8192}
            },timeout=120)
            if not r.ok: raise RuntimeError(f'HTTP {r.status_code}: {r.text[:900]}')
            parts=(r.json().get('candidates') or [{}])[0].get('content',{}).get('parts',[])
            text='\n'.join(p.get('text','') for p in parts if p.get('text')).strip()
            if not text: raise RuntimeError('empty Gemini response')
            _GEMINI_WORKING=model; print('[Gemini] Success:',model); return text
        except Exception as e:
            errors.append(f'{model}: {e}'); print('[Gemini] Failed:',errors[-1])
    raise RuntimeError('All Gemini models failed:\n'+'\n'.join(errors))

def _openai_compat(base,key,model,prompt):
    r=requests.post(base,headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={
        'model':model,'messages':[{'role':'user','content':prompt}],'temperature':0.8,'max_tokens':8192
    },timeout=120)
    if not r.ok: raise RuntimeError(f'HTTP {r.status_code}: {r.text[:900]}')
    return r.json()['choices'][0]['message']['content'].strip()

def generate_text(prompt,provider='gemini'):
    p=(provider or 'gemini').lower()
    if p=='gemini': return _gemini(prompt)
    if p=='groq': return _openai_compat('https://api.groq.com/openai/v1/chat/completions',_key('GROQ_API_KEY'),'llama-3.3-70b-versatile',prompt)
    if p=='together': return _openai_compat('https://api.together.xyz/v1/chat/completions',_key('TOGETHER_API_KEY'),'meta-llama/Llama-3.3-70B-Instruct-Turbo',prompt)
    if p=='mistral': return _openai_compat('https://api.mistral.ai/v1/chat/completions',_key('MISTRAL_API_KEY'),'mistral-small-latest',prompt)
    if p=='openai': return _openai_compat('https://api.openai.com/v1/chat/completions',_key('OPENAI_API_KEY'),'gpt-4o-mini',prompt)
    raise ValueError(f'Unsupported LLM provider: {provider}')

def generate_text_auto(prompt,preferred='gemini'):
    order=[preferred,'gemini','groq','mistral','together','openai']; seen=[]; errors=[]
    for p in order:
        if not p or p in seen: continue
        seen.append(p)
        try:return generate_text(prompt,p)
        except Exception as e: errors.append(f'{p}: {e}'); print(f'[LLM] {p} failed:',e)
    raise RuntimeError('All LLM providers failed:\n'+'\n'.join(errors))

def build_story(user_input:str, provider='gemini', mode='builder', language='en', **kwargs):
    if mode=='custom': return {'title':'Custom Story','story':user_input,'summary':'User supplied story','suggested_duration':30}
    lang=LANG_NAMES.get(language,language)
    autonomous='Invent a fresh episode under this ongoing direction.' if mode=='autonomous' else 'Turn the idea into one complete story.'
    prompt=f"""You are Culprit Studio Pro's story writer. {autonomous}\nLanguage: {lang}. ALL narration must be in {lang}.\nUser direction: {user_input}\nReturn ONLY JSON: {{"title":"","story":"","summary":"","suggested_duration":30}}. Keep it coherent, original and suitable for video."""
    return _json(generate_text_auto(prompt,provider))

def plan_video(config:Dict[str,Any])->Dict[str,Any]:
    story=str(config.get('story') or config.get('prompt') or '').strip()
    if not story: raise ValueError('No story/prompt supplied')
    lang=LANG_NAMES.get(config.get('language','en'),config.get('language','en'))
    seconds=max(10,int(config.get('duration_seconds',30)))
    # dynamic scenes, roughly one 4-6 second clip
    scene_count=max(3,min(24,round(seconds/5)))
    art=config.get('art_style','Modern Cartoon'); ratio=config.get('aspect_ratio','9:16')
    prompt=f"""You are an AI video director. Build a production plan from this story:\n{story}\n\nLanguage: {lang}\nArt style: {art}\nAspect ratio: {ratio}\nTarget duration: {seconds} seconds\nCreate exactly {scene_count} scenes.\n\nReturn ONLY JSON with this structure:\n{{"title":"","description":"","hashtags":["#tag"],"character_bible":"consistent recurring character description","scenes":[{{"scene":1,"narration":"","caption":"short foreground subtitle","visual_prompt":"detailed reference-image prompt","motion_prompt":"moving-video prompt: subject motion + environment motion + camera movement","duration":5}}]}}\n\nRules:\n- narration and caption MUST be in {lang}.\n- visual_prompt/motion_prompt can be English for model quality.\n- Maintain the same character appearance across scenes using character_bible.\n- Every motion_prompt must describe real movement, not a slideshow.\n- Keep captions short and readable.\n- Total pacing should approximate {seconds}s."""
    plan=_json(generate_text_auto(prompt,config.get('llm_provider','gemini')))
    scenes=plan.get('scenes') or []
    if not scenes: raise RuntimeError('Planner returned no scenes')
    bible=str(plan.get('character_bible','')).strip()
    norm=[]
    for i,s in enumerate(scenes,1):
        if not isinstance(s,dict):continue
        narration=str(s.get('narration','')).strip()
        if not narration:continue
        visual=str(s.get('visual_prompt') or narration).strip()
        motion=str(s.get('motion_prompt') or visual).strip()
        if bible:
            visual=f'{bible}. {visual}'
            motion=f'Keep character identity exactly consistent: {bible}. {motion}'
        norm.append({**s,'scene':i,'narration':narration,'caption':str(s.get('caption') or narration).strip(),'visual_prompt':visual,'motion_prompt':motion,'duration':float(s.get('duration') or 5)})
    if not norm: raise RuntimeError('Planner returned unusable scenes')
    plan['scenes']=norm; plan.setdefault('title',config.get('title') or 'Untitled Video'); plan.setdefault('description',''); plan.setdefault('hashtags',[])
    return plan
