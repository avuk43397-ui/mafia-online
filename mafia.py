
import os
import random
import string
import asyncio
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

ROLE_INFO = {
    "Мафия": ("🔴", "Ночью выбирает жертву вместе с Доном."),
    "Дон": ("👑", "Глава мафии. Ночью выбирает жертву."),
    "Доктор": ("🩺", "Ночью спасает одного игрока."),
    "Шериф": ("🔎", "Ночью проверяет игрока на принадлежность к мафии/маньяку."),
    "Телохранитель": ("🛡️", "Ночью защищает игрока от убийства."),
    "Маньяк": ("🔪", "Ночью убивает игрока и играет сам за себя."),
    "Детектив": ("🕵️", "Ночью узнаёт точную роль игрока."),
    "Мирный": ("🟢", "Особых способностей нет. Голосует днём."),
}

HTML = r"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mafia Online</title>
<style>
*{box-sizing:border-box}
:root{--bg:#08090e;--panel:#11131c;--panel2:#171a25;--line:#292d3d;--text:#f5f5f7;--muted:#85899a;--red:#e74c5b;--gold:#d7ad63;--green:#54d48a;--blue:#63a8ff}
body{margin:0;min-height:100vh;background:radial-gradient(circle at 50% -10%,#252034 0,#0b0c12 42%,#050609 100%);color:var(--text);font-family:Inter,Segoe UI,Arial,sans-serif}
button,input{font:inherit}
button{border:0;cursor:pointer}
.hidden{display:none!important}
.wrap{width:min(1120px,94%);margin:0 auto;padding:34px 0 60px}
.brand{text-align:center;margin-bottom:26px}
.brand h1{font-size:58px;letter-spacing:10px;margin:0;text-shadow:0 0 28px #8b2637}
.brand p{color:var(--muted);letter-spacing:4px;margin:7px 0}
.panel{background:linear-gradient(145deg,rgba(24,27,38,.96),rgba(12,14,21,.96));border:1px solid var(--line);border-radius:22px;box-shadow:0 20px 70px rgba(0,0,0,.45);padding:24px}
.login{max-width:620px;margin:40px auto}
.title{font-size:26px;font-weight:800;margin:0 0 8px}
.sub{color:var(--muted);margin-bottom:20px}
.inputs{display:grid;grid-template-columns:1.5fr 1fr;gap:12px}
input{width:100%;background:#0b0d13;border:1px solid #303547;color:#fff;border-radius:13px;padding:15px;outline:0}
input:focus{border-color:#756080;box-shadow:0 0 0 3px rgba(117,96,128,.15)}
.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}
.btn{background:linear-gradient(135deg,#c74352,#7e2738);color:#fff;padding:13px 18px;border-radius:12px;font-weight:800;box-shadow:0 10px 28px rgba(199,67,82,.18)}
.btn:hover{filter:brightness(1.12);transform:translateY(-1px)}
.btn.secondary{background:#202432;border:1px solid #363b4e;box-shadow:none}
.btn.gold{background:linear-gradient(135deg,#d8b36a,#8f6b31);color:#17120a}
.error{color:#ff7785;min-height:24px;margin-top:10px}
.role-help{margin-top:20px;padding:16px;border:1px solid var(--line);border-radius:14px;background:#0c0e15;color:#a9adbc;line-height:1.7}
.game{display:none}
.top{display:grid;grid-template-columns:1fr 1.3fr 120px;gap:14px;align-items:center;margin-bottom:14px}
.box{background:#0d0f16;border:1px solid var(--line);border-radius:16px;padding:15px}
.label{font-size:11px;letter-spacing:2px;color:var(--muted)}
.roomcode{font-size:31px;font-weight:900;letter-spacing:7px;color:var(--gold)}
.phase{text-align:center;font-weight:900;font-size:18px}
.role{text-align:center;color:var(--muted);margin-top:6px}
.timer{font-size:42px;text-align:center;font-weight:900;color:#fff}
.announcement{border:1px solid #393146;background:linear-gradient(90deg,#15111d,#12151f);padding:18px;border-radius:16px;margin-bottom:14px;text-align:center;font-size:18px;font-weight:700}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
h2{font-size:20px;margin:0 0 15px}
.players{display:grid;gap:9px}
.player{display:flex;justify-content:space-between;align-items:center;background:#0c0f16;border:1px solid #252a38;padding:12px;border-radius:12px}
.player.dead{opacity:.45}
.status{font-size:12px;color:var(--green)}
.dead .status{color:#ff6e79}
.player button{padding:7px 10px;border-radius:9px;background:#292e3e;color:#fff}
.log{height:330px;overflow:auto;display:flex;flex-direction:column;gap:8px}
.log div{padding:10px;background:#0c0f16;border-radius:10px;color:#b9bdca;font-size:14px}
.action-title{color:var(--gold);font-weight:800;margin-top:16px}
.result{margin-top:15px;border:1px solid #594b32;background:linear-gradient(145deg,#19150d,#100f0b);border-radius:16px;padding:18px}
.result h3{margin:0 0 12px}
.role-row{display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid #292519}
.role-row:last-child{border-bottom:0}
.footer{color:#555a6b;text-align:center;margin-top:20px;font-size:12px}
@media(max-width:760px){.top,.grid,.inputs{grid-template-columns:1fr}.timer{font-size:30px}.brand h1{font-size:42px}.wrap{padding-top:18px}}
</style>
</head>
<body>
<div class="wrap">
  <div class="brand"><h1>MAFIA</h1><p>NIGHT • LIES • SURVIVAL</p></div>

  <section id="login" class="panel login">
    <div class="title">🔥 Добро пожаловать</div>
    <div class="sub">Создай комнату или присоединись к друзьям.</div>
    <div class="inputs">
      <input id="name" maxlength="18" placeholder="Твоё имя">
      <input id="room" maxlength="4" placeholder="Код комнаты">
    </div>
    <div class="actions">
      <button class="btn" onclick="createRoom()">✨ Создать комнату</button>
      <button class="btn secondary" onclick="joinRoom()">🚪 Войти</button>
    </div>
    <div id="loginError" class="error"></div>
    <div class="role-help">
      <b>Автоматический подбор ролей</b><br>
      4–5: Мафия, Доктор, Шериф<br>
      6–7: 2 Мафии, Доктор, Шериф<br>
      8–9: Мафия, Дон, Доктор, Шериф, Телохранитель<br>
      10–11: + Маньяк и Детектив<br>
      12: усиленный состав с 3 членами мафии
    </div>
  </section>

  <section id="game" class="game">
    <div class="top">
      <div class="box">
        <div class="label">КОД КОМНАТЫ</div>
        <div id="roomCode" class="roomcode">----</div>
        <button class="btn secondary" style="margin-top:8px" onclick="copyRoom()">📋 Скопировать</button>
      </div>
      <div class="box">
        <div id="phase" class="phase">ЛОББИ</div>
        <div id="myRole" class="role">Роль не назначена</div>
      </div>
      <div class="box timer" id="timer">--</div>
    </div>

    <div id="announcement" class="announcement">Ожидание игроков...</div>

    <div class="grid">
      <div class="panel">
        <h2>👥 Игроки</h2>
        <div id="players" class="players"></div>
        <div id="hostControls" class="actions hidden">
          <button id="startButton" class="btn gold" onclick="startGame()">▶ Начать игру</button>
        </div>
        <div id="actions"></div>
        <div id="result" class="result hidden"></div>
      </div>
      <div class="panel">
        <h2>📜 События</h2>
        <div id="log" class="log"></div>
      </div>
    </div>
    <div class="footer">Mafia Online • WebSocket realtime</div>
  </section>
</div>

<script>
let ws=null, myName="", myRoom="", lastState=null;

function $(id){return document.getElementById(id)}
function setError(t){$("loginError").textContent=t||""}

async function createRoom(){
  setError("");
  try{
    const r=await fetch("/create");
    if(!r.ok) throw new Error("Не удалось создать комнату");
    const d=await r.json();
    $("room").value=d.room;
    joinRoom();
  }catch(e){setError(e.message)}
}

function joinRoom(){
  setError("");
  myName=$("name").value.trim();
  myRoom=$("room").value.trim().toUpperCase();
  if(!myName){setError("Введи имя.");return}
  if(!/^\d{4}$/.test(myRoom)){setError("Код комнаты должен состоять из 4 цифр.");return}

  const proto=location.protocol==="https:"?"wss":"ws";
  ws=new WebSocket(`${proto}://${location.host}/ws`);
  ws.onopen=()=>ws.send(JSON.stringify({type:"join",name:myName,room:myRoom}));
  ws.onmessage=e=>handleMessage(JSON.parse(e.data));
  ws.onerror=()=>setError("Не удалось подключиться к серверу.");
  ws.onclose=()=>{};
}

function handleMessage(d){
  if(d.type==="error"){setError(d.message);return}
  if(d.type==="info"){alert(d.message);return}
  if(d.type==="state"){lastState=d; render(d)}
}

function send(type,target=""){
  if(ws && ws.readyState===1) ws.send(JSON.stringify({type,target}));
}

function startGame(){send("start")}
function copyRoom(){
  navigator.clipboard?.writeText(lastState?.room||myRoom);
}

function render(s){
  $("login").style.display="none";
  $("game").style.display="block";
  $("roomCode").textContent=s.room;
  $("phase").textContent=s.phase;
  $("timer").textContent=s.time>0?s.time:"--";
  $("announcement").textContent=s.announcement||"";
  $("myRole").textContent=s.role ? roleText(s.role) : "Роль не назначена";

  const isHost=s.host===myName;
  $("hostControls").classList.toggle("hidden",!(isHost && (s.phase==="ЛОББИ"||s.phase==="🏆 ИГРА ОКОНЧЕНА")));
  $("startButton").textContent=s.phase==="🏆 ИГРА ОКОНЧЕНА"?"🔄 Начать заново":"▶ Начать игру";

  $("players").innerHTML="";
  for(const p of s.players){
    const row=document.createElement("div");
    row.className="player"+(p.alive?"":" dead");
    const left=document.createElement("span");
    left.textContent=(p.alive?"🟢 ":"💀 ")+p.name;
    const right=document.createElement("span");
    right.className="status";
    right.textContent=p.alive?"В игре":"Мёртв";
    row.append(left,right);
    $("players").appendChild(row);
  }

  const log=$("log");
  log.innerHTML="";
  for(const x of (s.log||[])){
    const el=document.createElement("div");el.textContent=x;log.appendChild(el);
  }
  log.scrollTop=log.scrollHeight;

  renderActions(s);
  renderResult(s);
}

function roleText(r){
  const icons={Мафия:"🔴",Дон:"👑",Доктор:"🩺",Шериф:"🔎",Телохранитель:"🛡️",Маньяк:"🔪",Детектив:"🕵️",Мирный:"🟢"};
  return (icons[r]||"🎭")+" "+r;
}

function renderActions(s){
  const box=$("actions");box.innerHTML="";
  if(s.phase==="🏆 ИГРА ОКОНЧЕНА"||s.phase==="ЛОББИ")return;
  if(!s.role||!s.alive) {
    if(!s.alive && s.phase!=="🏆 ИГРА ОКОНЧЕНА"){
      const d=document.createElement("div");d.className="action-title";d.textContent="💀 Вы мертвы. Наблюдайте за игрой.";box.appendChild(d);
    }
    return;
  }

  let targets=s.players.filter(p=>p.alive && p.name!==myName).map(p=>p.name);
  let actionType=null,title="";

  if(s.phase==="🌙 НОЧЬ"){
    if(s.role==="Мафия"||s.role==="Дон"){actionType="kill";title="🔪 Выберите жертву мафии";}
    if(s.role==="Маньяк"){actionType="maniac_kill";title="🔪 Выберите жертву";}
    if(s.role==="Доктор"){actionType="heal";title="🩺 Кого спасти?";targets=s.players.filter(p=>p.alive).map(p=>p.name)}
    if(s.role==="Телохранитель"){actionType="protect";title="🛡️ Кого защитить?";targets=s.players.filter(p=>p.alive).map(p=>p.name)}
    if(s.role==="Шериф"){actionType="inspect";title="🔎 Кого проверить?"}
    if(s.role==="Детектив"){actionType="detect";title="🕵️ Узнать точную роль?"}
  }
  if(s.phase==="🗳️ ГОЛОСОВАНИЕ"){actionType="vote";title="⚖️ Кого изгнать?"}

  if(actionType){
    const t=document.createElement("div");t.className="action-title";t.textContent=title;box.appendChild(t);
    const row=document.createElement("div");row.className="actions";
    for(const name of targets){
      const b=document.createElement("button");b.className="btn secondary";b.textContent=name;
      b.onclick=()=>send(actionType,name);row.appendChild(b);
    }
    box.appendChild(row);
  }
}

function renderResult(s){
  const r=$("result");
  if(s.phase!=="🏆 ИГРА ОКОНЧЕНА"||!s.roles){r.classList.add("hidden");return}
  r.classList.remove("hidden");
  r.innerHTML="<h3>🏆 Итоги игры — все роли раскрыты</h3>";
  for(const x of s.roles){
    const line=document.createElement("div");line.className="role-row";
    const n=document.createElement("span");n.textContent=x.name+(x.alive?"":" 💀");
    const role=document.createElement("b");role.textContent=roleText(x.role);
    line.append(n,role);r.appendChild(line);
  }
}
</script>
</body>
</html>
"""

def generate_room_code():
    while True:
        code = "".join(random.choice(string.digits) for _ in range(4))
        if code not in rooms:
            return code

def now():
    return asyncio.get_running_loop().time()

def role_set(count):
    if count < 4:
        return None
    if count <= 5:
        return ["Мафия", "Доктор", "Шериф"] + ["Мирный"] * (count - 3)
    if count <= 7:
        return ["Мафия", "Мафия", "Доктор", "Шериф"] + ["Мирный"] * (count - 4)
    if count <= 9:
        return ["Мафия", "Дон", "Доктор", "Шериф", "Телохранитель"] + ["Мирный"] * (count - 5)
    if count <= 11:
        return ["Мафия", "Дон", "Доктор", "Шериф", "Телохранитель", "Маньяк", "Детектив"] + ["Мирный"] * (count - 7)
    return ["Мафия", "Мафия", "Дон", "Доктор", "Шериф", "Телохранитель", "Маньяк", "Детектив"] + ["Мирный"] * (count - 8)

def is_mafia(player):
    return player["role"] in {"Мафия", "Дон"}

def is_alive(room, name):
    p = room["players"].get(name)
    return bool(p and p["alive"])

def get_state(room, player_name):
    player = room["players"].get(player_name)
    remaining = max(0, int(room["ends"] - now())) if room["ends"] else 0
    roles = None
    if room["phase"] == WIN:
        roles = [{"name": p["name"], "role": p["role"], "alive": p["alive"]} for p in room["players"].values()]
    return {
        "type": "state",
        "room": room["code"],
        "host": room["host"],
        "phase": room["phase"],
        "time": remaining,
        "role": player["role"] if player else None,
        "alive": player["alive"] if player else False,
        "players": [{"name": p["name"], "alive": p["alive"]} for p in room["players"].values()],
        "announcement": room["announcement"],
        "log": room["log"][-80:],
        "roles": roles,
    }

async def broadcast(room):
    for websocket, player_name in list(room["connections"].items()):
        try:
            await websocket.send_json(get_state(room, player_name))
        except Exception:
            room["connections"].pop(websocket, None)

def assign_roles(room):
    roles = role_set(len(room["players"]))
    if roles is None:
        return False
    players = list(room["players"].values())
    random.shuffle(roles)
    random.shuffle(players)
    for p, role in zip(players, roles):
        p["role"] = role
    return True

def check_winner(room):
    alive = [p for p in room["players"].values() if p["alive"]]
    mafia = [p for p in alive if is_mafia(p)]
    maniac = [p for p in alive if p["role"] == "Маньяк"]
    citizens = [p for p in alive if not is_mafia(p) and p["role"] != "Маньяк"]

    if not mafia and not maniac:
        room["phase"] = WIN
        room["ends"] = 0
        room["announcement"] = "🟢 Мирные жители победили!"
        room["log"].append("🏆 Победа мирных жителей!")
        return True

    if maniac and len(alive) == 1:
        room["phase"] = WIN
        room["ends"] = 0
        room["announcement"] = "🔪 Маньяк остался один и победил!"
        room["log"].append("🏆 Маньяк победил!")
        return True

    if len(mafia) >= len(citizens) + len(maniac):
        room["phase"] = WIN
        room["ends"] = 0
        room["announcement"] = "🔴 Мафия захватила город!"
        room["log"].append("🏆 Мафия победила!")
        return True

    if not alive:
        room["phase"] = WIN
        room["ends"] = 0
        room["announcement"] = "⚖️ Все игроки погибли. Игра окончена."
        room["log"].append("🏆 Игра окончена.")
        return True

    return False

def resolve_night(room):
    protected = set()
    if room["doctor_target"]:
        protected.add(room["doctor_target"])
    if room["bodyguard_target"]:
        protected.add(room["bodyguard_target"])

    deaths = []
    for target in (room["night_target"], room["maniac_target"]):
        if target and is_alive(room, target) and target not in protected and target not in deaths:
            deaths.append(target)

    if deaths:
        for name in deaths:
            room["players"][name]["alive"] = False
            room["log"].append(f"💀 Ночью погиб {name}.")
        room["announcement"] = "☀️ Город просыпается. Ночью произошло убийство."
    else:
        room["announcement"] = "☀️ Город просыпается. Этой ночью никто не погиб."

    room["night_target"] = None
    room["maniac_target"] = None
    room["doctor_target"] = None
    room["bodyguard_target"] = None

async def start_game(room):
    task = room.get("game_task")
    current = asyncio.current_task()
    if task and not task.done() and task is not current:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    for p in room["players"].values():
        p["alive"] = True
        p["role"] = None

    room["night_target"] = None
    room["maniac_target"] = None
    room["doctor_target"] = None
    room["bodyguard_target"] = None
    room["votes"] = {}
    room["log"] = ["🎬 Новая игра началась!"]
    assign_roles(room)
    room["phase"] = NIGHT
    room["ends"] = now() + 15
    room["announcement"] = "🌙 Город засыпает. Особые роли делают свой выбор."
    room["game_task"] = asyncio.create_task(game_loop(room))

async def game_loop(room):
    try:
        while room["phase"] != WIN:
            current = now()
            if room["ends"] > current:
                await broadcast(room)
                await asyncio.sleep(min(1, room["ends"] - current))
                continue

            if room["phase"] == NIGHT:
                resolve_night(room)
                if check_winner(room):
                    await broadcast(room)
                    return
                room["phase"] = DAY
                room["ends"] = now() + 8
                await broadcast(room)
                await asyncio.sleep(8)
                if check_winner(room):
                    await broadcast(room)
                    return
                room["phase"] = VOTE
                room["ends"] = now() + 60
                room["votes"] = {}
                room["announcement"] = "🗳️ День. Обсудите подозреваемых и проголосуйте."
                await broadcast(room)

            elif room["phase"] == VOTE:
                counts = {}
                for target in room["votes"].values():
                    counts[target] = counts.get(target, 0) + 1

                if counts:
                    maximum = max(counts.values())
                    winners = [n for n, c in counts.items() if c == maximum]
                    if len(winners) > 1:
                        room["announcement"] = "⚖️ Ничья! Никто не был изгнан."
                        room["log"].append("⚖️ Голоса разделились.")
                    else:
                        victim = winners[0]
                        if is_alive(room, victim):
                            room["players"][victim]["alive"] = False
                            room["announcement"] = f"⚖️ {victim} был изгнан голосованием."
                            room["log"].append(room["announcement"])
                else:
                    room["announcement"] = "🤷 Никто не проголосовал."

                room["votes"] = {}
                if check_winner(room):
                    await broadcast(room)
                    return

                room["phase"] = NIGHT
                room["ends"] = now() + 15
                room["announcement"] = "🌙 Город засыпает. Ночные роли просыпаются."
                await broadcast(room)
    except asyncio.CancelledError:
        return

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
        "announcement": "Ожидание игроков...",
        "night_target": None,
        "maniac_target": None,
        "doctor_target": None,
        "bodyguard_target": None,
        "votes": {},
        "log": [],
        "game_task": None,
    }
    print("Создана комната:", code)
    return {"room": code}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    room = None
    player_name = None

    try:
        first = await websocket.receive_json()
        if first.get("type") != "join":
            return

        player_name = str(first.get("name", "")).strip()
        room_code = str(first.get("room", "")).strip().upper()

        if not player_name:
            await websocket.send_json({"type": "error", "message": "Введи имя."})
            return
        if room_code not in rooms:
            await websocket.send_json({"type": "error", "message": "Комната не найдена."})
            return

        room = rooms[room_code]

        if room["phase"] not in {LOBBY, WIN}:
            await websocket.send_json({"type": "error", "message": "Игра уже идёт. Подожди окончания."})
            return
        if player_name in room["players"]:
            await websocket.send_json({"type": "error", "message": "Это имя уже занято."})
            return
        if len(room["players"]) >= 12:
            await websocket.send_json({"type": "error", "message": "Максимум 12 игроков."})
            return

        room["players"][player_name] = {"name": player_name, "alive": True, "role": None}
        room["connections"][websocket] = player_name

        if room["host"] is None:
            room["host"] = player_name

        await broadcast(room)

        while True:
            data = await websocket.receive_json()
            command = data.get("type")
            player = room["players"].get(player_name)

            if command == "start":
                if player_name != room["host"]:
                    continue
                if room["phase"] not in {LOBBY, WIN}:
                    continue
                if len(room["players"]) < 4:
                    await websocket.send_json({"type": "error", "message": "Нужно минимум 4 игрока."})
                    continue
                await start_game(room)
                await broadcast(room)
                continue

            if not player or not player["alive"]:
                continue

            target = str(data.get("target", "")).strip()
            if target == player_name or not is_alive(room, target):
                continue

            if command == "kill" and room["phase"] == NIGHT and player["role"] in {"Мафия", "Дон"}:
                room["night_target"] = target
                room["announcement"] = "🔪 Мафия выбрала цель."
                await broadcast(room)

            elif command == "maniac_kill" and room["phase"] == NIGHT and player["role"] == "Маньяк":
                room["maniac_target"] = target
                room["announcement"] = "🔪 Маньяк выбрал цель."
                await broadcast(room)

            elif command == "heal" and room["phase"] == NIGHT and player["role"] == "Доктор":
                room["doctor_target"] = target
                room["log"].append("🩺 Доктор сделал выбор.")
                await broadcast(room)

            elif command == "protect" and room["phase"] == NIGHT and player["role"] == "Телохранитель":
                room["bodyguard_target"] = target
                room["log"].append("🛡️ Телохранитель сделал выбор.")
                await broadcast(room)

            elif command == "inspect" and room["phase"] == NIGHT and player["role"] == "Шериф":
                target_player = room["players"].get(target)
                if target_player:
                    result = "🔴 МАФИЯ" if is_mafia(target_player) else ("🟡 МАНЬЯК" if target_player["role"] == "Маньяк" else "🟢 НЕ МАФИЯ")
                    await websocket.send_json({"type": "info", "message": f"{target}: {result}"})

            elif command == "detect" and room["phase"] == NIGHT and player["role"] == "Детектив":
                target_player = room["players"].get(target)
                if target_player:
                    await websocket.send_json({"type": "info", "message": f"{target} — роль: {target_player['role']}"})

            elif command == "vote" and room["phase"] == VOTE:
                room["votes"][player_name] = target
                room["announcement"] = f"🗳️ {player_name} проголосовал."
                await broadcast(room)

    except WebSocketDisconnect:
        pass
    except Exception as error:
        print("WebSocket error:", repr(error))
    finally:
        if room is not None and player_name is not None:
            room["connections"].pop(websocket, None)

            if room["phase"] == LOBBY and player_name in room["players"]:
                del room["players"][player_name]
                if room["host"] == player_name:
                    room["host"] = next(iter(room["players"]), None)

            await broadcast(room)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
