import asyncio
import os
import random
import re
import string
from contextlib import suppress

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI(title="Mafia Online")
rooms = {}

LOBBY = "ЛОББИ"
NIGHT = "🌙 НОЧЬ"
DAY = "☀️ ДЕНЬ"
VOTE = "🗳️ ГОЛОСОВАНИЕ"
WIN = "🏆 ИГРА ОКОНЧЕНА"

NIGHT_SECONDS = 20
DAY_SECONDS = 30
VOTE_SECONDS = 35
MAX_PLAYERS = 12

ROLE_INFO = {
    "Мафия": ("🔴", "Ночью вместе с мафией выбирает жертву."),
    "Дон": ("👑", "Глава мафии. Ночью участвует в выборе жертвы."),
    "Доктор": ("🩺", "Ночью спасает одного игрока от убийства."),
    "Шериф": ("🔎", "Один раз за игру проверяет, является ли игрок мафией."),
    "Телохранитель": ("🛡️", "Ночью защищает одного игрока."),
    "Маньяк": ("🔪", "Ночью убивает. Побеждает один."),
    "Детектив": ("🕵️", "Ночью узнаёт точную роль игрока."),
    "Мирный": ("🟢", "Днём обсуждает и голосует."),
}

COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


HTML = r'''
<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>Mafia Online</title>
<style>
:root{--bg:#08070d;--panel:#12101a;--panel2:#181522;--line:#2d2739;--text:#f5f2fa;--muted:#9f98ad;--accent:#9b5cff;--accent2:#6d35d7;--danger:#ff4d67;--good:#43e59a;--gold:#ffc857;--shadow:0 18px 55px #0008}
*{box-sizing:border-box}html,body{margin:0;min-height:100%;font-family:Inter,Segoe UI,Arial,sans-serif;background:radial-gradient(circle at 20% 0%,#24123b 0,#0b0910 35%,#050509 100%);color:var(--text)}
button,input,select{font:inherit}button{cursor:pointer}.app{max-width:1250px;margin:auto;padding:18px}.top{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.brand{font-weight:900;font-size:22px;letter-spacing:.5px;margin-right:auto}.pill{background:#15111e;border:1px solid var(--line);padding:9px 13px;border-radius:999px;color:#d9d1e8}.timer{min-width:78px;text-align:center;font-size:24px;font-weight:900;color:var(--gold)}
.btn{border:1px solid var(--line);background:#17131f;color:#fff;padding:10px 14px;border-radius:12px;transition:.18s;box-shadow:0 5px 15px #0003}.btn:hover{transform:translateY(-1px);background:#221a30}.btn:disabled{opacity:.4;cursor:not-allowed;transform:none}.accent{background:linear-gradient(135deg,var(--accent),var(--accent2));border-color:#aa7cff}.danger{border-color:#5b2733;background:#27121a}.ghost{background:transparent}.notice{margin-top:14px;padding:14px 16px;border:1px solid #3a2c4d;border-radius:16px;background:linear-gradient(135deg,#1d142b,#120e18);box-shadow:var(--shadow)}
.layout{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:16px;margin-top:16px}.card{background:linear-gradient(180deg,#14111b,#0f0d14);border:1px solid var(--line);border-radius:20px;padding:18px;box-shadow:var(--shadow)}.card h2,.card h3{margin:0 0 13px}.section{margin-top:18px}.players{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.player{display:flex;align-items:center;gap:10px;min-width:0;padding:10px;border:1px solid #292333;border-radius:14px;background:#17131f}.player.dead{opacity:.42;filter:grayscale(.7)}.avatar{width:43px;height:43px;flex:0 0 43px;border-radius:50%;object-fit:cover;background:#30243d;border:2px solid #49395b}.avatarFallback{display:grid;place-items:center;font-size:19px}.pname{font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.meta{font-size:12px;color:var(--muted);margin-top:3px}.hostMark{color:var(--gold)}
.roleBox{padding:16px;border:1px solid #342747;border-radius:16px;background:radial-gradient(circle at 80% 10%,#2c164c,#17111f 55%)}.roleIcon{font-size:42px}.roleName{font-size:25px;font-weight:900;margin-top:4px}.roleDesc{color:#b9b0c7;line-height:1.45;margin-top:6px}.select{width:100%;border:1px solid var(--line);background:#0c0a10;color:#fff;padding:12px;border-radius:12px;outline:none}.actions{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}.full{grid-column:1/-1}.actionHint{font-size:12px;color:var(--muted);margin-top:8px;min-height:17px}.log{height:300px;overflow:auto;background:#08070b;border:1px solid #201b29;border-radius:14px;padding:12px;white-space:pre-wrap;line-height:1.5;font-size:13px}.chat{height:220px;overflow:auto;background:#09080d;border:1px solid #201b29;border-radius:14px;padding:10px}.msg{margin:7px 0}.msg b{color:#d7b8ff}.chatForm{display:flex;gap:7px;margin-top:8px}.chatForm input,.input{flex:1;min-width:0;border:1px solid var(--line);background:#0d0b12;color:#fff;padding:11px;border-radius:11px;outline:none}.hostPanel{border-top:1px solid var(--line);margin-top:16px;padding-top:16px}.hostGrid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.subtle{color:var(--muted);font-size:12px}.status{display:flex;gap:7px;align-items:center;font-size:12px}.dot{width:8px;height:8px;border-radius:50%;background:var(--good);box-shadow:0 0 12px var(--good)}
.overlay{position:fixed;inset:0;background:#000b;display:none;align-items:center;justify-content:center;padding:18px;z-index:20}.overlay.show{display:flex}.modal{width:min(480px,100%);max-height:90vh;overflow:auto;background:#14111b;border:1px solid #3b304a;border-radius:20px;padding:20px;box-shadow:0 30px 90px #000}.modal h2{margin-top:0}.modalRow{display:flex;gap:8px;margin-top:10px}.modalRow>*{flex:1}.profilePreview{display:flex;gap:12px;align-items:center;margin:12px 0}.bigAvatar{width:68px;height:68px;border-radius:50%;object-fit:cover;background:#30243d;border:2px solid #4a3a5b}.colorRow{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}.color{width:28px;height:28px;border-radius:50%;border:2px solid #fff4;cursor:pointer}.color.active{outline:2px solid #fff;outline-offset:2px}.roleTable{display:grid;gap:7px}.roleLine{display:flex;gap:9px;padding:9px;background:#0e0c13;border-radius:10px}.roleLine b{min-width:105px}.toast{position:fixed;right:18px;bottom:18px;max-width:360px;padding:13px 15px;background:#17131f;border:1px solid #4b3a60;border-radius:13px;box-shadow:var(--shadow);display:none;z-index:30}.toast.show{display:block;animation:pop .2s ease}.hidden{display:none!important}@keyframes pop{from{transform:translateY(10px);opacity:0}to{transform:none;opacity:1}}
@media(max-width:900px){.layout{grid-template-columns:1fr}.players{grid-template-columns:1fr}.brand{width:100%}}@media(max-width:520px){.app{padding:10px}.card{padding:13px}.actions,.hostGrid{grid-template-columns:1fr}.pill{font-size:12px}.timer{font-size:20px}.top .btn{padding:8px 10px}}
</style>
</head>
<body>
<div class="app">
  <div class="top">
    <div class="brand">🕯️ MAFIA ONLINE</div>
    <span id="roomPill" class="pill">Комната —</span>
    <span id="phasePill" class="pill">ЛОББИ</span>
    <span id="alivePill" class="pill">👥 0</span>
    <span id="timer" class="timer">00:00</span>
    <button class="btn" onclick="openProfile()">👤 Профиль</button>
    <button class="btn" onclick="openRules()">❔ Правила</button>
  </div>

  <div id="notice" class="notice">Подключение...</div>

  <div class="layout">
    <main>
      <section class="card">
        <h2>👥 Игроки</h2>
        <div id="players" class="players"></div>
        <div id="winBox" class="notice hidden"></div>
      </section>

      <section class="card section">
        <h2>💬 Чат</h2>
        <div id="chat" class="chat"></div>
        <div class="chatForm">
          <input id="chatInput" maxlength="180" placeholder="Написать сообщение..." onkeydown="if(event.key==='Enter')sendChat()">
          <button class="btn accent" onclick="sendChat()">➤</button>
        </div>
      </section>

      <section class="card section">
        <h2>📜 События</h2>
        <div id="log" class="log"></div>
      </section>
    </main>

    <aside>
      <section class="card">
        <h2>🎭 Твоя роль</h2>
        <div id="roleBox" class="roleBox">
          <div class="roleIcon">❔</div>
          <div class="roleName">Ожидание игры</div>
          <div class="roleDesc">Когда хост начнёт игру, здесь появится твоя роль.</div>
        </div>

        <div class="section">
          <h3>🎯 Цель</h3>
          <select id="target" class="select"></select>
          <div id="actionHint" class="actionHint"></div>
          <div id="actions" class="actions"></div>
        </div>

        <div id="hostPanel" class="hostPanel hidden">
          <h3>👑 Управление хоста</h3>
          <div id="hostHint" class="subtle">Минимум 4 игрока.</div>
          <div class="actions">
            <button id="startBtn" class="btn accent full" onclick="startGame()">▶️ Начать игру</button>
            <button class="btn" onclick="transferHost()">👑 Передать хоста</button>
            <button class="btn danger" onclick="kickPlayer()">👢 Кикнуть</button>
            <button class="btn full" onclick="restartGame()">🔄 Новая игра</button>
          </div>
        </div>
      </section>
    </aside>
  </div>
</div>

<div id="profileModal" class="overlay"><div class="modal">
  <h2>👤 Профиль</h2>
  <div class="profilePreview"><img id="profileAvatarPreview" class="bigAvatar" alt=""><div><b id="previewName">Игрок</b><div class="subtle">Профиль сохраняется в браузере.</div></div></div>
  <input id="profileName" class="input" maxlength="18" placeholder="Твоё имя">
  <div class="modalRow"><input id="avatarFile" class="input" type="file" accept="image/png,image/jpeg,image/webp,image/gif"></div>
  <div class="subtle" style="margin-top:10px">Цвет</div><div id="colors" class="colorRow"></div>
  <div class="actions"><button class="btn accent" onclick="saveProfile()">Сохранить</button><button class="btn" onclick="closeModals()">Закрыть</button></div>
</div></div>

<div id="rulesModal" class="overlay"><div class="modal">
  <h2>❔ Правила</h2>
  <p class="subtle">Игра начинается от 4 игроков. Ночью специальные роли совершают действия, днём город обсуждает события, затем проходит голосование.</p>
  <div class="roleTable" id="roleTable"></div>
  <div class="actions"><button class="btn accent full" onclick="closeModals()">Готово</button></div>
</div></div>

<div id="toast" class="toast"></div>
<script>
const ROLE_INFO = __ROLE_INFO_JSON__;
const LOBBY = 'ЛОББИ';
let ws=null, state=null, reconnectTimer=null, profile={};
const params=new URLSearchParams(location.search);
const room=params.get('room');
const $=id=>document.getElementById(id);

profile.name=localStorage.getItem('mafia_name')||'';
profile.avatar=localStorage.getItem('mafia_avatar')||'';
profile.color=localStorage.getItem('mafia_color')||'#9b5cff';

const colors=['#9b5cff','#ff4d67','#43e59a','#4da3ff','#ffc857','#ff7a3d','#e56cff','#50d5c2'];
$('colors').innerHTML=colors.map(c=>`<button class="color" style="background:${c}" data-color="${c}" onclick="pickColor('${c}')"></button>`).join('');
$('roleTable').innerHTML=Object.entries(ROLE_INFO).map(([r,v])=>`<div class="roleLine"><b>${v[0]} ${esc(r)}</b><span>${esc(v[1])}</span></div>`).join('');

function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function toast(msg){$('toast').textContent=msg;$('toast').classList.add('show');clearTimeout(window.__toast);window.__toast=setTimeout(()=>$('toast').classList.remove('show'),2800)}
function openProfile(){ $('profileName').value=profile.name;updatePreview();$('profileModal').classList.add('show') }
function openRules(){ $('rulesModal').classList.add('show') }
function closeModals(){ document.querySelectorAll('.overlay').forEach(x=>x.classList.remove('show')) }
function pickColor(c){profile.color=c;updatePreview();document.querySelectorAll('.color').forEach(x=>x.classList.toggle('active',x.dataset.color===c))}
function updatePreview(){ $('previewName').textContent=$('profileName').value.trim()||'Игрок';$('profileAvatarPreview').src=profile.avatar||avatarData(profile.name||'Игрок',profile.color);document.querySelectorAll('.color').forEach(x=>x.classList.toggle('active',x.dataset.color===profile.color)) }
$('profileName').addEventListener('input',updatePreview);
$('avatarFile').addEventListener('change',e=>{const f=e.target.files?.[0];if(!f)return;if(f.size>500000){toast('Аватар слишком большой. Максимум 500 КБ.');e.target.value='';return}const r=new FileReader();r.onload=()=>{profile.avatar=r.result;updatePreview()};r.readAsDataURL(f)});
function avatarData(name,color){const letter=esc((name||'?').trim().slice(0,1).toUpperCase());return 'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect width="100" height="100" rx="50" fill="${color||'#9b5cff'}"/><text x="50" y="62" text-anchor="middle" font-size="45" font-family="Arial" fill="white">${letter}</text></svg>`)}
function saveProfile(){const n=$('profileName').value.trim().slice(0,18);if(!n){toast('Введи имя.');return}profile.name=n;localStorage.setItem('mafia_name',n);localStorage.setItem('mafia_avatar',profile.avatar||'');localStorage.setItem('mafia_color',profile.color);closeModals();if(ws&&ws.readyState===1)send({type:'profile',name:n,avatar:profile.avatar,color:profile.color});else connect()}

function connect(){
  if(!room){$('notice').textContent='Нет кода комнаты. Открой ссылку вида /?room=1234';return}
  if(!profile.name){$('notice').textContent='Сначала создай профиль.';openProfile();return}
  clearTimeout(reconnectTimer);
  const proto=location.protocol==='https:'?'wss://':'ws://';
  ws=new WebSocket(proto+location.host+'/ws');
  ws.onopen=()=>{send({type:'join',room,name:profile.name,avatar:profile.avatar,color:profile.color});toast('Подключение установлено')};
  ws.onmessage=e=>{let d;try{d=JSON.parse(e.data)}catch{return}if(d.type==='error'){toast(d.message);return}if(d.type==='info'){toast(d.message);return}if(d.type==='state'){state=d;render()}};
  ws.onclose=()=>{if(state?.phase!==WIN){$('notice').textContent='Соединение потеряно. Переподключение...';reconnectTimer=setTimeout(connect,2200)}};
  ws.onerror=()=>{};
}
function send(o){if(ws&&ws.readyState===1)ws.send(JSON.stringify(o))}
function sendChat(){const text=$('chatInput').value.trim();if(!text)return;send({type:'chat',message:text});$('chatInput').value=''}
function action(type){const t=$('target').value;if(!t){toast('Выбери игрока.');return}send({type,target:t})}
function startGame(){send({type:'start'})}
function restartGame(){send({type:'start'})}
function kickPlayer(){const t=prompt('Имя игрока для кика:');if(t)send({type:'kick',target:t.trim()})}
function transferHost(){const t=prompt('Передать хоста игроку:');if(t)send({type:'transfer_host',target:t.trim()})}

function render(){
  $('roomPill').textContent='Комната '+state.room;
  $('phasePill').textContent=state.phase;
  $('alivePill').textContent=`👥 ${state.players.filter(p=>p.alive).length}/${state.players.length}`;
  $('timer').textContent=fmt(state.time);
  $('notice').textContent=state.announcement||'';
  renderPlayers();renderRole();renderTargets();renderActions();renderChat();renderLog();renderHost();renderWin();
}
function fmt(n){n=Math.max(0,Number(n)||0);return String(Math.floor(n/60)).padStart(2,'0')+':'+String(n%60).padStart(2,'0')}
function renderPlayers(){
  $('players').innerHTML=state.players.map(p=>{
    const av=p.avatar||avatarData(p.name,p.color);return `<div class="player ${p.alive?'':'dead'}"><img class="avatar" src="${esc(av)}" alt=""><div style="min-width:0;flex:1"><div class="pname">${esc(p.name)} ${p.name===state.host?'<span class="hostMark">👑</span>':''}</div><div class="meta">${p.alive?'🟢 жив':'💀 выбыл'}${p.name===profile.name?' · ты':''}</div></div></div>`
  }).join('');
}
function renderRole(){
  if(!state.role){$('roleBox').innerHTML='<div class="roleIcon">❔</div><div class="roleName">Ожидание игры</div><div class="roleDesc">Хост ещё не начал игру.</div>';return}
  const info=ROLE_INFO[state.role]||['🎭',''];$('roleBox').innerHTML=`<div class="roleIcon">${info[0]}</div><div class="roleName">${esc(state.role)}</div><div class="roleDesc">${esc(info[1])}</div>${state.mafia_team?.length?'<div class="meta" style="margin-top:10px">🔴 Твоя команда: '+state.mafia_team.map(esc).join(', ')+'</div>':''}${state.phase===WIN&&state.roles?'<div class="meta" style="margin-top:10px">Игра завершена — роли раскрыты.</div>':''}`;
}
function renderTargets(){
  const alive=state.players.filter(p=>p.alive&&p.name!==profile.name);$('target').innerHTML=alive.map(p=>`<option value="${esc(p.name)}">${esc(p.name)}</option>`).join('');
  if(!alive.length)$('target').innerHTML='<option value="">Нет доступных целей</option>';
}
function renderActions(){
  const a=$('actions');a.innerHTML='';const role=state.role;const night=state.phase===NIGHT&&state.alive;const vote=state.phase===VOTE&&state.alive;
  const add=(label,type,cls='')=>{const b=document.createElement('button');b.className='btn '+cls;b.textContent=label;b.onclick=()=>action(type);a.appendChild(b)};
  if(night){
    if(role==='Мафия'||role==='Дон')add('🔴 Выбрать жертву','kill','accent');
    if(role==='Маньяк')add('🔪 Убить','maniac_kill','danger');
    if(role==='Доктор')add('🩺 Лечить','heal');
    if(role==='Телохранитель')add('🛡️ Защитить','protect');
    if(role==='Шериф'&&!state.sheriff_used)add('🔎 Проверить','inspect');
    if(role==='Детектив')add('🕵️ Узнать роль','detect');
    if(!a.children.length){const s=document.createElement('div');s.className='subtle full';s.textContent='Этой ночью у твоей роли нет действия.';a.appendChild(s)}
    $('actionHint').textContent=state.action_status||'Выбери цель и действие.';
  }else if(vote){add('🗳️ Отдать голос','vote','accent');$('actionHint').textContent=state.voted_for?'Ты уже проголосовал за: '+state.voted_for:'Выбери игрока и отдай голос.'}
  else{$('actionHint').textContent=state.phase===DAY?'Обсудите события. Скоро начнётся голосование.':state.phase===LOBBY?'Ждём игроков и хоста.':'Действия недоступны.'}
}
function renderChat(){const c=$('chat');c.innerHTML=(state.chat||[]).map(m=>`<div class="msg"><b>${esc(m.name)}:</b> ${esc(m.message)}</div>`).join('');c.scrollTop=c.scrollHeight}
function renderLog(){$('log').textContent=(state.log||[]).join('\n');$('log').scrollTop=$('log').scrollHeight}
function renderHost(){const isHost=profile.name===state.host;$('hostPanel').classList.toggle('hidden',!isHost);if(!isHost)return;$('hostHint').textContent=state.phase===LOBBY?`Игроков: ${state.players.length}/${MAX_PLAYERS}. Минимум 4.`:'Хост может начать новую игру после окончания текущей.';$('startBtn').disabled=state.phase!==LOBBY&&state.phase!==WIN}
function renderWin(){if(state.phase!==WIN||!state.roles){$('winBox').classList.add('hidden');return}const winners=state.winner||'';$('winBox').classList.remove('hidden');$('winBox').innerHTML=`<b>${esc(state.announcement)}</b><div class="subtle" style="margin-top:8px">${esc(winners)}</div><div style="margin-top:10px">${state.roles.map(r=>`${r.alive?'🟢':'💀'} ${esc(r.name)} — <b>${esc(r.role)}</b>`).join('<br>')}</div>`}

updatePreview();pickColor(profile.color);connect();
</script>
</body>
</html>
'''


