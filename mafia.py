import os
import random
import string
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse


app = FastAPI()

rooms = {}


# =========================
# HTML + CSS + JAVASCRIPT
# =========================

HTML = r"""
<!DOCTYPE html>
<html lang="ru">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Mafia Online</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    min-height: 100vh;

    font-family: Arial, sans-serif;

    color: white;

    background:
        radial-gradient(
            circle at top,
            #3b214d,
            #11111b 45%,
            #07070c 100%
        );
}

.container {
    width: 100%;
    max-width: 900px;

    margin: auto;

    padding: 25px;
}

.logo {
    text-align: center;

    font-size: 42px;
    font-weight: 900;

    letter-spacing: 6px;

    margin-bottom: 25px;

    text-shadow:
        0 0 10px #9f4dff,
        0 0 30px #9f4dff;
}

.card {
    background: rgba(20, 20, 32, 0.95);

    border: 1px solid #403b58;

    border-radius: 22px;

    padding: 25px;

    box-shadow:
        0 20px 60px rgba(0,0,0,.45);
}

.hidden {
    display: none !important;
}

input {
    width: 100%;

    padding: 14px;

    margin-bottom: 12px;

    border-radius: 12px;

    border: 1px solid #4b4666;

    background: #0e0e18;

    color: white;

    font-size: 16px;

    outline: none;
}

input:focus {
    border-color: #a65cff;
}

button {
    width: 100%;

    padding: 14px;

    margin-top: 8px;

    border: 0;

    border-radius: 12px;

    background:
        linear-gradient(
            135deg,
            #7b3cff,
            #c63d8f
        );

    color: white;

    font-size: 16px;

    font-weight: bold;

    cursor: pointer;

    transition: .2s;
}

button:hover {
    transform: translateY(-2px);

    filter: brightness(1.15);
}

button:disabled {
    opacity: .4;

    cursor: not-allowed;

    transform: none;
}

.secondary {
    background: #292b40;
}

.danger {
    background:
        linear-gradient(
            135deg,
            #9d263e,
            #e33c54
        );
}

.row {
    display: grid;

    grid-template-columns:
        repeat(2, 1fr);

    gap: 10px;
}

.room-code {
    text-align: center;

    font-size: 42px;

    font-weight: 900;

    letter-spacing: 8px;

    color: #d4b4ff;

    margin: 15px;
}

.players {
    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(170px, 1fr)
        );

    gap: 10px;

    margin-top: 15px;
}

.player {
    background: #202236;

    border: 1px solid #393d5a;

    border-radius: 14px;

    padding: 14px;
}

.player.dead {
    opacity: .35;

    text-decoration: line-through;
}

.phase {
    text-align: center;

    font-size: 28px;

    font-weight: 900;

    margin-bottom: 5px;
}

.timer {
    text-align: center;

    font-size: 65px;

    font-weight: 900;

    color: #ff719f;

    text-shadow:
        0 0 20px #ff719f;
}

.role {
    text-align: center;

    padding: 16px;

    margin: 15px 0;

    border-radius: 15px;

    background: #211a31;

    font-size: 22px;

    font-weight: bold;
}

.message {
    text-align: center;

    min-height: 25px;

    color: #bfc3dd;
}

.log {
    margin-top: 20px;

    padding: 15px;

    background: #0d0e17;

    border-radius: 12px;

    min-height: 40px;

    color: #bfc3dd;
}

@media(max-width:600px) {

    .logo {
        font-size: 28px;
    }

    .row {
        grid-template-columns: 1fr;
    }

    .timer {
        font-size: 50px;
    }

}

</style>

</head>


<body>


<div class="container">


<div class="logo">
☠ MAFIA ONLINE
</div>


<!-- ================= MENU ================= -->

<div id="menu" class="card">

<h2>
Добро пожаловать
</h2>

<p class="message">
Создай комнату или присоединись к друзьям.
</p>


<input
    id="name"
    maxlength="18"
    placeholder="Твоё имя"
>


<div class="row">

<button onclick="createRoom()">
Создать комнату
</button>

<button
    class="secondary"
    onclick="joinRoom()"
>
Войти в комнату
</button>

</div>


<input
    id="room"
    maxlength="4"
    placeholder="Код комнаты"
>


<div
    id="menuMessage"
    class="message"
></div>

</div>


<!-- ================= GAME ================= -->

<div
    id="game"
    class="card hidden"
>


<div
    id="phase"
    class="phase"
>
Лобби
</div>


<div
    id="timer"
    class="timer"
>
—
</div>


<div
    id="role"
    class="role"
>
Роль пока неизвестна
</div>


<div
    id="roomDisplay"
    class="room-code"
>
----
</div>


<div
    id="message"
    class="message"
>
</div>


<h3>
Игроки
</h3>


<div
    id="players"
    class="players"
>
</div>


<div
    id="actions"
>
</div>


<div
    id="log"
    class="log"
>
</div>


</div>


</div>


<script>


// ========================================
// ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
// ========================================

let socket = null;

let myName = "";

let currentRoom = "";

let lastAnnouncement = "";


// ========================================
// ВСПОМОГАТЕЛЬНЫЕ
// ========================================

function $(id) {

    return document.getElementById(id);

}


// ========================================
// ЗВУК
// ========================================

function playSound(type) {

    try {

        const AudioContext =
            window.AudioContext ||
            window.webkitAudioContext;

        const audio =
            new AudioContext();

        const oscillator =
            audio.createOscillator();

        const gain =
            audio.createGain();


        oscillator.connect(gain);

        gain.connect(audio.destination);


        let frequency = 500;

        let duration = 0.15;


        if (type === "click") {

            frequency = 650;

            duration = 0.08;

        }


        if (type === "night") {

            frequency = 180;

            duration = 0.5;

        }


        if (type === "day") {

            frequency = 700;

            duration = 0.35;

        }


        if (type === "death") {

            frequency = 90;

            duration = 0.8;

        }


        if (type === "vote") {

            frequency = 450;

            duration = 0.25;

        }


        if (type === "win") {

            frequency = 900;

            duration = 0.8;

        }


        oscillator.frequency.value =
            frequency;


        gain.gain.value =
            0.04;


        oscillator.start();


        gain.gain.exponentialRampToValueAtTime(
            0.001,
            audio.currentTime + duration
        );


        oscillator.stop(
            audio.currentTime + duration
        );


    } catch (error) {

        console.log(
            "Звук недоступен"
        );

    }

}


// ========================================
// ГОЛОС
// ========================================

function speak(text) {

    if (
        !("speechSynthesis" in window)
    ) {

        return;

    }


    speechSynthesis.cancel();


    const voice =
        new SpeechSynthesisUtterance(
            text
        );


    voice.lang = "ru-RU";

    voice.rate = 0.9;

    voice.pitch = 0.8;


    speechSynthesis.speak(
        voice
    );

}


// ========================================
// СОЗДАТЬ КОМНАТУ
// ========================================

function createRoom() {

    myName =
        $("name")
        .value
        .trim();


    if (!myName) {

        $("menuMessage")
            .textContent =
            "Сначала введи имя.";

        return;

    }


    fetch("/create")

        .then(
            response =>
                response.json()
        )

        .then(
            data => {

                currentRoom =
                    data.room;


                $("room")
                    .value =
                    currentRoom;


                connect();


            }
        )

        .catch(
            () => {

                $("menuMessage")
                    .textContent =
                    "Ошибка создания комнаты.";

            }
        );

}


// ========================================
// ВОЙТИ
// ========================================

function joinRoom() {

    myName =
        $("name")
        .value
        .trim();


    currentRoom =
        $("room")
        .value
        .trim()
        .toUpperCase();


    if (!myName) {

        $("menuMessage")
            .textContent =
            "Введи имя.";

        return;

    }


    if (!currentRoom) {

        $("menuMessage")
            .textContent =
            "Введи код комнаты.";

        return;

    }


    connect();

}


// ========================================
// WEBSOCKET
// ========================================

function connect() {

    const protocol =
        location.protocol === "https:"
            ? "wss://"
            : "ws://";


    socket =
        new WebSocket(
            protocol +
            location.host +
            "/ws"
        );


    socket.onopen =
        function() {

            socket.send(
                JSON.stringify({

                    type: "join",

                    name: myName,

                    room: currentRoom

                })
            );

        };


    socket.onmessage =
        function(event) {

            const data =
                JSON.parse(
                    event.data
                );


            if (
                data.type === "error"
            ) {

                $("menuMessage")
                    .textContent =
                    data.message;

                return;

            }


            if (
                data.type === "state"
            ) {

                render(data);

            }

        };


    socket.onclose =
        function() {

            $("message")
                .textContent =
                "Соединение закрыто.";

        };

}


// ========================================
// ОТПРАВКА
// ========================================

function send(data) {

    if (
        socket &&
        socket.readyState === 1
    ) {

        socket.send(
            JSON.stringify(data)
        );

    }

}


// ========================================
// ОТРИСОВКА
// ========================================

function render(data) {

    $("menu")
        .classList
        .add("hidden");


    $("game")
        .classList
        .remove("hidden");


    $("roomDisplay")
        .textContent =
        data.room;


    $("phase")
        .textContent =
        data.phase;


    $("timer")
        .textContent =
        data.time > 0
            ? data.time + " сек"
            : "—";


    if (data.role) {

        $("role")
            .textContent =
            "Твоя роль: " +
            data.role;

    }


    $("players")
        .innerHTML =


        data.players
            .map(

                player => `

                <div
                    class="
                        player
                        ${
                            player.alive
                                ? ""
                                : "dead"
                        }
                    "
                >

                    👤
                    ${escapeHtml(
                        player.name
                    )}

                    <br>

                    <small>

                    ${
                        player.alive
                            ? "🟢 Жив"
                            : "💀 Мёртв"
                    }

                    ${
                        player.name ===
                        data.host
                            ? " 👑 Хост"
                            : ""
                    }

                    </small>

                </div>

                `

            )
            .join("");


    // ====================================
    // ФАЗА
    // ====================================

    if (
        data.announcement &&
        data.announcement !==
        lastAnnouncement
    ) {

        lastAnnouncement =
            data.announcement;


        $("message")
            .textContent =
            data.announcement;


        if (
            data.phase ===
            "🌙 НОЧЬ — МАФИЯ"
        ) {

            playSound("night");

            speak(
                "Город засыпает. Мафия просыпается."
            );

        }


        else if (
            data.phase ===
            "☀️ ДЕНЬ"
        ) {

            playSound("day");

            speak(
                "Город просыпается."
            );

        }


        else if (
            data.announcement
                .toLowerCase()
                .includes("убит")
        ) {

            playSound("death");

            speak(
                data.announcement
            );

        }


        else if (
            data.phase ===
            "🗳️ ГОЛОСОВАНИЕ"
        ) {

            playSound("vote");

            speak(
                "Началось голосование."
            );

        }


        else if (
            data.phase ===
            "🏆 ПОБЕДА"
        ) {

            playSound("win");

            speak(
                data.announcement
            );

        }

    }


    // ====================================
    // КНОПКИ
    // ====================================

    let html = "";


    // Хост начинает игру

    if (
        data.phase === "ЛОББИ" &&
        data.host === myName
    ) {

        if (
            data.players.length >= 4
        ) {

            html += `

            <button
                onclick="startGame()"
            >
                🎮 НАЧАТЬ ИГРУ
            </button>

            `;

        }

        else {

            html += `

            <p class="message">

            Нужно минимум 4 игрока.

            </p>

            `;

        }

    }


    // ====================================
    // МАФИЯ
    // ====================================

    if (
        data.phase ===
        "🌙 НОЧЬ — МАФИЯ" &&
        data.role === "Мафия" &&
        data.alive.includes(myName)
    ) {

        html += `
        <h3>
        🔪 Выбери жертву
        </h3>
        `;


        data.players
            .filter(
                player =>
                    player.alive &&
                    player.name !==
                    myName
            )
            .forEach(

                player => {

                    html += `

                    <button
                        class="danger"
                        onclick="killPlayer(
                            '${escapeJs(
                                player.name
                            )}'
                        )"
                    >

                    🔪 Убить
                    ${escapeHtml(
                        player.name
                    )}

                    </button>

                    `;

                }

            );

    }


    // ====================================
    // ГОЛОСОВАНИЕ
    // ====================================

    if (
        data.phase ===
        "🗳️ ГОЛОСОВАНИЕ" &&
        data.alive.includes(myName)
    ) {

        html += `

        <h3>
        🗳️ За кого голосовать?
        </h3>

        `;


        data.players
            .filter(
                player =>
                    player.alive &&
                    player.name !==
                    myName
            )
            .forEach(

                player => {

                    html += `

                    <button
                        class="secondary"
                        onclick="vote(
                            '${escapeJs(
                                player.name
                            )}'
                        )"
                    >

                    🗳️
                    ${escapeHtml(
                        player.name
                    )}

                    </button>

                    `;

                }

            );

    }


    $("actions")
        .innerHTML =
        html;


    if (
        data.log &&
        data.log.length
    ) {

        $("log")
            .innerHTML =
            data.log
                .map(
                    x =>
                        "<div>" +
                        escapeHtml(x) +
                        "</div>"
                )
                .join("");

    }

}


// ========================================
// НАЧАТЬ ИГРУ
// ========================================

function startGame() {

    playSound("click");


    send({

        type: "start"

    });

}


// ========================================
// УБИЙСТВО
// ========================================

function killPlayer(name) {

    playSound("click");


    send({

        type: "kill",

        target: name

    });

}


// ========================================
// ГОЛОС
// ========================================

function vote(name) {

    playSound("click");


    send({

        type: "vote",

        target: name

    });

}


// ========================================
// ЗАЩИТА HTML
// ========================================

function escapeHtml(text) {

    return String(text)
        .replace(
            /[&<>"']/g,

            function(char) {

                return {

                    "&": "&amp;",
                    "<": "&lt;",
                    ">": "&gt;",
                    '"': "&quot;",
                    "'": "&#039;"

                }[char];

            }
        );

}


function escapeJs(text) {

    return String(text)
        .replace(
            /\\/g,
            "\\\\"
        )
        .replace(
            /'/g,
            "\\'"
        );

}

</script>

</body>
</html>
"""


