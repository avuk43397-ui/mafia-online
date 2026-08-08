import os
import random
import string
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

rooms = {}

HTML = r"""
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MAFIA ONLINE</title>

<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background:
        radial-gradient(circle at top, #22283a 0%, #0c0e15 55%, #07080d 100%);
    color: white;
    min-height: 100vh;
}

.app {
    width: min(1100px, 94%);
    margin: 0 auto;
    padding: 28px 0 40px;
}

header {
    text-align: center;
    margin-bottom: 24px;
}

.logo {
    font-size: 42px;
    font-weight: 900;
    letter-spacing: 6px;
    text-shadow: 0 0 25px #ff3158;
}

.subtitle {
    color: #9da4b8;
}

.card {
    background: rgba(20, 23, 34, 0.86);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 22px;
    padding: 22px;
    box-shadow: 0 18px 50px rgba(0,0,0,0.35);
    backdrop-filter: blur(12px);
}

.hidden {
    display: none !important;
}

.row {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

input {
    flex: 1;
    min-width: 180px;
    background: #0d1018;
    color: white;
    border: 1px solid #303646;
    border-radius: 13px;
    padding: 14px 16px;
    outline: none;
}

input:focus {
    border-color: #ff3158;
    box-shadow: 0 0 0 3px rgba(255,49,88,0.12);
}

button {
    border: 0;
    border-radius: 13px;
    padding: 13px 18px;
    font-weight: 800;
    cursor: pointer;
    color: white;
    background: linear-gradient(135deg, #ff3158, #a51f42);
    transition: 0.18s;
    box-shadow: 0 8px 22px rgba(255,49,88,0.2);
}

button:hover {
    transform: translateY(-2px);
}

button.secondary {
    background: #252a39;
    box-shadow: none;
}

button:disabled {
    opacity: 0.45;
    cursor: not-allowed;
    transform: none;
}

.topbar {
    display: flex;
    justify-content: space-between;
    gap: 14px;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 16px;
}

.room-code {
    font-size: 28px;
    font-weight: 900;
    letter-spacing: 5px;
}

.phase {
    font-size: 18px;
    font-weight: 800;
}

.timer {
    font-size: 42px;
    font-weight: 900;
    min-width: 90px;
    text-align: center;
}

.timer.warn {
    color: #ffb020;
}

.timer.danger {
    color: #ff3158;
}

.announcement {
    margin: 18px 0;
    padding: 18px;
    border-radius: 16px;
    background: linear-gradient(
        135deg,
        rgba(255,49,88,0.14),
        rgba(255,255,255,0.03)
    );
    border: 1px solid rgba(255,49,88,0.2);
    font-size: 18px;
}

.grid {
    display: grid;
    grid-template-columns: 1.15fr 0.85fr;
    gap: 16px;
}

.players {
    display: grid;
    grid-template-columns: repeat(
        auto-fill,
        minmax(180px, 1fr)
    );
    gap: 10px;
}

.player {
    padding: 14px;
    border-radius: 15px;
    background: #151925;
    border: 1px solid #292e3e;
    display: flex;
    justify-content: space-between;
    gap: 8px;
    align-items: center;
}

.player.dead {
    opacity: 0.42;
    text-decoration: line-through;
}

.badge {
    font-size: 12px;
    color: #aab1c4;
}

.role {
    font-weight: 900;
    margin: 14px 0;
    padding: 16px;
    border-radius: 15px;
    background: #111520;
    border: 1px solid #343a4c;
}

.role.mafia {
    border-color: #ff3158;
    color: #ff718c;
}

.role.citizen {
    border-color: #5f8cff;
    color: #8eaeff;
}

.actions {
    display: flex;
    gap: 9px;
    flex-wrap: wrap;
    margin-top: 15px;
}

.target-btn {
    width: 100%;
    text-align: left;
    background: #202534;
    box-shadow: none;
}

.log {
    max-height: 320px;
    overflow: auto;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.log div {
    padding: 10px 12px;
    background: #10131c;
    border-radius: 11px;
    color: #b9bfd0;
}

.small {
    font-size: 13px;
    color: #8f96aa;
}

.error {
    margin-top: 12px;
    color: #ff718c;
    min-height: 20px;
}

@media (max-width: 800px) {
    .grid {
        grid-template-columns: 1fr;
    }

    .logo {
        font-size: 32px;
    }
}
</style>
</head>

<body>

<div class="app">

<header>
    <div class="logo">MAFIA</div>
    <div class="subtitle">
        ONLINE • MULTIPLAYER
    </div>
</header>

<section id="home" class="card">

    <h2>Войти в игру</h2>

    <div class="row">

        <input
            id="name"
            maxlength="18"
            placeholder="Твоё имя"
        >

        <input
            id="room"
            maxlength="4"
            placeholder="Код комнаты"
        >

    </div>

    <div class="actions">

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

    <div
        id="homeError"
        class="error"
    ></div>

</section>


<section
    id="game"
    class="hidden"
>

    <div class="card">

        <div class="topbar">

            <div>

                <div class="small">
                    КОМНАТА
                </div>

                <div
                    id="roomCode"
                    class="room-code"
                >
                    ----
                </div>

            </div>


            <div>

                <div
                    id="phase"
                    class="phase"
                >
                    ЛОББИ
                </div>

                <div
                    id="myRole"
                    class="role"
                >
                    Роль пока не назначена
                </div>

            </div>


            <div
                id="timer"
                class="timer"
            >
                --
            </div>

        </div>


        <div
            id="announcement"
            class="announcement"
        >
            Ожидание игроков...
        </div>


        <div class="grid">

            <div>

                <div class="card">

                    <h3>
                        Игроки
                    </h3>

                    <div
                        id="players"
                        class="players"
                    ></div>


                    <div
                        id="hostControls"
                        class="actions hidden"
                    >

                        <button
                            onclick="startGame()"
                        >
                            Начать игру
                        </button>

                    </div>


                    <div
                        id="actions"
                        class="actions"
                    ></div>

                </div>

            </div>


            <div>

                <div class="card">

                    <h3>
                        События
                    </h3>

                    <div
                        id="log"
                        class="log"
                    ></div>

                </div>

            </div>

        </div>

    </div>

</section>

</div>


<script>

let ws = null;
let state = null;
let lastAnnouncement = "";


function el(id) {
    return document.getElementById(id);
}


function showHomeError(text) {
    el("homeError").textContent = text || "";
}


function escapeHtml(text) {

    return String(text).replace(
        /[&<>"']/g,
        function(c) {

            return {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#039;"
            }[c];

        }
    );
}


function beep(freq = 440, duration = 0.12) {

    try {

        const ctx =
            new (
                window.AudioContext ||
                window.webkitAudioContext
            )();

        const osc =
            ctx.createOscillator();

        const gain =
            ctx.createGain();

        osc.frequency.value = freq;

        gain.gain.value = 0.04;

        osc.connect(gain);

        gain.connect(ctx.destination);

        osc.start();

        osc.stop(
            ctx.currentTime + duration
        );

    } catch (e) {}

}


function speak(text) {

    try {

        if ("speechSynthesis" in window) {

            speechSynthesis.cancel();

            const u =
                new SpeechSynthesisUtterance(
                    text
                );

            u.lang = "ru-RU";
            u.rate = 0.95;
            u.pitch = 0.85;

            speechSynthesis.speak(u);
        }

    } catch (e) {}

}


async function createRoom() {

    showHomeError("");

    try {

        const r =
            await fetch("/create");

        const data =
            await r.json();

        el("room").value =
            data.room;

        joinRoom();

    } catch (e) {

        showHomeError(
            "Не удалось создать комнату."
        );

    }

}


function joinRoom() {

    showHomeError("");

    const name =
        el("name").value.trim();

    const room =
        el("room").value
            .trim()
            .toUpperCase();


    if (!name) {

        showHomeError(
            "Введи имя."
        );

        return;
    }


    if (!/^\d{4}$/.test(room)) {

        showHomeError(
            "Код комнаты должен содержать 4 цифры."
        );

        return;
    }


    if (ws) {
        ws.close();
    }


    const protocol =
        location.protocol === "https:"
            ? "wss"
            : "ws";


    ws =
        new WebSocket(
            `${protocol}://${location.host}/ws`
        );


    ws.onopen = function() {

        ws.send(
            JSON.stringify({
                type: "join",
                name: name,
                room: room
            })
        );

    };


    ws.onmessage = function(event) {

        const data =
            JSON.parse(event.data);


        if (data.type === "error") {

            showHomeError(
                data.message
            );

            return;
        }


        if (data.type === "state") {

            state = data;

            render();

        }

    };


    ws.onerror = function() {

        showHomeError(
            "Ошибка соединения с сервером."
        );

    };

}


function send(data) {

    if (
        ws &&
        ws.readyState === WebSocket.OPEN
    ) {

        ws.send(
            JSON.stringify(data)
        );

    }

}


function startGame() {

    send({
        type: "start"
    });

}


function render() {

    el("home")
        .classList
        .add("hidden");


    el("game")
        .classList
        .remove("hidden");


    el("roomCode").textContent =
        state.room;


    el("phase").textContent =
        state.phase;


    el("announcement").textContent =
        state.announcement || "";


    const timer =
        el("timer");


    timer.textContent =
        state.time > 0
            ? state.time
            : "--";


    timer.className =
        "timer";


    if (
        state.time <= 5 &&
        state.time > 0
    ) {

        timer.classList.add(
            "danger"
        );

    } else if (
        state.time <= 10 &&
        state.time > 0
    ) {

        timer.classList.add(
            "warn"
        );

    }


    const role =
        state.role;


    const roleEl =
        el("myRole");


    if (role === "Мафия") {

        roleEl.textContent =
            "🔪 ТЫ — МАФИЯ";

        roleEl.className =
            "role mafia";

    } else if (
        role === "Мирный"
    ) {

        roleEl.textContent =
            "🕊️ ТЫ — МИРНЫЙ";

        roleEl.className =
            "role citizen";

    } else {

        roleEl.textContent =
            "Роль пока не назначена";

        roleEl.className =
            "role";

    }


    const players =
        el("players");


    players.innerHTML =
        state.players.map(
            function(p) {

                return `
                    <div class="player ${
                        p.alive ? "" : "dead"
                    }">

                        <span>
                            ${escapeHtml(p.name)}
                        </span>

                        <span class="badge">
                            ${
                                p.alive
                                    ? "● жив"
                                    : "✖ выбыл"
                            }
                        </span>

                    </div>
                `;

            }
        ).join("");


    const currentName =
        el("name").value.trim();


    el("hostControls")
        .classList
        .toggle(
            "hidden",
            !(
                state.phase === "ЛОББИ" &&
                state.host === currentName
            )
        );


    const actions =
        el("actions");


    actions.innerHTML = "";


    if (
        state.phase ===
            "🌙 НОЧЬ — МАФИЯ" &&
        role === "Мафия"
    ) {

        const targets =
            state.players.filter(
                function(p) {

                    return (
                        p.alive &&
                        p.name !== currentName
                    );

                }
            );


        if (targets.length) {

            const title =
                document.createElement(
                    "div"
                );

            title.className =
                "small";

            title.textContent =
                "Выбери жертву:";

            actions.appendChild(
                title
            );


            targets.forEach(
                function(p) {

                    const b =
                        document.createElement(
                            "button"
                        );

                    b.className =
                        "target-btn";

                    b.textContent =
                        "🔪 " + p.name;

                    b.onclick =
                        function() {

                            send({
                                type: "kill",
                                target: p.name
                            });

                            beep(
                                180,
                                0.18
                            );

                        };


                    actions.appendChild(b);

                }
            );

        }

    }


    if (
        state.phase ===
            "🗳️ ГОЛОСОВАНИЕ" &&
        state.alive.includes(currentName)
    ) {

        const targets =
            state.players.filter(
                function(p) {

                    return (
                        p.alive &&
                        p.name !== currentName
                    );

                }
            );


        const title =
            document.createElement(
                "div"
            );

        title.className =
            "small";

        title.textContent =
            "За кого голосуешь:";

        actions.appendChild(
            title
        );


        targets.forEach(
            function(p) {

                const b =
                    document.createElement(
                        "button"
                    );

                b.className =
                    "target-btn";

                b.textContent =
                    "🗳️ " + p.name;

                b.onclick =
                    function() {

                        send({
                            type: "vote",
                            target: p.name
                        });

                        beep(
                            520,
                            0.1
                        );

                    };


                actions.appendChild(b);

            }
        );

    }


    const log =
        el("log");


    log.innerHTML =
        (state.log || [])
            .slice()
            .reverse()
            .map(
                function(x) {

                    return `
                        <div>
                            ${escapeHtml(x)}
                        </div>
                    `;

                }
            )
            .join("");


    if (
        state.announcement &&
        state.announcement !==
            lastAnnouncement
    ) {

        lastAnnouncement =
            state.announcement;


        beep(
            state.phase === "🏆 ПОБЕДА"
                ? 700
                : 300,
            0.16
        );


        if (
            state.phase !==
            "ЛОББИ"
        ) {

            speak(
                state.announcement
            );

        }

    }

}

</script>

</body>
</html>
"""


