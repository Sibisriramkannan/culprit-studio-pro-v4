import subprocess, json, os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CAPTION_PRESETS={
 'bold-stroke': {'size':72,'stroke':8,'bg':None,'font':'heavy','fill':'white','shadow':True,'y':0.72},
 'red-highlight': {'size':68,'stroke':2,'bg':'red','font':'heavy','fill':'white','shadow':False,'y':0.72},
 'sleek': {'size':52,'stroke':2,'bg':'glass','font':'clean','fill':'white','shadow':True,'y':0.78},
 'karaoke': {'size':66,'stroke':3,'bg':'purple','font':'heavy','fill':'white','shadow':True,'y':0.72},
 'majestic': {'size':64,'stroke':3,'bg':None,'font':'serif','fill':'gold','shadow':True,'y':0.69},
 'beast': {'size':82,'stroke':9,'bg':None,'font':'impact','fill':'white','shadow':True,'y':0.67},
 'elegant': {'size':58,'stroke':2,'bg':'glass','font':'serif','fill':'white','shadow':True,'y':0.75},
 'pixel': {'size':58,'stroke':4,'bg':'black','font':'mono','fill':'lime','shadow':False,'y':0.74},
 'clarity': {'size':56,'stroke':3,'bg':'black','font':'clean','fill':'white','shadow':False,'y':0.77},
 'neon': {'size':66,'stroke':4,'bg':None,'font':'heavy','fill':'cyan','shadow':True,'y':0.70},
 'comic': {'size':64,'stroke':5,'bg':'yellow','font':'heavy','fill':'black','shadow':True,'y':0.68},
 'minimal': {'size':46,'stroke':1,'bg':'glass','font':'clean','fill':'white','shadow':False,'y':0.81},
}
COLORS={'red':(190,30,45,235),'purple':(95,55,220,235),'black':(0,0,0,210),'yellow':(245,190,35,235),'glass':(5,8,18,150)}
FILLS={'white':(255,255,255,255),'gold':(255,218,120,255),'lime':(168,255,95,255),'cyan':(120,240,255,255),'black':(20,20,25,255)}

def duration(path):
    out=subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',path],text=True,encoding='utf-8',errors='replace')
    return float(json.loads(out)['format']['duration'])

def _fit(src,W,H):
    im=Image.open(src).convert('RGB'); s=max(W/im.width,H/im.height); im=im.resize((int(im.width*s),int(im.height*s)))
    return im.crop(((im.width-W)//2,(im.height-H)//2,(im.width+W)//2,(im.height+H)//2))

def _font_candidates(group,language):
    win='C:/Windows/Fonts'; linux='/usr/share/fonts/truetype'
    if language in ('ta','hi'):
        # Nirmala UI has Indic coverage on modern Windows. Linux candidates use Noto/DejaVu when installed.
        return [f'{win}/NirmalaB.ttf',f'{win}/Nirmala.ttf','/usr/share/fonts/truetype/noto/NotoSansTamil-Bold.ttf','/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf',f'{linux}/dejavu/DejaVuSans-Bold.ttf']
    groups={
      'heavy':[f'{win}/impact.ttf',f'{win}/arialbd.ttf',f'{linux}/dejavu/DejaVuSans-Bold.ttf'],
      'impact':[f'{win}/impact.ttf',f'{win}/arialbd.ttf',f'{linux}/dejavu/DejaVuSans-Bold.ttf'],
      'serif':[f'{win}/georgiab.ttf',f'{win}/timesbd.ttf',f'{linux}/dejavu/DejaVuSerif-Bold.ttf'],
      'mono':[f'{win}/consolab.ttf',f'{win}/courbd.ttf',f'{linux}/dejavu/DejaVuSansMono-Bold.ttf'],
      'clean':[f'{win}/segoeuib.ttf',f'{win}/arial.ttf',f'{linux}/dejavu/DejaVuSans.ttf'],
    }
    return groups.get(group,groups['clean'])

def _font(group,size,language='en'):
    for p in _font_candidates(group,language):
        if Path(p).exists():
            try:return ImageFont.truetype(p,size,layout_engine=getattr(ImageFont.Layout,'RAQM',None))
            except Exception:
                try:return ImageFont.truetype(p,size)
                except Exception:pass
    return ImageFont.load_default()

def _wrap(draw,text,font,maxw,stroke):
    # Word wrapping works for English/Hindi/Tamil input containing spaces. Long tokens fall back gracefully.
    words=str(text).split(); lines=[]; line=''
    for word in words:
        test=(line+' '+word).strip(); box=draw.textbbox((0,0),test,font=font,stroke_width=stroke)
        if box[2]-box[0]>maxw and line: lines.append(line); line=word
        else: line=test
    if line:lines.append(line)
    return '\n'.join(lines[:3])

def render_caption_overlay(text,out,style='bold-stroke',ratio='9:16',language='en'):
    W,H=(1080,1920) if ratio=='9:16' else (1920,1080); cfg=CAPTION_PRESETS.get(style,CAPTION_PRESETS['bold-stroke'])
    layer=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(layer); font=_font(cfg['font'],cfg['size'],language)
    text=_wrap(d,text,font,int(W*.82),cfg['stroke'])
    box=d.multiline_textbbox((0,0),text,font=font,spacing=10,align='center',stroke_width=cfg['stroke']); tw,th=box[2]-box[0],box[3]-box[1]
    x=(W-tw)//2; y=int(H*cfg['y'])
    if cfg['bg']:
        d.rounded_rectangle((x-28,y-18,x+tw+28,y+th+22),20,fill=COLORS[cfg['bg']])
    if cfg['shadow']:
        d.multiline_text((x+4,y+6),text,font=font,fill=(0,0,0,160),spacing=10,align='center',stroke_width=cfg['stroke']+1,stroke_fill=(0,0,0,170))
    d.multiline_text((x,y),text,font=font,fill=FILLS[cfg['fill']],spacing=10,align='center',stroke_width=cfg['stroke'],stroke_fill=(0,0,0,255))
    layer.save(out); return out

def caption_image(src,text,out,style,ratio,language='en'):
    W,H=(1080,1920) if ratio=='9:16' else (1920,1080); base=_fit(src,W,H).convert('RGBA'); overlay=Path(out).with_suffix('.overlay.png')
    render_caption_overlay(text,overlay,style,ratio,language); base.alpha_composite(Image.open(overlay).convert('RGBA')); base.convert('RGB').save(out,quality=94); overlay.unlink(missing_ok=True); return out

def overlay_caption_on_video(video,text,out,style,ratio,language='en'):
    # AI providers frequently return landscape clips even for a Shorts project.
    # Normalize/crop the raw clip to the requested canvas BEFORE adding captions.
    W,H=(1080,1920) if ratio=='9:16' else (1920,1080)
    overlay=Path(out).with_suffix('.caption-overlay.png'); render_caption_overlay(text,overlay,style,ratio,language)
    fc=(f'[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,'
        f'crop={W}:{H},setsar=1[base];[base][1:v]overlay=0:0:format=auto,format=yuv420p[v]')
    subprocess.run(['ffmpeg','-y','-i',video,'-i',str(overlay),'-filter_complex',fc,'-map','[v]','-an','-c:v','libx264','-preset','veryfast','-shortest',out],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    overlay.unlink(missing_ok=True); return out

def still_to_motion(image,out,seconds,ratio,effects):
    W,H=(1080,1920) if ratio=='9:16' else (1920,1080)
    vf=[f'scale={W}:{H}:force_original_aspect_ratio=increase',f'crop={W}:{H}']
    if 'kenburns' in effects: vf=[f'scale={W}:{H}:force_original_aspect_ratio=increase',f'crop={W}:{H}',f"zoompan=z='min(zoom+0.0008,1.08)':d={max(1,int(seconds*25))}:s={W}x{H}:fps=25"]
    if 'vignette' in effects:vf.append('vignette')
    if 'filmgrain' in effects:vf.append('noise=alls=5:allf=t')
    vf.append('format=yuv420p')
    subprocess.run(['ffmpeg','-y','-loop','1','-i',image,'-t',str(seconds),'-vf',','.join(vf),'-an','-c:v','libx264','-preset','veryfast',out],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); return out

def concat_and_mix(clips,audio,out,music=None):
    wd=Path(out).parent/'_compose'; wd.mkdir(exist_ok=True); listing=wd/'clips.txt'; listing.write_text('\n'.join(f"file '{Path(x).resolve().as_posix()}'" for x in clips),encoding='utf-8')
    base=wd/'base.mp4'; subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(listing),'-c','copy',str(base)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    if music and Path(music).exists(): cmd=['ffmpeg','-y','-i',str(base),'-i',audio,'-stream_loop','-1','-i',music,'-filter_complex','[2:a]volume=.10[m];[1:a][m]amix=inputs=2:duration=first[a]','-map','0:v','-map','[a]','-shortest','-c:v','copy','-c:a','aac',out]
    else: cmd=['ffmpeg','-y','-i',str(base),'-i',audio,'-map','0:v','-map','1:a','-shortest','-c:v','copy','-c:a','aac',out]
    subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); return out