# ========================================
# СОЗДАНИЕ КОДА КОМНАТЫ
# ========================================

def generate_room_code():

    while True:

        code = "".join(
            random.choice(
                string.digits
            )
            for _ in range(4)
        )

        if code not in rooms:

            return code


# ========================================
# СОСТОЯНИЕ КОМНАТЫ
# ========================================

def get_state(room, player_name):

    player =
        room["players"].get(
            player_name
        )


    current_time =
        asyncio.get_running_loop().time()


    remaining = 0


    if room["ends"]:

        remaining = max(
            0,
            int(
                room["ends"] -
                current_time
            )
        )


    return {

        "type": "state",

        "room": room["code"],

        "host": room["host"],

        "phase": room["phase"],

        "time": remaining,

        "role":
            player.get("role")
            if player
            else None,

        "alive":
            [
                p["name"]

                for p in
                room["players"].values()

                if p["alive"]
            ],

        "players":
            [
                {

                    "name": p["name"],

                    "alive":
                        p["alive"]

                }

                for p in
                room["players"].values()
            ],

        "announcement":
            room["announcement"],

        "log":
            room["log"]

    }


# ========================================
# ОТПРАВИТЬ ВСЕМ
# ========================================

async def broadcast(room):

    for websocket, player_name in list(
        room["connections"].items()
    ):

        try:

            await websocket.send_json(
                get_state(
                    room,
                    player_name
                )
            )

        except Exception:

            room["connections"].pop(
                websocket,
                None
            )


