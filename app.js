import { FFmpeg } from 'https://cdn.jsdelivr.net/npm/@ffmpeg/ffmpeg@0.12.15/dist/esm/index.js';
import { fetchFile, toBlobURL } from 'https://cdn.jsdelivr.net/npm/@ffmpeg/util@0.12.2/dist/esm/index.js';

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];

const state = {
  scenes: [],
  current: 0,
  currentLine: 0,
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

function toast(msg) {
  const el = $('#toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove('show'), 2800);
}

function formatTime(sec) {
  sec = Math.max(0, Number(sec) || 0);
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60);
  return h > 0 ? `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}` : `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function sceneName(path) {
  return path.split('/').pop().replace(/\.[^/.]+$/, '').replace(/[_-]+/g, ' ').trim() || 'Сцена';
}

function normalizePath(path) {
  return String(path).replace(/\\/g, '/').toLowerCase();
}

function slug(path) {
  return normalizePath(path).replace(/\.[^/.]+$/, '').replace(/[^a-z0-9а-яё]+/gi, '');
}

function mimeFor(name) {
  const ext = String(name).toLowerCase().split('.').pop();
  return ({ mp4: 'video/mp4', webm: 'video/webm', mov: 'video/quicktime', m4v: 'video/mp4', avi: 'video/x-msvideo' })[ext] || 'application/octet-stream';
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function parseTimestamp(value) {
  const raw = String(value).trim().replace(',', '.');
  const p = raw.split(':').map(Number);
  if (p.some(Number.isNaN)) return 0;
  if (p.length === 3) return p[0] * 3600 + p[1] * 60 + p[2];
  if (p.length === 2) return p[0] * 60 + p[1];
  return p[0] || 0;
}

function parseSrt(text) {
  const blocks = text.replace(/\r/g, '').split(/\n\s*\n/);
  const out = [];
  for (const block of blocks) {
    const lines = block.split('\n').map(x => x.trim()).filter(Boolean);
    const idx = lines.findIndex(x => x.includes('-->'));
    if (idx < 0) continue;
    const [a, b] = lines[idx].split('-->').map(x => x.trim());
    const cleanText = lines.slice(idx + 1).filter(x => !/^\d+$/.test(x)).join(' ');
    if (!cleanText) continue;
    out.push({ start: parseTimestamp(a), end: parseTimestamp(b), text: cleanText });
  }
  return out;
}

function parseVtt(text) {
  return parseSrt(text.replace(/^WEBVTT[^\n]*\n/i, ''));
}

function parseJsonScript(text) {
  const j = JSON.parse(text);
  const arr = Array.isArray(j) ? j : (j.scenes || j.lines || j.dialogues || j.cues || []);
  if (!Array.isArray(arr)) return [];
  return arr.map((x) => ({
    start: Number(x.start ?? x.from ?? 0),
    end: Number(x.end ?? x.to ?? 0),
    text: String(x.text ?? x.line ?? x.dialogue ?? x.caption ?? '').trim(),
  })).filter(x => x.text);
}

function parseTextScript(text, name) {
  const lower = name.toLowerCase();
  if (lower.endsWith('.json')) {
    try { return parseJsonScript(text); } catch (_) { return []; }
  }
  if (lower.endsWith('.srt')) return parseSrt(text);
  if (lower.endsWith('.vtt')) return parseVtt(text);
  return text.trim().split(/\n+/).map(x => x.trim()).filter(Boolean).map(textLine => ({ start: 0, end: 0, text: textLine.replace(/^\[[^\]]+\]\s*/, '') }));
}

async function filesToScenes(files) {
  const videos = [];
  const scripts = [];
  for (const file of files) {
    const path = file.webkitRelativePath || file.name;
    if (videoExt.test(path)) videos.push({ file, path });
    else if (textExt.test(path)) scripts.push({ file, path });
  }
  videos.sort((a, b) => a.path.localeCompare(b.path, undefined, { numeric: true, sensitivity: 'base' }));
  scripts.sort((a, b) => a.path.localeCompare(b.path, undefined, { numeric: true, sensitivity: 'base' }));

  const exact = new Map(scripts.map(x => [slug(x.path), x]));
  const used = new Set();
  const scenes = [];

  for (let i = 0; i < videos.length; i++) {
    const v = videos[i];
    let script = exact.get(slug(v.path));
    if (!script) {
      const videoSlug = slug(v.path);
      script = scripts.find(x => !used.has(x.path) && (
        videoSlug.includes(slug(x.path)) ||
        slug(x.path).includes(videoSlug) ||
        Math.abs(scripts.indexOf(x) - i) <= 1
      ));
    }
    if (script) used.add(script.path);

    let lines = script ? parseTextScript(await script.file.text(), script.path) : [];
    if (!lines.length) lines = [{ start: 0, end: 0, text: sceneName(v.path) }];

    scenes.push({
      id: i + 1,
      name: sceneName(v.path),
      path: v.path,
      file: v.file,
      url: URL.createObjectURL(v.file),
      duration: 0,
      lines,
      currentLine: 0,
      takes: { A: [], B: [] },
    });
  }
  return scenes;
}

function setProjectReady(name) {
  $('#projectStatus').textContent = 'Проект открыт';
  $('#projectStatus').classList.add('ready');
  $('#projectName').textContent = name || 'Dub project';
  $('#uploadSection').classList.add('hidden');
  $('#workspace').classList.remove('hidden');
  $('#sceneCount').textContent = state.scenes.length;
}

function sceneDone(scene) {
  return scene.takes.A.length > 0 || scene.takes.B.length > 0;
}

function updateProgress() {
  const done = state.scenes.filter(sceneDone).length;
  const percent = state.scenes.length ? Math.round(done / state.scenes.length * 100) : 0;
  $('#progressBar').style.width = `${percent}%`;
  $('#progressText').textContent = `${percent}%`;
  $('#exportBtn').disabled = state.scenes.length === 0 || state.scenes.some(scene => !sceneDone(scene)) || state.busyExport;
}

function renderScenes() {
  const list = $('#sceneList');
  list.innerHTML = '';
  state.scenes.forEach((scene, i) => {
    const item = document.createElement('div');
    item.className = `scene-item${i === state.current ? ' active' : ''}`;
    item.innerHTML = `<div class="scene-num">${i + 1}</div><div style="min-width:0"><div class="scene-title-mini">${escapeHtml(scene.name)}</div><div class="scene-sub ${sceneDone(scene) ? 'done' : ''}">${sceneDone(scene) ? '● дуб записан' : formatTime(scene.duration || 0)}</div></div>`;
    item.onclick = () => selectScene(i);
    list.appendChild(item);
  });
  updateProgress();
}

function renderLine() {
  const scene = state.scenes[state.current];
  const total = scene?.lines.length || 0;
  const index = Math.min(scene?.currentLine ?? 0, Math.max(0, total - 1));
  if (scene) scene.currentLine = index;
  state.currentLine = index;
  $('#scriptText').textContent = scene?.lines[index]?.text || 'Нет текста для этой сцены.';
  $('#lineLabel').textContent = total ? `Строка ${index + 1} / ${total}` : 'Нет строк';
  $('#prevLineBtn').disabled = index <= 0;
  $('#nextLineBtn').disabled = index >= total - 1;
}

function renderTakes() {
  const scene = state.scenes[state.current];
  if (!scene) return;
  const arr = scene.takes[state.actor];
  const list = $('#takesList');
  list.innerHTML = '';
  $('#takeInfo').textContent = arr.length ? `${arr.length} дубль${arr.length === 1 ? '' : arr.length < 5 ? 'я' : 'ей'} для диктора ${state.actor}.` : 'Записей пока нет.';
  arr.forEach((take, idx) => {
    const row = document.createElement('div');
    row.className = 'take-row';
    row.innerHTML = `<div class="take-left"><div class="take-player">${idx + 1}</div><div>Дубль ${idx + 1}<div style="color:#69717b;margin-top:2px">${formatTime(take.duration)} · ${escapeHtml(take.blob.type || 'audio')}</div></div></div><div class="take-actions"><button data-act="play">▶</button><button data-act="use">Использовать</button><button data-act="del">✕</button></div>`;
    row.querySelector('[data-act="play"]').onclick = () => {
      const url = URL.createObjectURL(take.blob);
      const audio = new Audio(url);
      audio.onended = () => URL.revokeObjectURL(url);
      audio.play().catch(() => toast('Не удалось воспроизвести дубль'));
    };
    row.querySelector('[data-act="use"]').onclick = () => {
      const chosen = arr.splice(idx, 1)[0];
      arr.unshift(chosen);
      renderTakes();
      renderScenes();
      toast('Этот дубль выбран основным');
    };
    row.querySelector('[data-act="del"]').onclick = () => {
      arr.splice(idx, 1);
      renderTakes();
      renderScenes();
    };
    list.appendChild(row);
  });
}

function applySoundState() {
  const video = $('#video');
  const originalEnabled = !video.muted;
  $('#soundBtn').classList.toggle('active', originalEnabled);
  $('#soundBtnText').textContent = originalEnabled ? 'Слышать оригинал' : 'Не слышать оригинал';
  $('#soundLabel').textContent = originalEnabled ? 'Звук включён' : 'Оригинал выключен';
}

async function getMic() {
  if (!window.isSecureContext && location.hostname !== 'localhost') throw new Error('Микрофон требует HTTPS. Render уже работает через HTTPS.');
  if (!navigator.mediaDevices?.getUserMedia) throw new Error('Браузер не поддерживает запись микрофона.');
  if (state.stream) return state.stream;
  state.stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } });
  return state.stream;
}

function recorderMimeType() {
  const types = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4'];
  return types.find(type => window.MediaRecorder?.isTypeSupported?.(type)) || '';
}

async function startRecording() {
  if (state.recorder && state.recorder.state !== 'inactive') return;
  try {
    await getMic();
    if (!window.MediaRecorder) throw new Error('MediaRecorder отсутствует в этом браузере.');
    const type = recorderMimeType();
    state.chunks = [];
    state.recorder = new MediaRecorder(state.stream, type ? { mimeType: type } : undefined);
    const sceneIndexAtStart = state.current;
    const actorAtStart = state.actor;
    const video = $('#video');
    video.currentTime = 0;
    state.recordingStartedAt = performance.now();

    state.recorder.ondataavailable = event => {
      if (event.data.size) state.chunks.push(event.data);
    };

    state.recorder.onstop = async () => {
      const blob = new Blob(state.chunks, { type: state.recorder.mimeType || 'audio/webm' });
      const duration = Math.max(0, (performance.now() - state.recordingStartedAt) / 1000);
      const scene = state.scenes[sceneIndexAtStart];
      if (scene) scene.takes[actorAtStart].unshift({ blob, duration, actor: actorAtStart, createdAt: Date.now() });
      state.recorder = null;
      $('#recordBtn').classList.remove('recording');
      $('#recordBtnText').textContent = 'Начать запись';
      $('#recordBtn').disabled = false;
      $('#stopBtn').disabled = true;
      renderTakes();
      renderScenes();
      toast('Дубль сохранён');

      if ($('#autoNext').checked && sceneIndexAtStart < state.scenes.length - 1) {
        await selectScene(sceneIndexAtStart + 1);
      }
    };

    state.recorder.start(200);
    $('#recordBtn').classList.add('recording');
    $('#recordBtnText').textContent = 'Идёт запись…';
    $('#recordBtn').disabled = true;
    $('#stopBtn').disabled = false;
    await video.play().catch(() => toast('Нажмите ▶, чтобы запустить видео, затем продолжите запись.'));
  } catch (error) {
    toast(`Не удалось открыть микрофон: ${error.message || error}`);
  }
}

function stopRecording() {
  if (state.recorder && state.recorder.state !== 'inactive') state.recorder.stop();
  $('#stopBtn').disabled = true;
}

async function selectScene(index) {
  if (index < 0 || index >= state.scenes.length) return;
  if (state.recorder && state.recorder.state !== 'inactive') stopRecording();
  state.current = index;
  state.currentLine = 0;
  const scene = state.scenes[index];
  const video = $('#video');
  video.src = scene.url;
  video.load();
  video.muted = false;
  $('#videoPlaceholder').style.display = 'none';
  $('#sceneTitle').textContent = scene.name;
  $('#sceneMeta').textContent = `Сцена ${index + 1} из ${state.scenes.length} · ${scene.path}`;
  $('#actorLabel').textContent = `Диктор ${state.actor}`;
  $('#nextBtn').disabled = index >= state.scenes.length - 1;
  $('#prevBtn').disabled = index <= 0;
  applySoundState();
  renderLine();
  renderTakes();
  renderScenes();

  await waitForMetadata(video).then(() => {
    scene.duration = Number.isFinite(video.duration) ? video.duration : 0;
    updateTimecode();
    renderScenes();
  }).catch(() => {});
}

function waitForMetadata(video) {
  if (video.readyState >= 1 && Number.isFinite(video.duration)) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const onLoad = () => { cleanup(); resolve(); };
    const onError = () => { cleanup(); reject(video.error || new Error('Не удалось прочитать видео.')); };
    const cleanup = () => { video.removeEventListener('loadedmetadata', onLoad); video.removeEventListener('error', onError); };
    video.addEventListener('loadedmetadata', onLoad, { once: true });
    video.addEventListener('error', onError, { once: true });
  });
}

async function loadZip(file) {
  try {
    if (!window.JSZip) throw new Error('JSZip не загрузился. Проверь интернет-доступ к CDN.');
    toast('Распаковываем ZIP…');
    const zip = await window.JSZip.loadAsync(file);
    const files = [];
    for (const [path, entry] of Object.entries(zip.files)) {
      if (entry.dir) continue;
      const blob = await entry.async('blob');
      const name = path.split('/').pop() || 'file';
      const f = new File([blob], name, { type: blob.type || mimeFor(path) });
      Object.defineProperty(f, 'webkitRelativePath', { value: path });
      files.push(f);
    }
    await openProject(files, file.name.replace(/\.zip$/i, ''));
  } catch (error) {
    console.error(error);
    toast(`Ошибка ZIP: ${error.message || error}`);
  }
}

async function openProject(files, name) {
  const scenes = await filesToScenes(files);
  if (!scenes.length) {
    toast('В архиве/папке не найдено видео.');
    return;
  }
  state.scenes.forEach(scene => URL.revokeObjectURL(scene.url));
  state.scenes = scenes;
  state.current = 0;
  state.currentLine = 0;
  state.sourceName = name;
  setProjectReady(name);
  renderScenes();
  await selectScene(0);
  toast(`Импортировано сцен: ${scenes.length}`);
}

async function ensureFFmpeg() {
  if (state.ffmpegLoaded) return state.ffmpeg;
  $('#exportStatus').textContent = 'Загружаем модуль сборки видео…';
  const ff = new FFmpeg();
  const base = 'https://cdn.jsdelivr.net/npm/@ffmpeg/core@0.12.10/dist/esm';
  await ff.load({
    coreURL: await toBlobURL(`${base}/ffmpeg-core.js`, 'text/javascript'),
    wasmURL: await toBlobURL(`${base}/ffmpeg-core.wasm`, 'application/wasm'),
  });
  state.ffmpeg = ff;
  state.ffmpegLoaded = true;
  return ff;
}

function safeBaseName(value) {
  return String(value).replace(/[^a-zA-Z0-9а-яА-ЯёЁ_-]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 80) || 'dub-project';
}

async function ensureDuration(scene) {
  if (scene.duration > 0) return scene.duration;
  const probe = document.createElement('video');
  probe.preload = 'metadata';
  probe.muted = true;
  const url = URL.createObjectURL(scene.file);
  try {
    probe.src = url;
    await waitForMetadata(probe);
    scene.duration = Number.isFinite(probe.duration) ? probe.duration : 0;
  } finally {
    probe.removeAttribute('src');
    URL.revokeObjectURL(url);
  }
  return scene.duration;
}

async function writeUniqueFile(ff, name, data) {
  await ff.writeFile(name, data);
}

async function exportMp4() {
  if (state.busyExport) return;
  state.busyExport = true;
  updateProgress();
  try {
    const ff = await ensureFFmpeg();
    const partNames = [];

    for (let i = 0; i < state.scenes.length; i++) {
      const scene = state.scenes[i];
      const take = scene.takes.A[0] || scene.takes.B[0];
      if (!take) throw new Error(`Нет готового дубля для сцены ${i + 1}`);
      const duration = await ensureDuration(scene);
      if (!duration) throw new Error(`Не удалось определить длительность сцены ${i + 1}`);

      const videoName = `input_${i}`;
      const audioName = `audio_${i}.${(take.blob.type || '').includes('mp4') ? 'm4a' : 'webm'}`;
      const outputName = `part_${i}.mp4`;
      $('#exportStatus').textContent = `Собираем сцену ${i + 1}/${state.scenes.length}…`;

      await writeUniqueFile(ff, videoName, await fetchFile(scene.file));
      await writeUniqueFile(ff, audioName, await fetchFile(take.blob));

      const args = [
        '-i', videoName,
        '-i', audioName,
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-crf', '24',
        '-c:a', 'aac',
        '-b:a', '160k',
        '-af', 'apad',
        '-t', String(duration),
        '-movflags', '+faststart',
        outputName,
      ];
      await ff.exec(args);
      partNames.push(outputName);
    }

    $('#exportStatus').textContent = 'Склеиваем сцены…';
    const concat = partNames.map(name => `file '${name}'`).join('\n') + '\n';
    await ff.writeFile('concat.txt', new TextEncoder().encode(concat));
    await ff.exec(['-f', 'concat', '-safe', '0', '-i', 'concat.txt', '-c', 'copy', '-movflags', '+faststart', 'dub-result.mp4']);

    const data = await ff.readFile('dub-result.mp4');
    const blob = new Blob([data], { type: 'video/mp4' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${safeBaseName(state.sourceName || 'dub-project')}-dub.mp4`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 15_000);
    $('#exportStatus').textContent = 'Готово — MP4 скачан.';
    toast('Готовое видео собрано');
  } catch (error) {
    console.error(error);
    $('#exportStatus').textContent = `Ошибка: ${error.message || error}`;
    toast('Не удалось собрать MP4. Открой консоль браузера для подробностей.');
  } finally {
    state.busyExport = false;
    updateProgress();
  }
}

