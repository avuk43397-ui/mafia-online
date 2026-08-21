import { FFmpeg } from 'https://cdn.jsdelivr.net/npm/@ffmpeg/ffmpeg@0.12.15/dist/esm/index.js';
import { fetchFile, toBlobURL } from 'https://cdn.jsdelivr.net/npm/@ffmpeg/util@0.12.2/dist/esm/index.js';

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];

const state = {
  scenes: [],
  current: 0,
  actor: 'A',
  stream: null,
  recorder: null,
  chunks: [],
  recordingStartedAt: 0,
  ffmpeg: null,
  ffmpegLoaded: false,
  busyExport: false,
  sourceName: '',
};

const videoExt = /\.(mp4|webm|mov|m4v|avi)$/i;
const textExt = /\.(txt|srt|vtt|json)$/i;

function toast(msg){
  const el = $('#toast'); el.textContent = msg; el.classList.add('show');
  clearTimeout(el._t); el._t = setTimeout(()=>el.classList.remove('show'), 2600);
}
function formatTime(sec){
  sec = Math.max(0, Number(sec)||0); const m = Math.floor(sec/60); const s = Math.floor(sec%60);
  return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
}
function sceneName(path){
  return path.split('/').pop().replace(/\.[^/.]+$/,'').replace(/[_-]+/g,' ').trim();
}
function slug(path){ return path.toLowerCase().replace(/\\/g,'/').replace(/\.[^/.]+$/,'').replace(/[^a-z0-9а-яё]+/gi,''); }
function mimeFor(name){
  const ext=name.toLowerCase().split('.').pop();
  return ({mp4:'video/mp4',webm:'video/webm',mov:'video/quicktime',m4v:'video/mp4',avi:'video/x-msvideo'})[ext] || 'video/mp4';
}
function parseSrt(text){
  const blocks=text.replace(/\r/g,'').split(/\n\s*\n/); const out=[];
  for(const block of blocks){
    const lines=block.split('\n').map(x=>x.trim()).filter(Boolean); if(lines.length<2) continue;
    const timeLine=lines.find(x=>x.includes('-->')); if(!timeLine) continue;
    const [a,b]=timeLine.split('-->').map(x=>x.trim());
    const t=s=>{const p=s.replace(',','.').split(':').map(Number); return p.length===3?p[0]*3600+p[1]*60+p[2]:p[0]*60+p[1]};
    out.push({start:t(a),end:t(b),text:lines.filter(x=>x!==timeLine && !/^\d+$/.test(x)).join(' ')});
  } return out;
}
function parseVtt(text){ return parseSrt(text.replace(/^WEBVTT[^\n]*\n/i,'')); }
function parseTextScript(text,name){
  const trimmed=text.trim();
  if(name.toLowerCase().endsWith('.json')){
    try{
      const j=JSON.parse(trimmed); const arr=Array.isArray(j)?j:(j.scenes||j.lines||j.dialogues||[]);
      if(Array.isArray(arr)) return arr.map((x,i)=>({start:Number(x.start??x.from??0),end:Number(x.end??x.to??0),text:String(x.text??x.line??x.dialogue??x.caption??x.name??'').trim()})).filter(x=>x.text);
    }catch(e){}
  }
  if(name.toLowerCase().endsWith('.srt')) return parseSrt(text);
  if(name.toLowerCase().endsWith('.vtt')) return parseVtt(text);
  return trimmed.split(/\n+/).map(x=>x.trim()).filter(Boolean).map(x=>({start:0,end:0,text:x.replace(/^\[[^\]]+\]\s*/,'')}));
}

async function filesToScenes(files){
  const videos=[], scripts=[];
  for(const f of files){
    const path=f.webkitRelativePath || f.name;
    if(videoExt.test(path)) videos.push({file:f,path});
    else if(textExt.test(path)) scripts.push({file:f,path});
  }
  videos.sort((a,b)=>a.path.localeCompare(b.path,undefined,{numeric:true,sensitivity:'base'}));
  scripts.sort((a,b)=>a.path.localeCompare(b.path,undefined,{numeric:true,sensitivity:'base'}));
  const scriptMap=new Map(scripts.map(x=>[slug(x.path),x]));
  const used=new Set(); const out=[];
  for(let i=0;i<videos.length;i++){
    const v=videos[i];
    let s=scriptMap.get(slug(v.path));
    if(!s){
      const vn=slug(v.path); s=scripts.find(x=>!used.has(x.path) && (vn.includes(slug(x.path)) || slug(x.path).includes(vn) || Math.abs(scripts.indexOf(x)-i)<=1));
    }
    if(s) used.add(s.path);
    let lines=[];
    if(s) lines=parseTextScript(await s.file.text(),s.path);
    if(!lines.length) lines=[{start:0,end:0,text:sceneName(v.path)}];
    const url=URL.createObjectURL(v.file);
    out.push({id:i+1,name:sceneName(v.path),path:v.path,file:v.file,url,duration:0,lines,takes:{A:[],B:[]},activeLine:0});
  }
  return out;
}

