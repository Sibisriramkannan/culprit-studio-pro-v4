from pathlib import Path
from datetime import datetime, timezone
import uuid, json, re
from app.config import settings
from app.db import insert_job, update_job
from app.providers.llm import plan_video
from app.providers.image import generate_reference
from app.providers.video import generate_scene, VideoRouterState
from app.providers.tts import synth
from app.providers.storage import upload_folder
from app.providers.youtube import upload as youtube_upload
from app.video_editor import still_to_motion, overlay_caption_on_video, concat_and_mix, duration

def write_json(path,data): Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def run(config):
    jid=datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]
    title=config.get('title') or 'Untitled Video'; insert_job(jid,config.get('mode','manual'),title,config)
    job=Path(settings.OUTPUT_DIR)/jid; job.mkdir(parents=True,exist_ok=True)
    def status(stage,progress): update_job(jid,status='running',stage=stage,progress=progress)
    try:
        status('planning',5); plan=plan_video(config); title=plan.get('title') or title; update_job(jid,title=title); write_json(job/'plan.json',plan)
        scenes=plan.get('scenes') or []
        if not scenes: raise RuntimeError('Video plan contains no scenes')
        narration=' '.join(str(s.get('narration','')).strip() for s in scenes if s.get('narration')).strip()
        if not narration: raise RuntimeError('Video plan contains no narration')
        status('voice',15); audio=job/'voice.mp3'; synth(narration,str(audio),config.get('voice_provider','edge'),config.get('voice_id','en-US-JennyNeural'),config.get('language','en'))
        total=max(1.0,duration(str(audio))); default_each=max(2.0,total/len(scenes))
        router=VideoRouterState(); preferred=config.get('video_provider','none'); clips=[]; report=[]
        for i,scene in enumerate(scenes,1):
            status(f'scene {i}/{len(scenes)}',20+int((i-1)/len(scenes)*55)); visual=str(scene.get('visual_prompt') or scene.get('narration','')).strip(); motion=str(scene.get('motion_prompt') or visual).strip(); caption=str(scene.get('caption') or scene.get('narration','')).strip()
            ref=job/f'scene-{i:02}-reference.png'
            try:
                generate_reference(f"{visual}. Style: {config.get('art_style','cinematic')}. No text, subtitles or watermark.",str(ref),config.get('image_provider','huggingface'))
            except Exception as e:
                print('[Pipeline] Reference image failed:',repr(e)); from PIL import Image,ImageDraw
                size=(768,1365) if config.get('aspect_ratio','9:16')=='9:16' else (1365,768); im=Image.new('RGB',size,(24,29,55)); ImageDraw.Draw(im).text((40,80),f'Scene {i}',fill='white'); im.save(ref)
            raw=job/f'scene-{i:02}-raw.mp4'; final_scene=job/f'scene-{i:02}.mp4'; generated=None
            if str(preferred).lower()!='none':
                generated=generate_scene(motion,str(ref),str(raw),preferred,router_state=router)
            used='local-ffmpeg'
            if generated:
                raw_path=generated['path'] if isinstance(generated,dict) else str(generated); used=(generated.get('provider','ai') if isinstance(generated,dict) else 'ai')
            else:
                sec=max(2.0,float(scene.get('duration') or default_each)); still_to_motion(str(ref),str(raw),sec,config.get('aspect_ratio','9:16'),config.get('effects',[])); raw_path=str(raw)
            # Captions are applied AFTER AI generation, so every provider gets the selected foreground style.
            overlay_caption_on_video(raw_path,caption,str(final_scene),config.get('caption_style','bold-stroke'),config.get('aspect_ratio','9:16'),config.get('language','en'))
            clips.append(str(final_scene)); report.append({'scene':i,'provider':used,'mode':'ai-video' if generated else 'fallback'})
        write_json(job/'video-provider-report.json',{'preferred':preferred,'successful_provider':router.successful_provider,'disabled_providers':sorted(router.disabled_providers),'failures':router.failures,'scenes':report})
        status('compositing',82); final=job/'final.mp4'; concat_and_mix(clips,str(audio),str(final),config.get('music_path'))
        if not final.exists(): raise RuntimeError('final.mp4 was not created')
        hf_uri=None
        if config.get('storage_mode','download') in ('huggingface','both'):
            status('hugging face upload',90)
            try:hf_uri=upload_folder(str(job),f'generated/{jid}')
            except Exception as e: print('[Pipeline] HF upload warning:',repr(e))
        yt_id=None
        if config.get('upload_to_youtube'):
            status('youtube upload',95); tags=plan.get('hashtags',[]); desc=(str(plan.get('description',''))+'\n\n'+' '.join(map(str,tags if isinstance(tags,list) else [tags]))).strip(); y=youtube_upload(str(final),title,desc,config.get('youtube_privacy','private')); yt_id=y.get('id') if isinstance(y,dict) else None
        update_job(jid,status='completed',stage='done',progress=100,video_path=str(final),youtube_video_id=yt_id,completed_at=datetime.now(timezone.utc).isoformat())
        return {'job_id':jid,'title':title,'status':'completed','video':str(final),'hf_uri':hf_uri,'youtube_video_id':yt_id,'video_router':{'successful_provider':router.successful_provider,'disabled_providers':sorted(router.disabled_providers),'failures':router.failures},'scene_providers':report}
    except Exception as e:
        update_job(jid,status='failed',stage='failed',error=str(e),completed_at=datetime.now(timezone.utc).isoformat()); print('[Pipeline] FAILED:',repr(e)); raise
