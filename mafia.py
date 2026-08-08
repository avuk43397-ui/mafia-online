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
    "Мафия": ("🔴", "Ночью выбирает жертву."),
    "Дон": ("👑", "Глава мафии."),
    "Доктор": ("🩺", "Ночью спасает игрока."),
    "Шериф": ("🔎", "Один раз за игру проверяет игрока."),
    "Телохранитель": ("🛡️", "Ночью защищает игрока."),
    "Маньяк": ("🔪", "Ночью убивает игрока и играет один."),
    "Детектив": ("🕵️", "Ночью узнаёт точную роль."),
    "Мирный": ("🟢", "Голосует днём."),
}

HTML = r"""
<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mafia Online</title>
<style>
*{box-sizing:border-box}body{margin:0;font-family:Arial,sans-serif;background:linear-gradient(135deg,#0b0715,#17102a);color:#fff;min-height:100vh}button,input{font:inherit}.wrap{max-width:1050px;margin:auto;padding:20px}.top{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.pill,.btn{border:1px solid #3a2c55;background:#181126;color:#fff;border-radius:12px;padding:10px 14px}.btn{cursor:pointer}.btn:hover{background:#26183e}.accent{background:#7b3ff2;border-color:#9b70ff}.grid{display:grid;grid-template-columns:1fr 320px;gap:16px;margin-top:16px}.card{background:rgba(18,12,31,.92);border:1px solid #35264e;border-radius:18px;padding:18px;box-shadow:0 15px 40px #0005}.players{display:grid;gap:8px}.player{display:flex;align-items:center;gap:10px;padding:10px;border-radius:12px;background:#211733}.avatar{width:38px;height:38px;border-radius:50%;object-fit:cover;background:#33214d}.dead{opacity:.45}.name{flex:1}.small{font-size:12px;color:#aaa}.timer{font-size:24px;font-weight:700}.log{height:310px;overflow:auto;background:#0d0916;padding:12px;border-radius:12px;white-space:pre-wrap}.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.target{width:100%;padding:11px;border-radius:10px;background:#120d1d;color:#fff;border:1px solid #3a2c55}.hidden{display:none}.role{font-size:24px;font-weight:700}.notice{padding:12px;border-radius:12px;background:#24153a;margin:12px 0}.modal{position:fixed;inset:0;background:#0009;display:none;align-items:center;justify-content:center;padding:20px}.modalbox{width:min(420px,100%);background:#171023;border:1px solid #45335e;border-radius:18px;padding:20px}.modal.show{display:flex}@media(max-width:800px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="wrap">
<div class="top">
<span id="roomPill" class="pill">Комната —</span>
<span id="phasePill" class="pill">ЛОББИ</span>
<span id="timer" class="timer">00:00</span>
<button class="btn" onclick="openProfile()">👤 Профиль</button>
</div>
<div id="notice" class="notice">Подключение...</div>
<div class="grid">
<main class="card">
<h2>👥 Игроки</h2>
<div id="players" class="players"></div>
<h2>📜 События</h2>
<div id="log" class="log"></div>
</main>
<aside class="card">
<h2>🎭 Твоя роль</h2>
<div id="role" class="role">Ожидание...</div>
<div id="roleInfo" class="small"></div>
<h3>🎯 Действие</h3>
<select id="target" class="target"></select>
<div class="actions">
<button class="btn accent" onclick="action('kill')">🔴 Убить</button>
<button class="btn" onclick="action('maniac_kill')">🔪 Маньяк</button>
<button class="btn" onclick="action('heal')">🩺 Лечить</button>
<button class="btn" onclick="action('protect')">🛡️ Защитить</button>
<button class="btn" onclick="action('inspect')">🔎 Проверить</button>
<button class="btn" onclick="action('detect')">🕵️ Узнать роль</button>
<button class="btn accent" onclick="action('vote')">🗳️ Голосовать</button>
</div>
<div id="hostActions" class="actions hidden">
<button class="btn accent" onclick="startGame()">▶️ Начать игру</button>
</div>
</aside>
</div>
</div>
<div id="profileModal" class="modal"><div class="modalbox">
<h2>👤 Профиль</h2>
<input id="profileName" class="target" maxlength="18" placeholder="Имя">
<div class="actions"><button class="btn accent" onclick="saveProfile()">Сохранить</button><button class="btn" onclick="closeModals()">Закрыть</button></div>
</div></div>
<script>
let ws=null, state=null;
const params=new URLSearchParams(location.search);
const room=params.get('room');
let name=localStorage.getItem('mafia_name')||'';
if(!room){document.getElementById('notice').textContent='Нет кода комнаты. Откройте ссылку из /create.'}
function connect(){
 if(!room||!name){document.getElementById('notice').textContent='Введите имя в профиле.';openProfile();return}
 ws=new WebSocket((location.protocol==='https:'?'wss://':'ws://')+location.host+'/ws');
 ws.onopen=()=>ws.send(JSON.stringify({type:'join',room,name}));
 ws.onmessage=e=>{const d=JSON.parse(e.data);if(d.type==='error'){alert(d.message);return}if(d.type==='info'){alert(d.message);return}if(d.type==='state'){state=d;render()}};
 ws.onclose=()=>setTimeout(connect,2000);
}
function send(o){if(ws&&ws.readyState===1)ws.send(JSON.stringify(o))}
function render(){
 roomPill.textContent='Комната '+state.room;phasePill.textContent=state.phase;timer.textContent='00:'+String(state.time).padStart(2,'0');notice.textContent=state.announcement||'';
 role.textContent=state.role||'Ожидание...';
 roleInfo.textContent=state.role?((ROLE_INFO[state.role]||['',''])[0]+' '+(ROLE_INFO[state.role]||['',''])[1]):'';
 players.innerHTML=state.players.map(p=>`<div class="player ${p.alive?'':'dead'}"><div class="avatar" style="background:${p.color||'#9b5cff'}"></div><div class="name">${esc(p.name)}<div class="small">${p.alive?'🟢 жив':'💀 мёртв'} ${p.name===state.host?' 👑':''}</div></div></div>`).join('');
 log.textContent=(state.log||[]).join('\n');log.scrollTop=log.scrollHeight;
 target.innerHTML=state.players.filter(p=>p.alive&&p.name!==name).map(p=>`<option>${esc(p.name)}</option>`).join('');
 hostActions.classList.toggle('hidden',name!==state.host||!(state.phase==='ЛОББИ'||state.phase==='🏆 ИГРА ОКОНЧЕНА'));
}
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function action(type){const t=target.value;if(!t)return;send({type,target:t})}
function startGame(){send({type:'start'})}
function openProfile(){profileName.value=name;profileModal.classList.add('show')}
function closeModals(){profileModal.classList.remove('show')}
function saveProfile(){const n=profileName.value.trim().slice(0,18);if(!n)return;name=n;localStorage.setItem('mafia_name',name);closeModals();if(ws&&ws.readyState===1)send({type:'profile',name});else connect()}
connect();
</script>
</body></html>
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
    presets = {
        4: ["Мафия", "Мирный", "Мирный", "Мирный"],
        5: ["Мафия", "Доктор", "Мирный", "Мирный", "Мирный"],
        6: ["Мафия", "Шериф", "Доктор", "Мирный", "Мирный", "Мирный"],
        7: ["Мафия", "Мафия", "Шериф", "Доктор", "Мирный", "Мирный", "Мирный"],
        8: ["Мафия", "Дон", "Шериф", "Доктор", "Телохранитель", "Мирный", "Мирный", "Мирный"],
        9: ["Мафия", "Дон", "Шериф", "Доктор", "Телохранитель", "Маньяк", "Мирный", "Мирный", "Мирный"],
        10: ["Мафия", "Дон", "Шериф", "Доктор", "Телохранитель", "Маньяк", "Детектив", "Мирный", "Мирный", "Мирный"],
    }
    if count in presets:
        return presets[count].copy()
    return ["Мафия", "Мафия", "Дон", "Шериф", "Доктор", "Телохранитель", "Маньяк", "Детектив"] + ["Мирный"] * (count - 8)


def is_mafia(player):
    return player["role"] in {"Мафия", "Дон"}


def alive(room, name):
    player = room["players"].get(name)
    return bool(player and player["alive"])


def state_for(room, name):
    player = room["players"].get(name)
    remaining = max(0, int(room["ends"] - now())) if room["ends"] else 0
    roles = None
    if room["phase"] == WIN:
        roles = [{"name": p["name"], "role": p["role"], "alive": p["alive"]} for p in room["players"].values()]
    return {
        "type": "state", "room": room["code"], "host": room["host"], "phase": room["phase"], "time": remaining,
        "role": player["role"] if player else None, "alive": player["alive"] if player else False,
        "sheriff_used": player.get("sheriff_used", False) if player else False,
        "players": [{"name": p["name"], "alive": p["alive"], "avatar": p.get("avatar", ""), "color": p.get("color", "#9b5cff")} for p in room["players"].values()],
        "announcement": room["announcement"], "log": room["log"][-80:], "roles": roles,
    }


async def broadcast(room):
    for websocket, player_name in list(room["connections"].items()):
        try:
            await websocket.send_json(state_for(room, player_name))
        except Exception:
            room["connections"].pop(websocket, None)


def assign_roles(room):
    roles = role_set(len(room["players"]))
    if roles is None:
        return False
    players = list(room["players"].values())
    random.shuffle(players)
    random.shuffle(roles)
    for player, role in zip(players, roles):
        player["role"] = role
        player["sheriff_used"] = False
    return True


def winner(room):
    alive_players = [p for p in room["players"].values() if p["alive"]]
    mafia = [p for p in alive_players if is_mafia(p)]
    maniac = [p for p in alive_players if p["role"] == "Маньяк"]
    citizens = [p for p in alive_players if not is_mafia(p) and p["role"] != "Маньяк"]
    if not mafia and not maniac:
        room["phase"] = WIN; room["ends"] = 0; room["announcement"] = "🟢 Мирные жители победили!"; room["log"].append("🏆 Победа мирных жителей."); return True
    if maniac and len(alive_players) == 1:
        room["phase"] = WIN; room["ends"] = 0; room["announcement"] = "🔪 Маньяк победил!"; room["log"].append("🏆 Победа маньяка."); return True
    if len(mafia) >= len(citizens) + len(maniac):
        room["phase"] = WIN; room["ends"] = 0; room["announcement"] = "🔴 Мафия захватила город!"; room["log"].append("🏆 Победа мафии."); return True
    return False


def resolve_night(room):
    protected = {x for x in (room["doctor_target"], room["bodyguard_target"]) if x}
    deaths = []
    for target in (room["night_target"], room["maniac_target"]):
        if target and alive(room, target) and target not in protected and target not in deaths:
            deaths.append(target)
    for name in deaths:
        room["players"][name]["alive"] = False
        room["log"].append(f"💀 Ночью погиб {name}.")
    room["announcement"] = "☀️ Город просыпается. Ночью произошло убийство." if deaths else "☀️ Город просыпается. Этой ночью никто не погиб."
    room["night_target"] = None; room["maniac_target"] = None; room["doctor_target"] = None; room["bodyguard_target"] = None


async def start_game(room):
    task = room.get("game_task")
    if task and not task.done() and task is not asyncio.current_task():
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
    for player in room["players"].values():
        player["alive"] = True; player["role"] = None; player["sheriff_used"] = False
    room.update({"night_target": None, "maniac_target": None, "doctor_target": None, "bodyguard_target": None, "votes": {}, "log": ["🎬 Новая игра началась!"], "phase": NIGHT, "ends": now() + 15, "announcement": "🌙 Город засыпает. Ночные роли просыпаются."})
    assign_roles(room)
    room["game_task"] = asyncio.create_task(game_loop(room))


async def game_loop(room):
    try:
        while room["phase"] != WIN:
            if room["ends"] > now():
                await broadcast(room)
                await asyncio.sleep(min(1, room["ends"] - now()))
                continue
            if room["phase"] == NIGHT:
                resolve_night(room)
                if winner(room):
                    await broadcast(room); return
                room["phase"] = DAY; room["ends"] = now() + 8; room["announcement"] = "☀️ День. Обсудите события."
                await broadcast(room)
                await asyncio.sleep(8)
                if winner(room):
                    await broadcast(room); return
                room["phase"] = VOTE; room["ends"] = now() + 45; room["votes"] = {}; room["announcement"] = "🗳️ Голосование началось."
                await broadcast(room)
            elif room["phase"] == VOTE:
                counts = {}
                for target in room["votes"].values():
                    counts[target] = counts.get(target, 0) + 1
                if counts:
                    maximum = max(counts.values())
                    top = [name for name, count in counts.items() if count == maximum]
                    if len(top) == 1 and alive(room, top[0]):
                        victim = top[0]; room["players"][victim]["alive"] = False; room["log"].append(f"⚖️ {victim} изгнан голосованием."); room["announcement"] = f"⚖️ {victim} был изгнан."
                    else:
                        room["announcement"] = "⚖️ Ничья. Никто не изгнан."
                else:
                    room["announcement"] = "🤷 Голосов нет."
                room["votes"] = {}
                if winner(room):
                    await broadcast(room); return
                room["phase"] = NIGHT; room["ends"] = now() + 15; room["announcement"] = "🌙 Город засыпает."
    except asyncio.CancelledError:
        pass


@app.get("/")
async def home():
    return HTMLResponse(HTML)


@app.get("/create")
async def create():
    code = generate_room_code()
    rooms[code] = {"code": code, "host": None, "players": {}, "connections": {}, "phase": LOBBY, "ends": 0, "announcement": "Ожидание игроков...", "night_target": None, "maniac_target": None, "doctor_target": None, "bodyguard_target": None, "votes": {}, "log": [], "game_task": None}
    return {"room": code, "url": f"/?room={code}"}


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    room = None
    name = None
    try:
        first = await websocket.receive_json()
        if first.get("type") != "join":
            return
        name = str(first.get("name", "")).strip()[:18]
        code = str(first.get("room", "")).strip().upper()
        if not name or code not in rooms:
            await websocket.send_json({"type": "error", "message": "Неверное имя или комната."}); return
        room = rooms[code]
        if room["phase"] not in {LOBBY, WIN}:
            await websocket.send_json({"type": "error", "message": "Игра уже идёт."}); return
        if name in room["players"]:
            await websocket.send_json({"type": "error", "message": "Это имя уже занято."}); return
        if len(room["players"]) >= 12:
            await websocket.send_json({"type": "error", "message": "Максимум 12 игроков."}); return
        room["players"][name] = {"name": name, "alive": True, "role": None, "avatar": str(first.get("avatar", ""))[:600000], "color": str(first.get("color", "#9b5cff"))[:20], "sheriff_used": False}
        room["connections"][websocket] = name
        if room["host"] is None:
            room["host"] = name
        room["log"].append(f"🟢 {name} вошёл в комнату.")
        await broadcast(room)
        while True:
            data = await websocket.receive_json()
            player = room["players"].get(name)
            command = data.get("type")
            if command == "profile" and player:
                new_name = str(data.get("name", name)).strip()[:18]
                if not new_name:
                    continue
                if new_name != name:
                    if new_name in room["players"]:
                        await websocket.send_json({"type": "error", "message": "Имя уже занято."}); continue
                    room["players"][new_name] = room["players"].pop(name); room["players"][new_name]["name"] = new_name
                    room["connections"][websocket] = new_name
                    if room["host"] == name: room["host"] = new_name
                    name = new_name; player = room["players"][name]
                player["avatar"] = str(data.get("avatar", ""))[:600000]
                player["color"] = str(data.get("color", "#9b5cff"))[:20]
                await broadcast(room); continue
            if command == "start":
                if name != room["host"]: continue
                if len(room["players"]) < 4:
                    await websocket.send_json({"type": "error", "message": "Нужно минимум 4 игрока."}); continue
                if room["phase"] in {LOBBY, WIN}:
                    await start_game(room); await broadcast(room)
                continue
            if command == "kick":
                if name != room["host"] or room["phase"] != LOBBY: continue
                target = str(data.get("target", ""))
                if target in room["players"] and target != name:
                    for ws, player_name in list(room["connections"].items()):
                        if player_name == target:
                            with suppress(Exception):
                                await ws.send_json({"type": "error", "message": "Ты был исключён хостом."}); await ws.close()
                            room["connections"].pop(ws, None)
                    room["players"].pop(target, None); room["log"].append(f"👢 {target} был исключён хостом."); await broadcast(room)
                continue
            if command == "transfer_host":
                if name != room["host"]: continue
                target = str(data.get("target", ""))
                if target in room["players"] and target != name:
                    room["host"] = target; room["log"].append(f"👑 {name} передал хоста {target}."); await broadcast(room)
                continue
            if not player or not player["alive"]: continue
            target = str(data.get("target", "")).strip()
            if target == name or not alive(room, target): continue
            if command == "kill" and room["phase"] == NIGHT and player["role"] in {"Мафия", "Дон"}:
                room["night_target"] = target
            elif command == "maniac_kill" and room["phase"] == NIGHT and player["role"] == "Маньяк":
                room["maniac_target"] = target
            elif command == "heal" and room["phase"] == NIGHT and player["role"] == "Доктор":
                room["doctor_target"] = target
            elif command == "protect" and room["phase"] == NIGHT and player["role"] == "Телохранитель":
                room["bodyguard_target"] = target
            elif command == "inspect" and room["phase"] == NIGHT and player["role"] == "Шериф" and not player["sheriff_used"]:
                player["sheriff_used"] = True
                result = "🔴 МАФИЯ" if is_mafia(room["players"][target]) else "🟢 НЕ МАФИЯ"
                await websocket.send_json({"type": "info", "message": f"🔎 {target}: {result}"})
            elif command == "detect" and room["phase"] == NIGHT and player["role"] == "Детектив":
                await websocket.send_json({"type": "info", "message": f"🕵️ {target}: роль «{room['players'][target]['role']}»"})
            elif command == "vote" and room["phase"] == VOTE:
                room["votes"][name] = target
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
                room["log"].append(f"🔴 {name} вышел из игры.")
                if room["host"] == name:
                    room["host"] = next(iter(room["players"]), None)
                    if room["host"]:
                        room["log"].append(f"👑 Новый хост: {room['host']}")
                await broadcast(room)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
