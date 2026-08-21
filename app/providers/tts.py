from pathlib import Path
import asyncio, requests
from app.config import settings

MALE_MARKERS=('Guy','Christopher','Eric','Roger','Madhur','Valluvar')
LANG_DEFAULTS={
 'en':{'male':'en-US-GuyNeural','female':'en-US-JennyNeural'},
 'ta':{'male':'ta-IN-ValluvarNeural','female':'ta-IN-PallaviNeural'},
 'hi':{'male':'hi-IN-MadhurNeural','female':'hi-IN-SwaraNeural'},
}

def resolve_voice(voice,language='en'):
    lang=(language or 'en').lower()
    if lang=='en' and voice: return voice
    gender='male' if any(x.lower() in str(voice).lower() for x in MALE_MARKERS) else 'female'
    return LANG_DEFAULTS.get(lang,LANG_DEFAULTS['en'])[gender]

async def _edge(text,voice,out):
    import edge_tts
    await edge_tts.Communicate(text=text,voice=voice).save(out)

def synth(text,out,provider='edge',voice='en-US-JennyNeural',language='en'):
    out=str(out); Path(out).parent.mkdir(parents=True,exist_ok=True); text=str(text).strip(); provider=(provider or 'edge').lower()
    if not text: raise RuntimeError('TTS received empty narration')
    voice=resolve_voice(voice,language)
    if provider=='edge':
        asyncio.run(_edge(text,voice,out))
    elif provider=='elevenlabs':
        if not settings.ELEVENLABS_API_KEY: raise RuntimeError('ELEVENLABS_API_KEY missing')
        r=requests.post(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}',headers={'xi-api-key':settings.ELEVENLABS_API_KEY,'Accept':'audio/mpeg','Content-Type':'application/json'},json={'text':text,'model_id':'eleven_multilingual_v2'},timeout=180)
        r.raise_for_status(); Path(out).write_bytes(r.content)
    elif provider=='deepgram':
        if not settings.DEEPGRAM_API_KEY: raise RuntimeError('DEEPGRAM_API_KEY missing')
        model=voice if str(voice).startswith('aura-') else 'aura-2-thalia-en'
        r=requests.post('https://api.deepgram.com/v1/speak',params={'model':model},headers={'Authorization':f'Token {settings.DEEPGRAM_API_KEY}','Content-Type':'application/json'},json={'text':text},timeout=180)
        r.raise_for_status(); Path(out).write_bytes(r.content)
    else: raise ValueError(f'Unsupported TTS provider: {provider}')
    p=Path(out)
    if not p.exists() or p.stat().st_size==0: raise RuntimeError(f'{provider} produced empty audio')
    return str(p)