function updateTimecode() {
  const video = $('#video');
  $('#timecode').textContent = `${formatTime(video.currentTime)} / ${formatTime(video.duration)}`;
}

$('#zipInput').addEventListener('change', e => e.target.files[0] && loadZip(e.target.files[0]));
$('#filesInput').addEventListener('change', e => e.target.files.length && openProject([...e.target.files], 'folder-project'));

const dz = $('#dropzone');
['dragenter', 'dragover'].forEach(event => dz.addEventListener(event, e => { e.preventDefault(); dz.classList.add('drag'); }));
['dragleave', 'drop'].forEach(event => dz.addEventListener(event, e => { e.preventDefault(); dz.classList.remove('drag'); }));
dz.addEventListener('drop', e => { const file = e.dataTransfer.files[0]; if (file) loadZip(file); });

$$('.actor').forEach(button => button.onclick = () => {
  state.actor = button.dataset.actor;
  $$('.actor').forEach(el => el.classList.toggle('active', el.dataset.actor === state.actor));
  $('#actorLabel').textContent = `Диктор ${state.actor}`;
  renderTakes();
});

$('#playBtn').onclick = () => { const video = $('#video'); video.paused ? video.play() : video.pause(); };
$('#video').addEventListener('loadedmetadata', () => {
  const scene = state.scenes[state.current];
  if (scene) scene.duration = Number.isFinite($('#video').duration) ? $('#video').duration : 0;
  updateTimecode();
  renderScenes();
});
$('#video').addEventListener('timeupdate', updateTimecode);
$('#video').addEventListener('ended', () => { $('#playBtn').textContent = '▶'; });
$('#video').addEventListener('play', () => { $('#playBtn').textContent = '❚❚'; });
$('#video').addEventListener('pause', () => { $('#playBtn').textContent = '▶'; });