# Constants are inserted into the page once, avoiding Python data in the browser code.
import json
HTML = HTML.replace("__ROLE_INFO_JSON__", json.dumps(ROLE_INFO, ensure_ascii=False))


def generate_room_code():
    while True:
        code = "".join(random.choice(string.digits) for _ in range(4))
        if code not in rooms:
            return code


def now():
    return asyncio.get_running_loop().time()


def clean_name(value):
    value = str(value or "").strip()
    return " ".join(value.split())[:18]


def clean_color(value):
    value = str(value or "#9b5cff")[:20]
    return value if COLOR_RE.fullmatch(value) else "#9b5cff"


def clean_avatar(value):
    value = str(value or "")
    if len(value) > 600_000:
        return ""
    if value and not value.startswith("data:image/"):
        return ""
    return value


def role_set(count):
    presets = {
        4: ["Мафия", "Мирный", "Мирный", "Мирный"],
        5: ["Мафия", "Доктор", "Мирный", "Мирный", "Мирный"],
        6: ["Мафия", "Шериф", "Доктор", "Мирный", "Мирный", "Мирный"],
        7: ["Мафия", "Мафия", "Шериф", "Доктор", "Мирный", "Мирный", "Мирный"],
        8: ["Мафия", "Дон", "Шериф", "Доктор", "Телохранитель", "Мирный", "Мирный", "Мирный"],
        9: ["Мафия", "Дон", "Шериф", "Доктор", "Телохранитель", "Маньяк", "Мирный", "Мирный", "Мирный"],
        10: ["Мафия", "Дон", "Шериф", "Доктор", "Телохранитель", "Маньяк", "Детектив", "Мирный", "Мирный", "Мирный"],
        11: ["Мафия", "Мафия", "Дон", "Шериф", "Доктор", "Телохранитель", "Маньяк", "Детектив", "Мирный", "Мирный", "Мирный"],
        12: ["Мафия", "Мафия", "Дон", "Шериф", "Доктор", "Телохранитель", "Маньяк", "Детектив", "Мирный", "Мирный", "Мирный", "Мирный"],
    }
    return presets.get(count)