function setProjectReady(name){
  $('#projectStatus').textContent='Проект открыт'; $('#projectStatus').classList.add('ready');
  $('#projectName').textContent=name || 'Dub project';
  $('#uploadSection').classList.add('hidden'); $('#workspace').classList.remove('hidden');
  $('#sceneCount').textContent=state.scenes.length;
}
function renderScenes(){
  const el=$('#sceneList'); el.innerHTML='';
  state.scenes.forEach((s,i)=>{
    const done=s.takes.A.length+s.takes.B.length>0;
    const item=document.createElement('div'); item.className='scene-item'+(i===state.current?' active':'');
    item.innerHTML=`<div class="scene-num">${i+1}</div><div style="min-width:0"><div class="scene-title-mini">${escapeHtml(s.name)}</div><div class="scene-sub ${done?'done':''}">${done?'● дуб записан':formatTime(s.duration||0)}</div></div>`;
    item.onclick=()=>selectScene(i); el.appendChild(item);
  });
  updateProgress();
}
function escapeHtml(s){return String(s).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
function updateProgress(){
  const done=state.scenes.filter(s=>s.takes.A.length || s.takes.B.length).length; const p=state.scenes.length?Math.round(done/state.scenes.length*100):0;
  $('#progressBar').style.width=p+'%'; $('#progressText').textContent=p+'%';
  $('#exportBtn').disabled=state.scenes.length===0 || state.scenes.some(s=>!(s.takes.A.length || s.takes.B.length)) || state.busyExport;
}

async function selectScene(i){
  if(i<0||i>=state.scenes.length) return;
  stopRecording(); state.current=i; const s=state.scenes[i];
  const v=$('#video'); v.src=s.url; v.muted=!$('#soundBtn').classList.contains('active'); v.load();
  $('#videoPlaceholder').style.display='none'; $('#sceneTitle').textContent=s.name; $('#sceneMeta').textContent=`Сцена ${i+1} из ${state.scenes.length} · ${s.path}`;
  $('#scriptText').textContent=s.lines[state.currentLine||0]?.text || s.lines[0]?.text || 'Нет текста';
  state.currentLine=0; renderLinesForCurrent(); renderTakes(); renderScenes();
  $('#actorLabel').textContent='Диктор '+state.actor; $('#nextBtn').disabled=i===state.scenes.length-1; $('#prevBtn').disabled=i===0;
}
function renderLinesForCurrent(){
  const s=state.scenes[state.current]; const line=s.lines[state.currentLine||0];
  $('#scriptText').textContent=line?.text || 'Нет текста для этой сцены.';
}
function setActor(a){state.actor=a; $$('.actor').forEach(x=>x.classList.toggle('active',x.dataset.actor===a)); $('#actorLabel').textContent='Диктор '+a; renderTakes();}
function renderTakes(){
  const s=state.scenes[state.current]; const list=$('#takesList'); list.innerHTML=''; const arr=s.takes[state.actor];
  $('#takeInfo').textContent=arr.length?`${arr.length} дуб${arr.length===1?'ль':'ля'} для диктора ${state.actor}.`:'Записей пока нет.';
  arr.forEach((take,idx)=>{
    const row=document.createElement('div'); row.className='take-row'; row.innerHTML=`<div class="take-left"><div class="take-player">${idx+1}</div><div>Дубль ${idx+1}<div style="color:#69717b;margin-top:2px">${formatTime(take.duration)} · ${take.blob.type||'audio'}</div></div></div><div class="take-actions"><button data-act="play">▶</button><button data-act="use">Использовать</button><button data-act="del">✕</button></div>`;
    row.querySelector('[data-act=play]').onclick=()=>{const a=new Audio(URL.createObjectURL(take.blob)); a.play()};
    row.querySelector('[data-act=use]').onclick=()=>{arr.splice(0,0,arr.splice(idx,1)[0]); renderTakes(); renderScenes(); toast('Основным сделан этот дубль');};
    row.querySelector('[data-act=del]').onclick=()=>{arr.splice(idx,1); renderTakes(); renderScenes();}; list.appendChild(row);
  });
}

async function getMic(){
  if(state.stream) return state.stream;
  state.stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true,autoGainControl:true}});
  return state.stream;
}
async function startRecording(){
  try{
    await getMic();
    const mime=['audio/webm;codecs=opus','audio/webm','audio/mp4'].find(x=>MediaRecorder.isTypeSupported(x)) || '';
    state.chunks=[]; state.recorder=new MediaRecorder(state.stream,mime?{mimeType:mime}:undefined); state.recordingStartedAt=performance.now();
    state.recorder.ondataavailable=e=>{if(e.data.size) state.chunks.push(e.data)};
    state.recorder.onstop=()=>{
      const blob=new Blob(state.chunks,{type:state.recorder.mimeType||'audio/webm'}); const duration=(performance.now()-state.recordingStartedAt)/1000;
      const s=state.scenes[state.current]; s.takes[state.actor].unshift({blob,duration,actor:state.actor}); renderTakes(); renderScenes(); $('#recordBtn').classList.remove('recording'); $('#recordBtnText').textContent='Начать запись'; $('#recordBtn').disabled=false; $('#stopBtn').disabled=true; toast('Дубль сохранён');
    };
    state.recorder.start(200);
    $('#recordBtn').classList.add('recording'); $('#recordBtnText').textContent='Идёт запись…'; $('#recordBtn').disabled=true; $('#stopBtn').disabled=false;
    // Start the scene automatically for timing
    const v=$('#video'); v.currentTime=0; await v.play().catch(()=>{});
  }catch(e){ toast('Не удалось открыть микрофон: '+(e.message||e)); }
}
function stopRecording(){ if(state.recorder && state.recorder.state!=='inactive') state.recorder.stop(); $('#stopBtn').disabled=true; }

