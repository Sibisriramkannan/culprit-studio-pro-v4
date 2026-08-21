from pathlib import Path
import base64
from app.config import settings

def generate_reference(prompt,out,provider='huggingface'):
    out=Path(out); out.parent.mkdir(parents=True,exist_ok=True); provider=(provider or 'huggingface').lower()
    if provider=='huggingface':
        if not settings.HUGGINGFACE_API_KEY: raise RuntimeError('HUGGINGFACE_API_KEY missing')
        from huggingface_hub import InferenceClient
        image=InferenceClient(token=settings.HUGGINGFACE_API_KEY).text_to_image(prompt,model='black-forest-labs/FLUX.1-schnell')
        image.save(out); return str(out)
    if provider=='openai':
        if not settings.OPENAI_API_KEY: raise RuntimeError('OPENAI_API_KEY missing')
        from openai import OpenAI
        r=OpenAI(api_key=settings.OPENAI_API_KEY).images.generate(model='gpt-image-1',prompt=prompt,size='1024x1536')
        if getattr(r.data[0],'b64_json',None): out.write_bytes(base64.b64decode(r.data[0].b64_json)); return str(out)
        raise RuntimeError('OpenAI returned no image data')
    raise ValueError(f'Unsupported reference image provider: {provider}')