def is_mafia(player):
    return bool(player and player.get("role") in {"Мафия", "Дон"})


def alive(room, name):
    player = room["players"].get(name)
    return bool(player and player.get("alive"))


def alive_names(room):
    return [p["name"] for p in room["players"].values() if p["alive"]]


def role_can_act(player):
    return player and player.get("alive") and player.get("role") in {
        "Мафия", "Дон", "Маньяк", "Доктор", "Телохранитель", "Шериф", "Детектив"
    }


def public_winner_text(room):
    return room.get("winner", "")


def state_for(room, name):
    player = room["players"].get(name)
    remaining = max(0, int(room["ends"] - now())) if room.get("ends") else 0
    mafia_team = []
    if player and is_mafia(player):
        mafia_team = [p["name"] for p in room["players"].values() if is_mafia(p) and p["alive"]]

    roles = None
    if room["phase"] == WIN:
        roles = [
            {"name": p["name"], "role": p["role"], "alive": p["alive"]}
            for p in room["players"].values()
        ]

    voted_for = room["votes"].get(name) if player else None
    action_status = ""
    if player and room["phase"] == NIGHT:
        if player["role"] == "Шериф" and player["sheriff_used"]:
            action_status = "Проверка шерифа уже использована."
        elif player["name"] in room["night_actions"]:
            action_status = "Действие принято. Можно изменить выбор до конца ночи."

    return {
        "type": "state",
        "room": room["code"],
        "host": room["host"],
        "phase": room["phase"],
        "time": remaining,
        "role": player["role"] if player else None,
        "alive": player["alive"] if player else False,
        "sheriff_used": player.get("sheriff_used", False) if player else False,
        "voted_for": voted_for,
        "action_status": action_status,
        "mafia_team": mafia_team,
        "players": [
            {
                "name": p["name"],
                "alive": p["alive"],
                "avatar": p.get("avatar", ""),
                "color": p.get("color", "#9b5cff"),
            }
            for p in room["players"].values()
        ],
        "announcement": room["announcement"],
        "log": room["log"][-100:],
        "chat": room["chat"][-100:],
        "roles": roles,
        "winner": public_winner_text(room),
    }