async function loadZip(file){
  try{
    toast('Распаковываем ZIP…'); const zip=await JSZip.loadAsync(file); const files=[];
    for(const [path,entry] of Object.entries(zip.files)){
      if(entry.dir) continue;
      const blob=await entry.async('blob'); const f=new File([blob],path.split('/').pop(),{type:blob.type||mimeFor(path)}); Object.defineProperty(f,'webkitRelativePath',{value:path}); files.push(f);
    }
    await openProject(files,file.name.replace(/\.zip$/i,''));
  }catch(e){ console.error(e); toast('Ошибка ZIP: '+e.message); }
}
async function openProject(files,name){
  const scenes=await filesToScenes(files); if(!scenes.length){toast('В архиве не найдено видео.'); return;}
  state.scenes.forEach(s=>URL.revokeObjectURL(s.url)); state.scenes=scenes; state.current=0; state.sourceName=name;
  setProjectReady(name); renderScenes(); await selectScene(0); toast(`Импортировано сцен: ${scenes.length}`);
}

async function ensureFFmpeg(){
  if(state.ffmpegLoaded) return state.ffmpeg;
  $('#exportStatus').textContent='Загружаем модуль сборки видео…';
  const ff=new FFmpeg();
  const base='https://cdn.jsdelivr.net/npm/@ffmpeg/core@0.12.10/dist/esm';
  await ff.load({
    coreURL: await toBlobURL(`${base}/ffmpeg-core.js`,'text/javascript'),
    wasmURL: await toBlobURL(`${base}/ffmpeg-core.wasm`,'application/wasm')
  });
  state.ffmpeg=ff; state.ffmpegLoaded=true; return ff;
}
function sanitize(s){return s.toLowerCase().replace(/[^a-z0-9]+/g,'_').slice(0,60)||'scene'}

