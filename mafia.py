import os
import random
import string
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

rooms = {}


def room_code():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=5))


HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mafia Online</title>

<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    min-height: 100vh;
    background: radial-gradient(circle at top, #24113d, #080812 70%);
    color: white;
    font-family: Arial, sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
}

.box {
    width: 420px;
    max-width: 92%;
    padding: 30px;
    background: rgba(20,20,35,.94);
    border: 1px solid #653b9b;
    border-radius: 20px;
    box-shadow: 0 0 40px rgba(130,60,220,.25);
    text-align: center;
}

h1 {
    margin-top: 0;
    color: #c995ff;
}

input {
    width: 100%;
    padding: 14px;
    margin: 7px 0;
    border: 1px solid #553477;
    border-radius: 10px;
    background: #11111e;
    color: white;
    outline: none;
}

button {
    width: 100%;
    padding: 14px;
    margin-top: 10px;
    border: 0;
    border-radius: 10px;
    background: linear-gradient(135deg,#7d3cff,#b14cff);
    color: white;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
}

button:hover {
    filter: brightness(1.15);
}

#game {
    display: none;
}

#players {
    text-align: left;
    margin-top: 20px;
}

.player {
    padding: 10px;
    margin: 6px 0;
    background: #151525;
    border-radius: 8px;
}

#message {
    margin-top: 15px;
    color: #c995ff;
    min-height: 22px;
}

.code {
    font-size: 28px;
    letter-spacing: 6px;
    color: #e2c7ff;
}
</style>
</head>

<body>

<div class="box" id="menu">

    <h1>MAFIA ONLINE</h1>

    <input id="name" placeholder="Твоё имя">

    <button onclick="createRoom()">Создать комнату</button>

    <input id="code" placeholder="Код комнаты">

    <button onclick="joinRoom()">Войти в комнату</button>

    <div id="message"></div>

</div>


<div class="box" id="game">

    <h1>MAFIA</h1>

    <div>Код комнаты:</div>
    <div class="code" id="roomCode"></div>

    <div id="message"></div>

    <h3>Игроки</h3>
    <div id="players"></div>

    <button onclick="startGame()">НАЧАТЬ ИГРУ</button>

</div>


<script>

let socket = null;
let myName = "";
let currentRoom = "";


function connect(room, name) {

    myName = name;
    currentRoom = room;

    const protocol = location.protocol === "https:" ? "wss" : "ws";

    socket = new WebSocket(
        protocol + "://" + location.host + "/ws/" + room
    );

    socket.onopen = function() {

        socket.send(JSON.stringify({
            type: "join",
            name: name
        }));

    };


    socket.onmessage = function(event) {

        const data = JSON.parse(event.data);

        if (data.type === "error") {
            document.getElementById("message").textContent = data.message;
            return;
        }

        if (data.type === "room") {

            document.getElementById("menu").style.display = "none";
            document.getElementById("game").style.display = "block";

            document.getElementById("roomCode").textContent = currentRoom;

            updatePlayers(data.players);
        }

        if (data.type === "game_started") {

            document.getElementById("message").textContent =
                "Игра началась!";

        }

    };


    socket.onclose = function() {

        document.getElementById("message").textContent =
            "Соединение закрыто.";

    };

}


function createRoom() {

    const name = document.getElementById("name").value.trim();

    if (!name) {
        alert("Введи имя");
        return;
    }

    fetch("/create")
        .then(response => response.json())
        .then(data => {

            connect(data.code, name);

        });

}


function joinRoom() {

    const name = document.getElementById("name").value.trim();
    const code = document.getElementById("code").value.trim().toUpperCase();

    if (!name || !code) {
        alert("Введи имя и код комнаты");
        return;
    }

    connect(code, name);

}


function updatePlayers(players) {

    const container = document.getElementById("players");

    container.innerHTML = "";

    players.forEach(function(player) {

        const div = document.createElement("div");

        div.className = "player";

        div.textContent = player;

        container.appendChild(div);

    });

}


function startGame() {

    if (!socket || socket.readyState !== WebSocket.OPEN) {
        return;
    }

    socket.send(JSON.stringify({
        type: "start"
    }));

}

</script>

</body>
</html>
"""


@app.get("/")
async def home():
    return HTMLResponse(HTML)


@app.get("/create")
async def create():
    code = room_code()

    while code in rooms:
        code = room_code()

    rooms[code] = {
        "players": [],
        "started": False
    }

    return {"code": code}


async def send_room(code):
    if code not in rooms:
        return

    data = {
        "type": "room",
        "players": [p["name"] for p in rooms[code]["players"]]
    }

    dead = []

    for player in rooms[code]["players"]:
        try:
            await player["socket"].send_json(data)
        except Exception:
            dead.append(player)

    for player in dead:
        if player in rooms[code]["players"]:
            rooms[code]["players"].remove(player)


@app.websocket("/ws/{code}")
async def websocket_endpoint(websocket: WebSocket, code: str):

    await websocket.accept()

    if code not in rooms:
        await websocket.send_json({
            "type": "error",
            "message": "Комната не существует."
        })
        await websocket.close()
        return

    player = None

    try:

        while True:

            data = await websocket.receive_json()

            if data["type"] == "join":

                name = str(data.get("name", "Игрок")).strip()

                if not name:
                    name = "Игрок"

                if len(rooms[code]["players"]) >= 10:

                    await websocket.send_json({
                        "type": "error",
                        "message": "Комната заполнена."
                    })

                    continue

                player = {
                    "name": name,
                    "socket": websocket
                }

                rooms[code]["players"].append(player)

                await send_room(code)

            elif data["type"] == "start":

                if len(rooms[code]["players"]) < 3:

                    await websocket.send_json({
                        "type": "error",
                        "message": "Нужно минимум 3 игрока."
                    })

                    continue

                rooms[code]["started"] = True

                mafia = random.choice(rooms[code]["players"])

                for p in rooms[code]["players"]:

                    role = "МАФИЯ" if p == mafia else "МИРНЫЙ"

                    await p["socket"].send_json({
                        "type": "game_started",
                        "role": role
                    })

    except WebSocketDisconnect:

        pass

    except Exception:

        pass

    finally:

        if player and code in rooms:

            if player in rooms[code]["players"]:
                rooms[code]["players"].remove(player)

            await send_room(code)

        if code in rooms and not rooms[code]["players"]:
            del rooms[code]


if __name__ == "__main__":

    import uvicorn

    port = int(os.environ.get("PORT", 8001))

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )
