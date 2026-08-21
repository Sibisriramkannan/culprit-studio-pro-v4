const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
let catalog={}, page="home";
const manual={mode:"manual",story_mode:"builder",story:"",title:"",language:"en",llm_provider:"gemini",voice_provider:"edge",voice_id:"en-US-JennyNeural",music_mode:"auto",music_provider:"library",music_mood:"Auto",music_path:null,art_style:"Modern Cartoon",image_provider:"huggingface",video_provider:"auto",animated_hook:false,caption_style:"bold-stroke",effects:["kenburns"],storage_mode:"download",aspect_ratio:"9:16",duration_seconds:30,upload_to_youtube:false,youtube_privacy:"private"};
const auto=JSON.parse(JSON.stringify({...manual,mode:"automation",story_mode:"autonomous"}));
let mStep=0,aStep=0;

function toast(t){let x=$("#toast");x.textContent=t;x.classList.add("show");setTimeout(()=>x.classList.remove("show"),2600)}
function setPage(p){page=p;$$("#nav button").forEach(b=>b.classList.toggle("active",b.dataset.page===p));$("#sidebar").classList.remove("open");render()}
$$("#nav button").forEach(b=>b.onclick=()=>setPage(b.dataset.page));
$("#menuBtn").onclick=()=>$("#sidebar").classList.toggle("open");

const titles={
home:["Home","Monitor your factory and launch a new workflow."],
manual:["Manual Studio","Review every creative decision before generation."],
automation:["Automation Studio","Build once, then let the factory generate on schedule."],
schedules:["Scheduler List","Manage local-time triggers, history and run-now actions."],
settings:["Settings","Providers, storage and YouTube connection."]
};
function header(){let t=titles[page];$("#pageTitle").textContent=t[0];$("#pageSub").textContent=t[1]}

async function api(url,opt){let r=await fetch(url,opt);let j=await r.json().catch(()=>({}));if(!r.ok)throw new Error(j.detail||j.error||r.statusText);return j}
function esc(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]))}
function artSlug(s){return s.toLowerCase().replaceAll(" ","-").replaceAll("/","-")}
function cardHead(title,sub,step,total=7){return `<div class="stepHead"><div><h2>${title}</h2><p>${sub}</p></div><span class="pill">STEP ${step+1} OF ${total}</span></div>`}
function progress(step,total=7){return `<div class="progress">${Array.from({length:total},(_,i)=>`<i class="${i<=step?'on':''}"></i>`).join("")}</div>`}