# ========================================
# ИГРОВОЙ ЦИКЛ
# ========================================

async def game_loop(room):

    while room["phase"] != "🏆 ПОБЕДА":

        now =
            asyncio.get_running_loop().time()


        # ================================
        # ТАЙМЕР
        # ================================

        if room["ends"] > now:

            await broadcast(room)

            await asyncio.sleep(
                min(
                    1,
                    room["ends"] - now
                )
            )

            continue


        # ================================
        # ЗАКОНЧИЛАСЬ НОЧЬ
        # ================================

        if room["phase"] == \
                "🌙 НОЧЬ — МАФИЯ":

            target =
                room["night_target"]


            if target:

                if (
                    target in
                    room["players"]
                ):

                    victim =
                        room["players"][
                            target
                        ]


                    if victim["alive"]:

                        victim["alive"] = False


                        room["announcement"] =
                            "Ночью был убит " +
                            target + "."


                        room["log"].append(
                            room["announcement"]
                        )

            else:

                room["announcement"] =
                    "Мафия никого не убила."


            room["night_target"] = None


            # Проверяем победу

            if check_winner(room):

                await broadcast(room)

                return


            # День

            room["phase"] = "☀️ ДЕНЬ"


            room["ends"] =
                asyncio.get_running_loop().time() + 8


            room["announcement"] =
                "Город просыпается."


            await broadcast(room)


            await asyncio.sleep(8)


            # Голосование

            room["phase"] =
                "🗳️ ГОЛОСОВАНИЕ"


            room["ends"] =
                asyncio.get_running_loop().time() + 60


            room["votes"] = {}


            room["announcement"] =
                "Началось голосование. У вас 60 секунд."


        # ================================
        # ЗАКОНЧИЛОСЬ ГОЛОСОВАНИЕ
        # ================================

        elif room["phase"] == \
                "🗳️ ГОЛОСОВАНИЕ":

            counts = {}


            for target in room["votes"].values():

                counts[target] =
                    counts.get(
                        target,
                        0
                    ) + 1


            if counts:

                victim =
                    max(
                        counts,
                        key=counts.get
                    )


                if (
                    victim in
                    room["players"]
                ):

                    room["players"][
                        victim
                    ]["alive"] = False


                    room["announcement"] =
                        victim +
                        " был изгнан голосованием."


                    room["log"].append(
                        room["announcement"]
                    )

            else:

                room["announcement"] =
                    "Никто не был изгнан."


            room["votes"] = {}


            # Проверяем победу

            if check_winner(room):

                await broadcast(room)

                return


            # Следующая ночь

            room["phase"] =
                "🌙 НОЧЬ — МАФИЯ"


            room["ends"] =
                asyncio.get_running_loop().time() + 15


            room["announcement"] =
                "Город засыпает. Мафия просыпается."


            await broadcast(room)