$('#soundBtn').onclick = () => { const video = $('#video'); video.muted = !video.muted; applySoundState(); };
$('#micBtn').onclick = async () => { try { await getMic(); toast('Микрофон готов'); } catch (error) { toast(`Микрофон недоступен: ${error.message || error}`); } };
$('#recordBtn').onclick = startRecording;
$('#stopBtn').onclick = stopRecording;
$('#nextBtn').onclick = () => selectScene(state.current + 1);
$('#prevBtn').onclick = () => selectScene(state.current - 1);
$('#prevLineBtn').onclick = () => { const scene = state.scenes[state.current]; if (!scene) return; scene.currentLine = Math.max(0, scene.currentLine - 1); renderLine(); };
$('#nextLineBtn').onclick = () => { const scene = state.scenes[state.current]; if (!scene) return; scene.currentLine = Math.min(scene.lines.length - 1, scene.currentLine + 1); renderLine(); };
$('#clearTakeBtn').onclick = () => { const scene = state.scenes[state.current]; if (!scene) return; scene.takes[state.actor] = []; renderTakes(); renderScenes(); };
$('#exportBtn').onclick = exportMp4;
$('#resetProjectBtn').onclick = () => { if (confirm('Сбросить текущий проект?')) location.reload(); };

window.addEventListener('beforeunload', () => {
  state.scenes.forEach(scene => URL.revokeObjectURL(scene.url));
  state.stream?.getTracks().forEach(track => track.stop());
});