async def broadcast(room):
    for websocket, name in list(room["connections"].items()):
        try:
            await websocket.send_json(state_for(room, name))
        except Exception:
            room["connections"].pop(websocket, None)


def assign_roles(room):
    roles = role_set(len(room["players"]))
    if not roles:
        return False
    players = list(room["players"].values())
    random.shuffle(players)
    random.shuffle(roles)
    for player, role in zip(players, roles):
        player["role"] = role
        player["sheriff_used"] = False
    return True


def check_winner(room):
    alive_players = [p for p in room["players"].values() if p["alive"]]
    mafia = [p for p in alive_players if is_mafia(p)]
    maniac = [p for p in alive_players if p["role"] == "Маньяк"]
    citizens = [p for p in alive_players if not is_mafia(p) and p["role"] != "Маньяк"]

    if not mafia and not maniac:
        room["phase"] = WIN
        room["ends"] = 0
        room["winner"] = "Победа мирных жителей"
        room["announcement"] = "🟢 Мирные жители победили!"
        room["log"].append("🏆 Победа мирных жителей.")
        return True

    if maniac and len(alive_players) == 1:
        room["phase"] = WIN
        room["ends"] = 0
        room["winner"] = "Победа маньяка"
        room["announcement"] = "🔪 Маньяк победил!"
        room["log"].append("🏆 Победа маньяка.")
        return True

    if mafia and len(mafia) >= len(citizens) + len(maniac):
        room["phase"] = WIN
        room["ends"] = 0
        room["winner"] = "Победа мафии"
        room["announcement"] = "🔴 Мафия захватила город!"
        room["log"].append("🏆 Победа мафии.")
        return True

    return False