# ========================================
# ПРОВЕРКА ПОБЕДЫ
# ========================================

def check_winner(room):

    mafia_count = 0

    citizen_count = 0


    for player in room["players"].values():

        if not player["alive"]:

            continue


        if player["role"] == "Мафия":

            mafia_count += 1

        else:

            citizen_count += 1


    if mafia_count == 0:

        room["phase"] =
            "🏆 ПОБЕДА"

        room["ends"] = 0

        room["announcement"] =
            "Мирные жители победили!"


        room["log"].append(
            "🏆 Мирные жители победили!"
        )

        return True


    if mafia_count >= citizen_count:

        room["phase"] =
            "🏆 ПОБЕДА"

        room["ends"] = 0

        room["announcement"] =
            "Мафия победила!"


        room["log"].append(
            "🏆 Мафия победила!"
        )

        return True


    return False


# ========================================
# ГЛАВНАЯ
# ========================================

@app.get("/")
async def home():

    return HTMLResponse(
        HTML
    )


# ========================================
# СОЗДАТЬ КОМНАТУ
# ========================================

@app.get("/create")
async def create_room():

    code =
        generate_room_code()


    rooms[code] = {

        "code": code,

        "host": None,

        "players": {},

        "connections": {},

        "phase": "ЛОББИ",

        "ends": 0,

        "announcement":
            "Ожидание игроков...",

        "night_target": None,

        "votes": {},

        "log": [],

        "game_task": None

    }


    return {

        "room": code

    }


# ========================================
# WEBSOCKET
# ========================================

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket
):

    await websocket.accept()


    room = None

    player_name = None


    try:

        first =
            await websocket.receive_json()


        if first.get("type") != "join":

            return


        player_name =
            str(
                first.get(
                    "name",
                    ""
                )
            ).strip()


        room_code =
            str(
                first.get(
                    "room",
                    ""
                )
            ).upper()


        if not player_name:

            await websocket.send_json({

                "type": "error",

                "message":
                    "Введи имя."

            })

            return


        if room_code not in rooms:

            await websocket.send_json({

                "type": "error",

                "message":
                    "Комната не найдена."

            })

            return


        room =
            rooms[room_code]


        if room["phase"] != "ЛОББИ":

            await websocket.send_json({

                "type": "error",

                "message":
                    "Игра уже началась."

            })

            return


        if player_name in room["players"]:

            await websocket.send_json({

                "type": "error",

                "message":
                    "Это имя уже занято."

            })

            return


        if len(room["players"]) >= 12:

            await websocket.send_json({

                "type": "error",

                "message":
                    "Комната заполнена."

            })

            return


        # Добавляем игрока

        room["players"][
            player_name
        ] = {

            "name":
                player_name,

            "alive":
                True,

            "role":
                None

        }


        room["connections"][
            websocket
        ] = player_name


        # Первый игрок — хост

        if room["host"] is None:

            room["host"] =
                player_name


        await broadcast(room)


        # =================================
        # ПОЛУЧЕНИЕ КОМАНД
        # =================================

        while True:

            data =
                await websocket.receive_json()


            command =
                data.get("type")


            # =============================
            # START
            # =============================

            if command == "start":

                if (
                    player_name !=
                    room["host"]
                ):

                    continue


                if (
                    room["phase"] !=
                    "ЛОББИ"
                ):

                    continue


                if len(
                    room["players"]
                ) < 4:

                    await websocket.send_json({

                        "type":
                            "error",

                        "message":
                            "Нужно минимум 4 игрока."

                    })

                    continue


                # Выбираем мафию

                names =
                    list(
                        room["players"]
                    )


                random.shuffle(names)


                mafia_count =
                    max(
                        1,
                        len(names) // 4
                    )


                for index, name in enumerate(
                    names
                ):

                    if index < mafia_count:

                        room["players"][
                            name
                        ]["role"] = \
                            "Мафия"

                    else:

                        room["players"][
                            name
                        ]["role"] = \
                            "Мирный"


                room["phase"] =
                    "🌙 НОЧЬ — МАФИЯ"


                room["ends"] =
                    asyncio.get_running_loop().time() + 15


                room["announcement"] =
                    "Город засыпает. Мафия просыпается."


                room["log"].append(
                    "Игра началась."
                )


                # Запускаем игровой цикл

                room["game_task"] =
                    asyncio.create_task(
                        game_loop(room)
                    )


                await broadcast(room)


            # =============================
            # УБИЙСТВО
            # =============================

            elif command == "kill":

                if room["phase"] != \
                        "🌙 НОЧЬ — МАФИЯ":

                    continue


                player =
                    room["players"].get(
                        player_name
                    )


                target_name =
                    str(
                        data.get(
                            "target",
                            ""
                        )
                    )


                if not player:

                    continue


                if not player["alive"]:

                    continue


                if player["role"] != \
                        "Мафия":

                    continue


                if target_name not in \
                        room["players"]:

                    continue


                if target_name == \
                        player_name:

                    continue


                target =
                    room["players"][
                        target_name
                    ]


                if not target["alive"]:

                    continue


                room["night_target"] =
                    target_name


                room["announcement"] =
                    "Мафия выбрала жертву."


                await broadcast(room)


            # =============================
            # ГОЛОСОВАНИЕ
            # =============================

            elif command == "vote":

                if room["phase"] != \
                        "🗳️ ГОЛОСОВАНИЕ":

                    continue


                player =
                    room["players"].get(
                        player_name
                    )


                target_name =
                    str(
                        data.get(
                            "target",
                            ""
                        )
                    )


                if not player:

                    continue


                if not player["alive"]:

                    continue


                if target_name not in \
                        room["players"]:

                    continue


                target =
                    room["players"][
                        target_name
                    ]


                if not target["alive"]:

                    continue


                if target_name == \
                        player_name:

                    continue


                room["votes"][
                    player_name
                ] = target_name


                room["announcement"] =
                    player_name +
                    " проголосовал."


                await broadcast(room)


    except WebSocketDisconnect:

        pass


    except Exception as error:

        print(
            "WebSocket error:",
            error
        )


    finally:

        if (
            room is not None
            and
            player_name is not None
        ):

            room["connections"].pop(
                websocket,
                None
            )


            # В лобби игрок полностью выходит

            if (
                room["phase"] ==
                "ЛОББИ"
                and
                player_name in
                room["players"]
            ):

                del room["players"][
                    player_name
                ]


                # Передаём хоста

                if (
                    room["host"] ==
                    player_name
                ):

                    if room["players"]:

                        room["host"] =
                            next(
                                iter(
                                    room["players"]
                                )
                            )

                    else:

                        room["host"] = None


            await broadcast(room)


# ========================================
# ЛОКАЛЬНЫЙ ЗАПУСК
# ========================================

if __name__ == "__main__":

    import uvicorn


    port =
        int(
            os.environ.get(
                "PORT",
                "8001"
            )
        )


    uvicorn.run(

        app,

        host="0.0.0.0",

        port=port

    )