async function exportMp4(){
  if(state.busyExport) return; state.busyExport=true; updateProgress();
  try{
    const ff=await ensureFFmpeg(); const used=[];
    for(let i=0;i<state.scenes.length;i++){
      const s=state.scenes[i]; const take=(s.takes.A[0]||s.takes.B[0]); if(!take) throw new Error(`Нет дубля для сцены ${i+1}`);
      const vName=`v${i}.mp4`; const aExt=(take.blob.type||'').includes('mp4')?'m4a':'webm'; const aName=`a${i}.${aExt}`; const oName=`o${i}.mp4`;
      $('#exportStatus').textContent=`Собираем сцену ${i+1}/${state.scenes.length}…`;
      await ff.writeFile(vName,await fetchFile(s.file)); await ff.writeFile(aName,await fetchFile(take.blob));
      // Replace original sound with the recorded dub. Shorter/longer takes are fit to the video length.
      await ff.exec(['-i',vName,'-i',aName,'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','veryfast','-crf','24','-c:a','aac','-b:a','160k','-af','apad','-t',String(Math.max(0.1, s.duration || 0.1)),'-movflags','+faststart',oName]);
      used.push(oName);
    }
    $('#exportStatus').textContent='Склеиваем сцены…';
    let list='';
    for(let i=0;i<used.length;i++){const line=`file '${used[i]}'\n`; const n=`list${i}.txt`; await ff.writeFile(n,new TextEncoder().encode(line)); list+=line;}
    // concat demuxer needs one list file
    await ff.writeFile('concat.txt',new TextEncoder().encode(list));
    await ff.exec(['-f','concat','-safe','0','-i','concat.txt','-c','copy','dub-result.mp4']);
    const data=await ff.readFile('dub-result.mp4');
    const blob=new Blob([data.buffer],{type:'video/mp4'}); const url=URL.createObjectURL(blob);
    const a=document.createElement('a'); a.href=url; a.download=(state.sourceName||'dub-project')+'-dub.mp4'; a.click();
    setTimeout(()=>URL.revokeObjectURL(url),10000); $('#exportStatus').textContent='Готово — MP4 скачан.'; toast('Готовое видео собрано');
  }catch(e){ console.error(e); $('#exportStatus').textContent='Ошибка: '+e.message; toast('Не удалось собрать MP4'); }
  finally{state.busyExport=false; updateProgress();}
}

// UI events
$('#zipInput').addEventListener('change',e=>e.target.files[0]&&loadZip(e.target.files[0]));
$('#filesInput').addEventListener('change',e=>e.target.files.length&&openProject([...e.target.files],'folder-project'));
const dz=$('#dropzone'); ['dragenter','dragover'].forEach(ev=>dz.addEventListener(ev,e=>{e.preventDefault();dz.classList.add('drag')})); ['dragleave','drop'].forEach(ev=>dz.addEventListener(ev,e=>{e.preventDefault();dz.classList.remove('drag')}));
dz.addEventListener('drop',e=>{const f=e.dataTransfer.files[0]; if(f) loadZip(f)});
$$('.actor').forEach(b=>b.onclick=()=>setActor(b.dataset.actor));
$('#playBtn').onclick=()=>{const v=$('#video'); v.paused?v.play():v.pause()};
$('#video').addEventListener('loadedmetadata',()=>{state.scenes[state.current].duration=$('#video').duration||0;renderScenes();updateTimecode()});
$('#video').addEventListener('timeupdate',updateTimecode);
$('#video').addEventListener('ended',()=>{$('#playBtn').textContent='▶'});
$('#video').addEventListener('play',()=>$('#playBtn').textContent='❚❚'); $('#video').addEventListener('pause',()=>$('#playBtn').textContent='▶');
function updateTimecode(){const v=$('#video'); $('#timecode').textContent=`${formatTime(v.currentTime)} / ${formatTime(v.duration)}`}
$('#soundBtn').onclick=()=>{const v=$('#video'); v.muted=!v.muted; $('#soundBtn').classList.toggle('active',!v.muted); $('#soundBtnText').textContent=v.muted?'Не слышать оригинал':'Слышать оригинал'; $('#soundLabel').textContent=v.muted?'Оригинал выключен':'Звук включён'};
$('#micBtn').onclick=async()=>{try{await getMic();toast('Микрофон готов')}catch(e){toast('Микрофон недоступен')}};
$('#recordBtn').onclick=startRecording; $('#stopBtn').onclick=stopRecording;
$('#nextBtn').onclick=()=>selectScene(state.current+1); $('#prevBtn').onclick=()=>selectScene(state.current-1);
$('#clearTakeBtn').onclick=()=>{state.scenes[state.current].takes[state.actor]=[];renderTakes();renderScenes()};
$('#exportBtn').onclick=exportMp4;
$('#resetProjectBtn').onclick=()=>{if(!confirm('Сбросить текущий проект?'))return;location.reload()};

window.addEventListener('beforeunload',()=>{state.scenes.forEach(s=>URL.revokeObjectURL(s.url));state.stream?.getTracks().forEach(t=>t.stop())});