def resolve_night(room):
    protected = {x for x in (room["doctor_target"], room["bodyguard_target"]) if x}
    deaths = []

    # Mafia votes: the target with the most mafia votes is killed.
    mafia_targets = [t for t in room["mafia_votes"].values() if alive(room, t)]
    if mafia_targets:
        counts = {}
        for target in mafia_targets:
            counts[target] = counts.get(target, 0) + 1
        max_count = max(counts.values())
        top = [target for target, count in counts.items() if count == max_count]
        if len(top) == 1:
            room["night_target"] = top[0]
        else:
            room["night_target"] = None

    for target in (room["night_target"], room["maniac_target"]):
        if target and alive(room, target) and target not in protected and target not in deaths:
            deaths.append(target)

    for target in deaths:
        room["players"][target]["alive"] = False
        room["log"].append(f"💀 Ночью погиб {target}.")

    if deaths:
        room["announcement"] = "☀️ Город просыпается. Ночью произошло убийство."
    else:
        room["announcement"] = "☀️ Город просыпается. Этой ночью никто не погиб."

    room["night_target"] = None
    room["maniac_target"] = None
    room["doctor_target"] = None
    room["bodyguard_target"] = None
    room["mafia_votes"] = {}
    room["night_actions"] = set()


def resolve_vote(room):
    valid_votes = {voter: target for voter, target in room["votes"].items() if alive(room, voter) and alive(room, target)}
    counts = {}
    for target in valid_votes.values():
        counts[target] = counts.get(target, 0) + 1

    room["votes"] = {}
    if not counts:
        room["announcement"] = "🤷 Никто не проголосовал."
        room["log"].append("🗳️ Голосование завершилось без голосов.")
        return

    maximum = max(counts.values())
    top = [name for name, count in counts.items() if count == maximum]
    if len(top) == 1 and alive(room, top[0]):
        victim = top[0]
        room["players"][victim]["alive"] = False
        room["announcement"] = f"⚖️ {victim} был изгнан голосованием."
        room["log"].append(f"⚖️ {victim} изгнан."
        )
    else:
        room["announcement"] = "⚖️ Ничья. Никто не изгнан."
        room["log"].append("⚖️ Голоса разделились. Никто не изгнан.")