async function home(){
 let d=await api("/api/dashboard").catch(()=>({jobs:{total:0,completed:0,failed:0,active:0},recent_jobs:[],youtube:null}));
 let yt=d.youtube, subs=yt?.statistics?.subscriberCount||"—", views=yt?.statistics?.viewCount||"—";
 $("#page").innerHTML=`<div class="hero">
  <section class="glass heroCard"><span class="eyebrow">AI VIDEO OPERATIONS</span><h2>Generate, automate and monitor from one studio.</h2><p>Build one-off videos with human review, or create autonomous schedules that write, generate and upload at the right time.</p><div class="quick"><button class="primary" data-go="manual">+ Manual Video</button><button class="secondary" data-go="automation">+ Automation</button><button class="ghost" data-go="schedules">Scheduler List</button></div></section>
  <div class="metrics"><div class="glass metric"><small>Videos generated</small><strong>${d.jobs.total}</strong><span>${d.jobs.active} active</span></div><div class="glass metric"><small>YouTube views</small><strong>${views}</strong><span>${yt?"Connected":"Connect in settings"}</span></div><div class="glass metric"><small>Completed</small><strong>${d.jobs.completed}</strong><span>successful jobs</span></div><div class="glass metric"><small>Subscribers</small><strong>${subs}</strong><span>${yt?.title||"YouTube"}</span></div></div>
 </div>
 <section class="glass chartCard"><div class="sectionTitle"><h3>Live performance monitor</h3><span>YouTube reach + generation activity</span></div><div class="chart"><svg viewBox="0 0 1000 220" preserveAspectRatio="none"><defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#6f4aff" stop-opacity=".35"/><stop offset="1" stop-color="#6f4aff" stop-opacity="0"/></linearGradient></defs><path d="M0,180 C80,175 120,120 200,135 S340,80 430,102 S560,55 640,88 S790,35 1000,48 L1000,220 L0,220Z" fill="url(#area)"/><path d="M0,180 C80,175 120,120 200,135 S340,80 430,102 S560,55 640,88 S790,35 1000,48" fill="none" stroke="#7954ff" stroke-width="4"/></svg></div></section>
 <div class="sectionTitle"><h3>Recent jobs</h3><span>${d.recent_jobs.length} shown</span></div>${jobsTable(d.recent_jobs)}`;
 $$("[data-go]").forEach(b=>b.onclick=()=>setPage(b.dataset.go));
}
function jobsTable(rows){if(!rows.length)return `<div class="glass empty">No video jobs yet. Start with Manual or Automation.</div>`;
 return `<div class="glass tableWrap"><table class="table"><thead><tr><th>Title</th><th>Mode</th><th>Status</th><th>Stage</th><th>Created</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${esc(r.title)}</td><td>${r.mode}</td><td><span class="badge ${r.status==="failed"?"fail":r.status!=="completed"?"wait":""}">${r.status}</span></td><td>${esc(r.stage)}</td><td>${(r.created_at||"").replace("T"," ").slice(0,16)}</td></tr>`).join("")}</tbody></table></div>`}

function manualPage(){wizard(manual,mStep,false)}
function automationPage(){wizard(auto,aStep,true)}
function wizard(state,step,isAuto){
 const total=isAuto?8:7; let h=progress(step,total),body="";
 if(step===0){
   body=cardHead(isAuto?"Automation Content Brain":"Story & Prompt","Choose how the story enters the production pipeline.",step,total)+`
   <div class="tabs">${(isAuto?[["builder","AI Story Builder"],["custom","Direct Full Prompt"],["autonomous","Autonomous Topic"]]:[["builder","AI Story Builder"],["custom","Custom Story"]]).map(x=>`<button data-storymode="${x[0]}" class="${state.story_mode===x[0]?"active":""}">${x[1]}</button>`).join("")}</div>
   ${state.story_mode!=="custom"?`<div class="grid2"><div><label>LLM model</label><select id="llm">${catalog.llm.map(x=>`<option value="${x.id}" ${x.id===state.llm_provider?"selected":""}>${x.name}</option>`).join("")}</select></div><div><label>Language</label><select id="storyLang">${catalog.languages.map(x=>`<option value="${x.id}" ${x.id===state.language?"selected":""}>${x.name}</option>`).join("")}</select></div></div>`:""}
   <label>${state.story_mode==="autonomous"?"One-line autonomous direction":state.story_mode==="custom"?"Full story / production prompt":"Idea or topic"}</label>
   <textarea id="storyInput" placeholder="${state.story_mode==="autonomous"?"Example: Generate learning videos for kids":state.story_mode==="custom"?"Paste complete story here...":"Describe the story you want..."}">${esc(state.story||"")}</textarea>
   ${state.story_mode==="builder"?`<button id="buildStory" class="secondary" style="margin-top:12px">✦ Generate Story for Review</button>`:""}
   <div id="storyReview">${state.title||state.story?storyReview(state):""}</div>`;
 } else if(step===1){
   body=cardHead("Language & Voice","Choose English, Tamil or Hindi, then preview a voice.",step,total)+`
   <div class="grid2"><div><label>Language</label><select id="lang">${catalog.languages.map(x=>`<option value="${x.id}" ${x.id===state.language?"selected":""}>${x.name}</option>`).join("")}</select></div><div><label>Voice provider</label><select id="vp"><option value="edge">Prototype voices</option><option value="elevenlabs">ElevenLabs</option><option value="deepgram">Deepgram</option></select></div></div>
   <div class="tiles" style="margin-top:15px">${catalog.voices.filter(v=>!v.language || v.language===state.language).map(v=>`<div class="tile ${state.voice_id===v.id?"selected":""}" data-select="voice" data-val="${v.id}"><div class="voiceRow"><div><b>${v.name}</b><small>${v.gender} · ${v.tag}</small></div><button class="play" data-play="${v.id}">▶</button></div></div>`).join("")}</div>`;
 } else if(step===2){
   body=cardHead("Background Music","Let Culprit match the story mood, or upload your own audio.",step,total)+`
   <div class="tiles">${[["auto","AI / Auto Match","Story mood → suitable soundtrack"],["upload","Upload Music","Use your own MP3/WAV"],["none","No Music","Voice + video only"]].map(x=>`<div class="tile ${state.music_mode===x[0]?"selected":""}" data-select="music" data-val="${x[0]}"><b>${x[1]}</b><small>${x[2]}</small></div>`).join("")}</div>
   <label>Music mood</label><select id="mood">${catalog.music_moods.map(x=>`<option ${x===state.music_mood?"selected":""}>${x}</option>`).join("")}</select>
   ${state.music_mode==="upload"?`<label>Upload audio</label><input id="musicFile" type="file" accept=".mp3,.wav,.m4a"><button id="uploadMusic" class="secondary" style="margin-top:10px">Upload Track</button><small id="musicPath" style="display:block;color:#8f98b4;margin-top:8px">${esc(state.music_path||"No file uploaded")}</small>`:""}`;
 } else if(step===3){
   body=cardHead("Art Style & Moving Video","Select the visual identity. This preset is fed into the moving-video scene prompts.",step,total)+`
   <div class="tiles">${catalog.art_styles.map(x=>`<div class="tile ${state.art_style===x?"selected":""}" data-select="art" data-val="${esc(x)}"><img class="previewArt" src="/static/previews/art/${artSlug(x)}.svg"><b>${x}</b><small>Scene + motion prompt preset</small></div>`).join("")}</div>
   <label>Animated video model</label><small style="display:block;color:#8f98b4;margin:0 0 10px">Selected model is tried first. On quota/API failure, Culprit automatically redirects to the next configured AI video provider.</small><div class="tiles">${catalog.video.map(v=>`<div class="tile ${state.video_provider===v.id?"selected":""}" data-select="video" data-val="${v.id}"><div class="effectPreview ${v.id==="none"?"":"particles"}"></div><b>${v.name}</b><small>${v.badge||""} · ${v.status}</small></div>`).join("")}</div>`;
 } else if(step===4){
   body=cardHead("Foreground Captions","Animated-looking foreground subtitle styles with live visual previews.",step,total)+`
   <div class="tiles">${catalog.captions.map(c=>`<div class="tile ${state.caption_style===c.id?"selected":""}" data-select="caption" data-val="${c.id}"><div class="captionPreview ${c.id==="red-highlight"?"red":c.id}"><span>${c.name==="Red Highlight"?"HOOK":c.name.toUpperCase()}</span></div><b>${c.name}</b></div>`).join("")}</div>`;
 } else if(step===5){
   body=cardHead("Effects","Choose video effects. Every card includes a motion preview.",step,total)+`
   <div class="tiles">${catalog.effects.map(e=>`<div class="tile ${state.effects.includes(e.id)?"selected":""}" data-effect="${e.id}"><div class="effectPreview ${e.id}"></div><b>${e.name}</b><small>${e.desc}</small></div>`).join("")}</div>`;
 } else if(step===6 && !isAuto){
   body=outputStep(state,step,total,false);
 } else if(step===6 && isAuto){
   body=outputStep(state,step,total,true);
 } else if(step===7 && isAuto){
   body=cardHead("Trigger & Scheduler","Choose when this automation runs. Times use the machine's local timezone.",step,total)+`
   <div class="grid3"><div><label>Schedule name</label><input id="schedName" value="${esc(state.title||"Automation")}"></div><div><label>Trigger</label><select id="preset"><option value="every_2_hours">Every 2 hours</option><option value="daily">Every day</option><option value="twice_daily">Every day (2 times)</option><option value="weekly">Every week</option><option value="custom">Custom cron</option></select></div><div><label>Primary time</label><input id="localTime" type="time" value="18:00"></div></div>
   <div class="grid3"><div><label>Second time</label><input id="secondTime" type="time" value="21:00"></div><div><label>Weekday (0=Mon)</label><input id="weekday" type="number" min="0" max="6" value="0"></div><div><label>Custom cron</label><input id="cron" placeholder="0 18 * * *"></div></div>
   <div class="storyBox"><b>Automation pipeline</b><p style="color:#8f98b4;line-height:1.7">Trigger → autonomous story/prompt → moving scenes → voice → music → captions → effects → final MP4 → storage → optional YouTube upload.</p></div>`;
 }
 $("#page").innerHTML=`<div class="wizard">${h}<section class="glass card">${body}</section><div class="wizActions"><button id="back" class="ghost" style="visibility:${step?"visible":"hidden"}">← Back</button><button id="next" class="primary">${step===total-1?(isAuto?"Complete Automation ✦":"Generate Video ✦"):"Continue →"}</button></div><pre id="result" style="white-space:pre-wrap;color:#8ff0b3"></pre></div>`;
 bindWizard(state,step,isAuto,total);
}
function storyReview(s){return `<div class="storyBox"><label>Generated title</label><input id="reviewTitle" value="${esc(s.title||"")}"><label>Story review / edit before proceed</label><textarea id="reviewStory">${esc(s.story||"")}</textarea><small style="color:#8f98b4">You can edit the LLM output before continuing.</small></div>`}
function outputStep(state,step,total,isAuto){return cardHead("Output, Storage & Publishing","Choose output ratio, duration, storage and optional YouTube upload.",step,total)+`
 <div class="grid3"><div><label>Storage</label><select id="storage"><option value="download">Download</option><option value="huggingface">Hugging Face</option><option value="both">HF + Download</option></select></div><div><label>Video ratio</label><select id="ratio"><option value="9:16">9:16 · Shorts</option><option value="16:9">16:9 · Channel video</option></select></div><div><label>Duration (seconds)</label><input id="duration" type="number" min="10" max="300" value="${state.duration_seconds}"></div></div>
 <label class="optionRow"><div><b>Upload to YouTube</b><small>${isAuto?"Automation will upload after generation.":"Upload after this video completes."}</small></div><input id="youtube" type="checkbox" ${state.upload_to_youtube?"checked":""}></label>
 <label>YouTube visibility</label><select id="privacy"><option value="private">Private</option><option value="unlisted">Unlisted</option><option value="public">Public</option></select>`;
}
function sync(state){
 let g=id=>$("#"+id);
 if(g("llm"))state.llm_provider=g("llm").value;if(g("storyLang")){state.language=g("storyLang").value; const avail=(catalog.voices||[]).filter(v=>!v.language||v.language===state.language); if(avail.length && !avail.some(v=>v.id===state.voice_id)) state.voice_id=avail[0].id;}if(g("storyInput"))state.story=g("storyInput").value;
 if(g("reviewStory"))state.story=g("reviewStory").value;if(g("reviewTitle"))state.title=g("reviewTitle").value;
 if(g("lang")){state.language=g("lang").value; const avail=(catalog.voices||[]).filter(v=>!v.language||v.language===state.language); if(avail.length && !avail.some(v=>v.id===state.voice_id)) state.voice_id=avail[0].id;}if(g("vp"))state.voice_provider=g("vp").value;if(g("mood"))state.music_mood=g("mood").value;
 if(g("storage"))state.storage_mode=g("storage").value;if(g("ratio"))state.aspect_ratio=g("ratio").value;if(g("duration"))state.duration_seconds=+g("duration").value;
 if(g("youtube"))state.upload_to_youtube=g("youtube").checked;if(g("privacy"))state.youtube_privacy=g("privacy").value;
}
function bindWizard(state,step,isAuto,total){
 $$("[data-storymode]").forEach(b=>b.onclick=()=>{state.story_mode=b.dataset.storymode;state.story="";state.title="";wizard(state,step,isAuto)});
 $$("[data-select]").forEach(el=>el.onclick=e=>{if(e.target.dataset.play)return;let k=el.dataset.select,v=el.dataset.val;if(k==="voice")state.voice_id=v;if(k==="music")state.music_mode=v;if(k==="art")state.art_style=v;if(k==="video")state.video_provider=v;if(k==="caption")state.caption_style=v;wizard(state,step,isAuto)});
 $$("[data-effect]").forEach(el=>el.onclick=()=>{let x=el.dataset.effect;state.effects=state.effects.includes(x)?state.effects.filter(y=>y!==x):[...state.effects,x];wizard(state,step,isAuto)});
 $$("[data-play]").forEach(b=>b.onclick=e=>{e.stopPropagation();new Audio(`/api/voice-preview/${b.dataset.play}?language=${state.language}`).play()});
 if($("#buildStory"))$("#buildStory").onclick=async()=>{sync(state);if(!state.story.trim()){toast("Enter an idea first");return}let b=$("#buildStory");b.disabled=true;b.textContent="Generating…";try{let r=await api("/api/story",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({llm_provider:state.llm_provider,mode:"builder",user_input:state.story,language:state.language})});state.title=r.title;state.story=r.story;$("#storyReview").innerHTML=storyReview(state);toast("Story generated — review and edit it")}catch(e){toast(e.message)}finally{b.disabled=false;b.textContent="✦ Generate Story for Review"}};
 if($("#uploadMusic"))$("#uploadMusic").onclick=async()=>{let f=$("#musicFile").files[0];if(!f){toast("Choose a file");return}let fd=new FormData();fd.append("file",f);let r=await api("/api/upload/music",{method:"POST",body:fd});state.music_path=r.path;$("#musicPath").textContent=r.path;toast("Music uploaded")};
 $("#back").onclick=()=>{sync(state);if(isAuto)aStep--;else mStep--;wizard(state,isAuto?aStep:mStep,isAuto)};
 $("#next").onclick=async()=>{sync(state);
   if(step===0 && state.story_mode==="builder" && !state.title){toast("Generate and review the story first");return}
   if(step===0 && state.story_mode==="custom" && !state.story.trim()){toast("Enter your full story/prompt");return}
   if(step===0 && state.story_mode==="autonomous" && !state.story.trim()){toast("Enter an autonomous topic/direction");return}
   if(step<total-1){if(isAuto)aStep++;else mStep++;wizard(state,isAuto?aStep:mStep,isAuto);return}
   if(isAuto){await saveAutomation(state);return}
   $("#next").disabled=true;$("#next").textContent="Generating…";$("#result").textContent="Starting production pipeline…";
   try{let r=await api("/api/generate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({config:state})});$("#result").textContent=JSON.stringify(r,null,2);toast("Video generation completed")}catch(e){$("#result").textContent=e.message;toast("Generation failed")}finally{$("#next").disabled=false;$("#next").textContent="Generate Video ✦"}
 };
}
async function saveAutomation(state){
 let req={name:$("#schedName").value||"Automation",enabled:true,preset:$("#preset").value,local_time:$("#localTime").value,second_local_time:$("#secondTime").value,weekday:+$("#weekday").value,custom_cron:$("#cron").value||null,config:state};
 try{await api("/api/schedules",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(req)});toast("Automation scheduled");setPage("schedules")}catch(e){toast(e.message)}
}

async function schedulesPage(){
 let rows=await api("/api/schedules").catch(()=>[]);
 $("#page").innerHTML=`<div class="sectionTitle"><h3>Automations</h3><button class="primary" id="newAuto">+ New Automation</button></div>${rows.length?`<div class="scheduleGrid">${rows.map(r=>`<div class="glass scheduleCard"><span class="badge ${r.enabled?"":"wait"}">${r.enabled?"ACTIVE":"PAUSED"}</span><h4>${esc(r.name)}</h4><p>${r.preset.replaceAll("_"," ")} · ${r.local_time||""}</p><p>Last: ${r.last_run?String(r.last_run).replace("T"," ").slice(0,16):"Never"}<br>Status: ${esc(r.last_status||"never")}</p><div class="scheduleActions"><button class="secondary" data-run="${r.id}">Run now</button><button class="ghost" data-toggle="${r.id}" data-enabled="${r.enabled}">${r.enabled?"Pause":"Resume"}</button><button class="danger" data-del="${r.id}">Delete</button></div></div>`).join("")}</div>`:`<div class="glass empty">No automations yet.</div>`}`;
 $("#newAuto").onclick=()=>setPage("automation");
 $$("[data-run]").forEach(b=>b.onclick=async()=>{toast("Run started");await api(`/api/schedules/${b.dataset.run}/run`,{method:"POST"});toast("Run completed");schedulesPage()});
 $$("[data-toggle]").forEach(b=>b.onclick=async()=>{await api(`/api/schedules/${b.dataset.toggle}`,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({enabled:!Number(b.dataset.enabled)})});schedulesPage()});
 $$("[data-del]").forEach(b=>b.onclick=async()=>{if(confirm("Delete this automation?")){await api(`/api/schedules/${b.dataset.del}`,{method:"DELETE"});schedulesPage()}});
}
async function settingsPage(){
 let st=await api("/api/providers/status").catch(()=>({}));
 function badge(x){if(!x)return `<span class="badge fail">UNKNOWN</span>`;if(x.connected||x.enabled||x.status==="READY")return `<span class="badge">READY</span>`;if(x.configured)return `<span class="badge wait">${x.status==="NOT_IMPLEMENTED"?"NOT IMPLEMENTED":"CONFIGURED"}</span>`;return `<span class="badge fail">NOT CONFIGURED</span>`}
 function rows(group){return Object.entries(group||{}).map(([name,x])=>`<div class="statusLine"><div><b>${esc(name)}</b>${x?.reason?`<small style="display:block;color:#8f98b4;margin-top:4px;max-width:280px">${esc(x.reason)}</small>`:""}</div>${badge(x)}</div>`).join("")}
 let yt=st.youtube||{};
 $("#page").innerHTML=`<div class="settingsGrid">
 <section class="glass settingCard"><h3>LLM Providers</h3>${rows(st.llm)}</section>
 <section class="glass settingCard"><h3>Image Generation</h3>${rows(st.image)}</section>
 <section class="glass settingCard"><h3>Voice / TTS</h3>${rows(st.voice)}</section>
 <section class="glass settingCard"><h3>AI Video Router</h3>${rows(st.video)}</section>
 <section class="glass settingCard"><h3>Storage</h3>${rows(st.storage)}</section>
 <section class="glass settingCard"><h3>YouTube</h3><div class="statusLine"><b>Connection</b>${yt.connected?`<span class="badge">CONNECTED</span>`:`<span class="badge fail">NOT CONNECTED</span>`}</div>${yt.channel?`<div class="statusLine"><b>Channel</b><span>${esc(yt.channel.title||"Connected")}</span></div>`:`<a class="primary" href="/auth/youtube/start" style="display:inline-block;text-decoration:none;margin-top:12px">Connect YouTube</a>`}</section>
 </div>`;
}
async function render(){header();if(page==="home")await home();if(page==="manual")manualPage();if(page==="automation")automationPage();if(page==="schedules")await schedulesPage();if(page==="settings")await settingsPage()}
(async()=>{catalog=await api("/api/catalog");render()})();