def generate_room_code():

    while True:

        code = "".join(
            random.choice(string.digits)
            for _ in range(4)
        )

        if code not in rooms:

            return code


def get_state(room, player_name):

    player = room["players"].get(
        player_name
    )

    current_time = (
        asyncio
        .get_running_loop()
        .time()
    )

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

        "room":
            room["code"],

        "host":
            room["host"],

        "phase":
            room["phase"],

        "time":
            remaining,

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
                    "alive": p["alive"]
                }
                for p in
                room["players"].values()
            ],

        "announcement":
            room["announcement"],

        "log":
            room["log"]

    }


async def broadcast(room):

    for (
        websocket,
        player_name
    ) in list(
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


async def game_loop(room):

    while (
        room["phase"] !=
        "🏆 ПОБЕДА"
    ):

        now = (
            asyncio
            .get_running_loop()
            .time()
        )


        if room["ends"] > now:

            await broadcast(room)

            await asyncio.sleep(
                min(
                    1,
                    room["ends"] - now
                )
            )

            continue


        # ============================
        # КОНЕЦ НОЧИ
        # ============================

        if (
            room["phase"] ==
            "🌙 НОЧЬ — МАФИЯ"
        ):

            target = (
                room["night_target"]
            )


            if (
                target and
                target in room["players"]
            ):

                victim = (
                    room["players"]
                    [target]
                )


                if victim["alive"]:

                    victim["alive"] = False

                    room["announcement"] = (
                        f"Ночью был убит {target}."
                    )

                    room["log"].append(
                        room["announcement"]
                    )

            else:

                room["announcement"] = (
                    "Мафия никого не убила."
                )


            room["night_target"] = None


            if check_winner(room):

                await broadcast(room)

                return


            # =========================
            # ДЕНЬ
            # =========================

            room["phase"] = "☀️ ДЕНЬ"

            room["ends"] = (
                asyncio
                .get_running_loop()
                .time()
                + 8
            )

            room["announcement"] = (
                "Город просыпается."
            )

            await broadcast(room)

            await asyncio.sleep(8)


            # =========================
            # ГОЛОСОВАНИЕ
            # =========================

            room["phase"] = (
                "🗳️ ГОЛОСОВАНИЕ"
            )

            room["ends"] = (
                asyncio
                .get_running_loop()
                .time()
                + 60
            )

            room["votes"] = {}

            room["announcement"] = (
                "Началось голосование. "
                "У вас 60 секунд."
            )

            await broadcast(room)


        # ============================
        # КОНЕЦ ГОЛОСОВАНИЯ
        # ============================

        elif (
            room["phase"] ==
            "🗳️ ГОЛОСОВАНИЕ"
        ):

            counts = {}


            for target in (
                room["votes"].values()
            ):

                counts[target] = (
                    counts.get(
                        target,
                        0
                    ) + 1
                )


            if counts:

                victim = max(
                    counts,
                    key=counts.get
                )


                if (
                    victim in room["players"]
                    and
                    room["players"]
                    [victim]["alive"]
                ):

                    room["players"][
                        victim
                    ]["alive"] = False

                    room["announcement"] = (
                        f"{victim} "
                        "был изгнан голосованием."
                    )

                    room["log"].append(
                        room["announcement"]
                    )

            else:

                room["announcement"] = (
                    "Никто не был изгнан."
                )


            room["votes"] = {}


            if check_winner(room):

                await broadcast(room)

                return


            # =========================
            # НОВАЯ НОЧЬ
            # =========================

            room["phase"] = (
                "🌙 НОЧЬ — МАФИЯ"
            )

            room["ends"] = (
                asyncio
                .get_running_loop()
                .time()
                + 15
            )

            room["announcement"] = (
                "Город засыпает. "
                "Мафия просыпается."
            )

            await broadcast(room)


def check_winner(room):

    mafia_count = 0
    citizen_count = 0


    for player in (
        room["players"].values()
    ):

        if not player["alive"]:

            continue


        if player["role"] == "Мафия":

            mafia_count += 1

        else:

            citizen_count += 1


    if mafia_count == 0:

        room["phase"] = (
            "🏆 ПОБЕДА"
        )

        room["ends"] = 0

        room["announcement"] = (
            "Мирные жители победили!"
        )

        room["log"].append(
            "🏆 Мирные жители победили!"
        )

        return True


    if mafia_count >= citizen_count:

        room["phase"] = (
            "🏆 ПОБЕДА"
        )

        room["ends"] = 0

        room["announcement"] = (
            "Мафия победила!"
        )

        room["log"].append(
            "🏆 Мафия победила!"
        )

        return True


    return False


@app.get("/")
async def home():

    return HTMLResponse(
        HTML
    )


@app.get("/create")
async def create_room():

    code = generate_room_code()


    rooms[code] = {

        "code":
            code,

        "host":
            None,

        "players":
            {},

        "connections":
            {},

        "phase":
            "ЛОББИ",

        "ends":
            0,

        "announcement":
            "Ожидание игроков...",

        "night_target":
            None,

        "votes":
            {},

        "log":
            [],

        "game_task":
            None

    }


    return {
        "room": code
    }


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket
):

    await websocket.accept()


    room = None

    player_name = None


    try:

        first = (
            await websocket
            .receive_json()
        )


        if first.get("type") != "join":

            return


        player_name = str(
            first.get(
                "name",
                ""
            )
        ).strip()


        room_code = str(
            first.get(
                "room",
                ""
            )
        ).upper()


        if not player_name:

            await websocket.send_json({

                "type":
                    "error",

                "message":
                    "Введи имя."

            })

            return


        if room_code not in rooms:

            await websocket.send_json({

                "type":
                    "error",

                "message":
                    "Комната не найдена."

            })

            return


        room = rooms[
            room_code
        ]


        if room["phase"] != "ЛОББИ":

            await websocket.send_json({

                "type":
                    "error",

                "message":
                    "Игра уже началась."

            })

            return


        if player_name in room["players"]:

            await websocket.send_json({

                "type":
                    "error",

                "message":
                    "Это имя уже занято."

            })

            return


        if len(
            room["players"]
        ) >= 12:

            await websocket.send_json({

                "type":
                    "error",

                "message":
                    "Комната заполнена."

            })

            return


        # =========================
        # ДОБАВЛЯЕМ ИГРОКА
        # =========================

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

            room["host"] = (
                player_name
            )


        await broadcast(room)


        # =========================
        # КОМАНДЫ
        # =========================

        while True:

            data = (
                await websocket
                .receive_json()
            )


            command = data.get(
                "type"
            )


            # =====================
            # START
            # =====================

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


                # Выбираем роли

                names = list(
                    room["players"]
                )


                random.shuffle(
                    names
                )


                mafia_count = max(
                    1,
                    len(names) // 4
                )


                for (
                    index,
                    name
                ) in enumerate(names):

                    if index < mafia_count:

                        room["players"][
                            name
                        ]["role"] = (
                            "Мафия"
                        )

                    else:

                        room["players"][
                            name
                        ]["role"] = (
                            "Мирный"
                        )


                room["phase"] = (
                    "🌙 НОЧЬ — МАФИЯ"
                )


                room["ends"] = (
                    asyncio
                    .get_running_loop()
                    .time()
                    + 15
                )


                room["announcement"] = (
                    "Город засыпает. "
                    "Мафия просыпается."
                )


                room["log"].append(
                    "Игра началась."
                )


                room["game_task"] = (
                    asyncio.create_task(
                        game_loop(room)
                    )
                )


                await broadcast(room)


            # =====================
            # УБИЙСТВО
            # =====================

            elif command == "kill":

                if (
                    room["phase"] !=
                    "🌙 НОЧЬ — МАФИЯ"
                ):

                    continue


                player = (
                    room["players"]
                    .get(player_name)
                )


                target_name = str(
                    data.get(
                        "target",
                        ""
                    )
                ).strip()


                if not player:

                    continue


                if not player["alive"]:

                    continue


                if player["role"] != "Мафия":

                    continue


                if target_name not in (
                    room["players"]
                ):

                    continue


                if target_name == player_name:

                    continue


                target = (
                    room["players"]
                    [target_name]
                )


                if not target["alive"]:

                    continue


                room["night_target"] = (
                    target_name
                )


                room["announcement"] = (
                    "Мафия выбрала жертву."
                )


                await broadcast(room)


            # =====================
            # ГОЛОСОВАНИЕ
            # =====================

            elif command == "vote":

                if (
                    room["phase"] !=
                    "🗳️ ГОЛОСОВАНИЕ"
                ):

                    continue


                player = (
                    room["players"]
                    .get(player_name)
                )


                target_name = str(
                    data.get(
                        "target",
                        ""
                    )
                ).strip()


                if not player:

                    continue


                if not player["alive"]:

                    continue


                if target_name not in (
                    room["players"]
                ):

                    continue


                target = (
                    room["players"]
                    [target_name]
                )


                if not target["alive"]:

                    continue


                if target_name == player_name:

                    continue


                room["votes"][
                    player_name
                ] = target_name


                room["announcement"] = (
                    f"{player_name} "
                    "проголосовал."
                )


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


            # В лобби игрок выходит

            if (
                room["phase"] == "ЛОББИ"
                and
                player_name in room["players"]
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

                        room["host"] = next(
                            iter(
                                room["players"]
                            )
                        )

                    else:

                        room["host"] = None


            await broadcast(room)


# ============================
# ЛОКАЛЬНЫЙ ЗАПУСК
# ============================

if __name__ == "__main__":

    import uvicorn


    port = int(
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