async def start_game(room):
    task = room.get("game_task")
    if task and not task.done() and task is not asyncio.current_task():
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    if len(room["players"]) < 4:
        return False
    if not assign_roles(room):
        return False

    for player in room["players"].values():
        player["alive"] = True
        player["sheriff_used"] = False

    room.update({
        "night_target": None,
        "maniac_target": None,
        "doctor_target": None,
        "bodyguard_target": None,
        "mafia_votes": {},
        "night_actions": set(),
        "votes": {},
        "chat": [],
        "log": ["🎬 Новая игра началась! Роли распределены."],
        "phase": NIGHT,
        "ends": now() + NIGHT_SECONDS,
        "announcement": "🌙 Город засыпает. Ночные роли просыпаются.",
        "winner": "",
    })
    room["game_task"] = asyncio.create_task(game_loop(room))
    return True


async def game_loop(room):
    try:
        while room["phase"] != WIN:
            remaining = room["ends"] - now()
            if remaining > 0:
                await broadcast(room)
                await asyncio.sleep(min(1, remaining))
                continue

            if room["phase"] == NIGHT:
                resolve_night(room)
                if check_winner(room):
                    await broadcast(room)
                    return
                room["phase"] = DAY
                room["ends"] = now() + DAY_SECONDS
                room["announcement"] = "☀️ День. Обсудите события ночи."
                await broadcast(room)
                continue

            if room["phase"] == DAY:
                if check_winner(room):
                    await broadcast(room)
                    return
                room["phase"] = VOTE
                room["ends"] = now() + VOTE_SECONDS
                room["votes"] = {}
                room["announcement"] = "🗳️ Голосование началось. Выберите игрока."
                room["log"].append("🗳️ Началось дневное голосование.")
                await broadcast(room)
                continue

            if room["phase"] == VOTE:
                resolve_vote(room)
                if check_winner(room):
                    await broadcast(room)
                    return
                room["phase"] = NIGHT
                room["ends"] = now() + NIGHT_SECONDS
                room["announcement"] = "🌙 Город засыпает. Ночные роли просыпаются."
                await broadcast(room)
                continue

            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass


async def close_room_task(room):
    task = room.get("game_task")
    if task and not task.done():
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


@app.get("/")
async def home():
    return HTMLResponse(HTML)


@app.get("/create")
async def create_room():
    code = generate_room_code()
    rooms[code] = {
        "code": code,
        "host": None,
        "players": {},
        "connections": {},
        "phase": LOBBY,
        "ends": 0,
        "announcement": "Ожидание игроков. Минимум 4 игрока.",
        "night_target": None,
        "maniac_target": None,
        "doctor_target": None,
        "bodyguard_target": None,
        "mafia_votes": {},
        "night_actions": set(),
        "votes": {},
        "log": ["🏠 Комната создана."],
        "chat": [],
        "game_task": None,
        "winner": "",
    }
    return {"room": code, "url": f"/?room={code}"}


@app.get("/health")
async def health():
    return {"status": "ok", "rooms": len(rooms)}


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    room = None
    name = None

    try:
        first = await websocket.receive_json()
        if first.get("type") != "join":
            await websocket.close()
            return

        name = clean_name(first.get("name"))
        code = str(first.get("room", "")).strip().upper()
        if not name or code not in rooms:
            await websocket.send_json({"type": "error", "message": "Неверное имя или комната."})
            await websocket.close()
            return

        room = rooms[code]
        if room["phase"] not in {LOBBY, WIN}:
            await websocket.send_json({"type": "error", "message": "Игра уже идёт. Дождись окончания партии."})
            await websocket.close()
            return
        if name in room["players"]:
            await websocket.send_json({"type": "error", "message": "Это имя уже занято в комнате."})
            await websocket.close()
            return
        if len(room["players"]) >= MAX_PLAYERS:
            await websocket.send_json({"type": "error", "message": f"Максимум {MAX_PLAYERS} игроков."})
            await websocket.close()
            return

        room["players"][name] = {
            "name": name,
            "alive": True,
            "role": None,
            "avatar": clean_avatar(first.get("avatar")),
            "color": clean_color(first.get("color")),
            "sheriff_used": False,
        }
        room["connections"][websocket] = name
        if room["host"] is None:
            room["host"] = name

        room["log"].append(f"🟢 {name} вошёл в комнату.")
        await broadcast(room)

        while True:
            data = await websocket.receive_json()
            command = str(data.get("type", ""))
            player = room["players"].get(name)

            if command == "profile" and player:
                new_name = clean_name(data.get("name", name))
                if not new_name:
                    await websocket.send_json({"type": "error", "message": "Имя не может быть пустым."})
                    continue
                if new_name != name:
                    if new_name in room["players"]:
                        await websocket.send_json({"type": "error", "message": "Имя уже занято."})
                        continue
                    room["players"][new_name] = room["players"].pop(name)
                    room["players"][new_name]["name"] = new_name
                    room["connections"][websocket] = new_name
                    if room["host"] == name:
                        room["host"] = new_name
                    if name in room["votes"]:
                        room["votes"][new_name] = room["votes"].pop(name)
                    name = new_name
                    player = room["players"][name]

                player["avatar"] = clean_avatar(data.get("avatar"))
                player["color"] = clean_color(data.get("color"))
                await broadcast(room)
                continue

            if command == "chat":
                message = " ".join(str(data.get("message", "")).strip().split())[:180]
                if player and message and (room["phase"] in {LOBBY, DAY, VOTE, WIN} or not player["alive"]):
                    room["chat"].append({"name": name, "message": message})
                    room["chat"] = room["chat"][-100:]
                    await broadcast(room)
                continue

            if command == "start":
                if name != room["host"]:
                    continue
                if room["phase"] not in {LOBBY, WIN}:
                    continue
                if len(room["players"]) < 4:
                    await websocket.send_json({"type": "error", "message": "Нужно минимум 4 игрока."})
                    continue
                await start_game(room)
                await broadcast(room)
                continue

            if command == "kick":
                if name != room["host"] or room["phase"] != LOBBY:
                    continue
                target = clean_name(data.get("target"))
                if target in room["players"] and target != name:
                    for ws, player_name in list(room["connections"].items()):
                        if player_name == target:
                            with suppress(Exception):
                                await ws.send_json({"type": "error", "message": "Ты был исключён хостом."})
                                await ws.close()
                            room["connections"].pop(ws, None)
                    room["players"].pop(target, None)
                    room["log"].append(f"👢 {target} исключён хостом.")
                    await broadcast(room)
                continue

            if command == "transfer_host":
                if name != room["host"]:
                    continue
                target = clean_name(data.get("target"))
                if target in room["players"] and target != name:
                    room["host"] = target
                    room["log"].append(f"👑 {name} передал хоста {target}.")
                    await broadcast(room)
                continue

            if not player or not player["alive"]:
                continue

            target = clean_name(data.get("target"))
            if target == name or not alive(room, target):
                continue

            if command == "kill" and room["phase"] == NIGHT and player["role"] in {"Мафия", "Дон"}:
                room["mafia_votes"][name] = target
                room["night_actions"].add(name)
                room["log"].append(f"🔴 {name} выбрал цель мафии.")

            elif command == "maniac_kill" and room["phase"] == NIGHT and player["role"] == "Маньяк":
                room["maniac_target"] = target
                room["night_actions"].add(name)
                room["log"].append("🔪 Маньяк выбрал цель.")

            elif command == "heal" and room["phase"] == NIGHT and player["role"] == "Доктор":
                room["doctor_target"] = target
                room["night_actions"].add(name)

            elif command == "protect" and room["phase"] == NIGHT and player["role"] == "Телохранитель":
                room["bodyguard_target"] = target
                room["night_actions"].add(name)

            elif command == "inspect" and room["phase"] == NIGHT and player["role"] == "Шериф":
                if player["sheriff_used"]:
                    await websocket.send_json({"type": "info", "message": "🔎 Проверка шерифа уже использована."})
                    continue
                player["sheriff_used"] = True
                room["night_actions"].add(name)
                result = "🔴 МАФИЯ" if is_mafia(room["players"][target]) else "🟢 НЕ МАФИЯ"
                await websocket.send_json({"type": "info", "message": f"🔎 {target}: {result}"})

            elif command == "detect" and room["phase"] == NIGHT and player["role"] == "Детектив":
                room["night_actions"].add(name)
                await websocket.send_json({"type": "info", "message": f"🕵️ {target}: роль «{room['players'][target]['role']}»"})

            elif command == "vote" and room["phase"] == VOTE:
                room["votes"][name] = target
                room["log"].append(f"🗳️ {name} отдал голос.")
                if all(voter in room["votes"] for voter in alive_names(room)):
                    room["ends"] = now()

            await broadcast(room)

    except WebSocketDisconnect:
        pass
    except Exception as error:
        print("WebSocket error:", repr(error))
    finally:
        if room and name:
            room["connections"].pop(websocket, None)
            if name in room["players"]:
                room["players"].pop(name, None)
                room["votes"].pop(name, None)
                room["mafia_votes"].pop(name, None)
                room["night_actions"].discard(name)
                room["log"].append(f"🔴 {name} вышел из комнаты.")

                if room["host"] == name:
                    room["host"] = next(iter(room["players"]), None)
                    if room["host"]:
                        room["log"].append(f"👑 Новый хост: {room['host']}")

                if not room["players"]:
                    await close_room_task(room)
                    rooms.pop(room["code"], None)
                else:
                    await broadcast(room)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
