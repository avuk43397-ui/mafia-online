import os
import random
import string
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

rooms = {}


# ============================================================
# HTML
# ============================================================

HTML = r"""
<!DOCTYPE html>
<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>Мафия</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    min-height: 100vh;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background:
        radial-gradient(
            circle at top,
            #29203d,
            #100d18 60%,
            #08070c
        );

    color: white;

    padding: 25px;
}

.container {
    max-width: 1100px;
    margin: auto;
}

h1 {
    text-align: center;
    margin-bottom: 25px;
}

.card {
    background: rgba(25, 21, 35, 0.95);

    border: 1px solid rgba(255,255,255,0.08);

    border-radius: 18px;

    padding: 20px;

    box-shadow:
        0 15px 50px rgba(0,0,0,0.35);
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

    min-width: 200px;

    padding: 14px 16px;

    border-radius: 12px;

    border: 1px solid #3a3348;

    background: #15121d;

    color: white;

    outline: none;

    font-size: 15px;
}

input:focus {
    border-color: #8b5cf6;
}

button {
    border: none;

    border-radius: 12px;

    padding: 13px 18px;

    background: #7c3aed;

    color: white;

    font-weight: bold;

    cursor: pointer;

    transition:
        transform 0.15s,
        opacity 0.15s;
}

button:hover {
    transform: translateY(-2px);
    opacity: 0.9;
}

button:active {
    transform: translateY(0);
}

.secondary {
    background: #302a3c;
}

.danger {
    background: #dc2626;
}

.success {
    background: #059669;
}

.actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 15px;
}

.error {
    color: #ff6b6b;
    margin-top: 12px;
    min-height: 20px;
}

#gameScreen {
    margin-top: 25px;
}

.topbar {
    display: grid;

    grid-template-columns:
        1fr
        1fr
        100px;

    gap: 15px;

    align-items: center;
}

.small {
    color: #9f96ad;
    font-size: 12px;
}

.room-code {
    font-size: 30px;
    font-weight: bold;
    letter-spacing: 5px;
}

.phase {
    font-weight: bold;
    font-size: 17px;
}

.role {
    margin-top: 5px;
    color: #bda9ff;
}

.timer {
    text-align: center;

    font-size: 32px;

    font-weight: bold;

    background: #17131f;

    padding: 12px;

    border-radius: 14px;
}

.announcement {
    margin-top: 20px;

    padding: 16px;

    border-radius: 14px;

    background: rgba(124,58,237,0.15);

    border: 1px solid rgba(124,58,237,0.3);

    text-align: center;

    font-size: 17px;
}

.grid {
    display: grid;

    grid-template-columns:
        1fr
        1fr;

    gap: 20px;

    margin-top: 20px;
}

.players {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.player {
    display: flex;

    justify-content: space-between;

    align-items: center;

    padding: 12px;

    border-radius: 12px;

    background: #17131f;
}

.player.dead {
    opacity: 0.4;
    text-decoration: line-through;
}

.player-name {
    font-weight: bold;
}

.badge {
    padding: 5px 9px;

    border-radius: 8px;

    font-size: 12px;
}

.alive {
    background: #064e3b;
    color: #6ee7b7;
}

.dead-badge {
    background: #4c0519;
    color: #fda4af;
}

.log {
    max-height: 350px;

    overflow-y: auto;
}

.log-item {
    padding: 9px 0;

    border-bottom:
        1px solid
        rgba(255,255,255,0.05);

    color: #c7bfce;
}

.action-button {
    width: 100%;

    margin-top: 7px;
}

.targets {
    margin-top: 15px;
}

.result {
    margin-top: 20px;

    padding: 20px;

    border-radius: 16px;

    background:
        linear-gradient(
            135deg,
            rgba(124,58,237,0.2),
            rgba(0,0,0,0.2)
        );

    border:
        1px solid
        rgba(255,255,255,0.08);
}

.result h2 {
    text-align: center;
}

.role-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.role-player {
    display: flex;

    justify-content: space-between;

    padding: 12px;

    background: #17131f;

    border-radius: 10px;
}

.mafia-role {
    color: #ff6b6b;
    font-weight: bold;
}

.citizen-role {
    color: #6ee7b7;
    font-weight: bold;
}

@media (max-width: 750px) {

    .grid {
        grid-template-columns: 1fr;
    }

    .topbar {
        grid-template-columns: 1fr;
    }

    .timer {
        text-align: left;
    }

}

</style>

</head>


<body>

<div class="container">

<h1>🔪 МАФИЯ</h1>


<div id="homeScreen" class="card">

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

</div>


<div
    id="gameScreen"
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

    </div>


    <div class="grid">

        <div class="card">

            <h3>
                👥 Игроки
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
                    id="startButton"
                    onclick="startGame()"
                >
                    ▶ Начать игру
                </button>

            </div>


            <div
                id="actions"
                class="actions"
            ></div>


            <div
                id="result"
                class="result hidden"
            ></div>

        </div>


        <div class="card">

            <h3>
                📜 События
            </h3>

            <div
                id="log"
                class="log"
            ></div>

        </div>

    </div>

</div>

</div>


<script>

let socket = null;

let myName = "";

let currentState = null;


// ============================================================
// СОЗДАНИЕ КОМНАТЫ
// ============================================================

async function createRoom() {

    const response =
        await fetch("/create");

    const data =
        await response.json();

    document.getElementById("room").value =
        data.room;

    joinRoom();
}


// ============================================================
// ВХОД
// ============================================================

function joinRoom() {

    const name =
        document
        .getElementById("name")
        .value
        .trim();

    const room =
        document
        .getElementById("room")
        .value
        .trim()
        .toUpperCase();

    const error =
        document.getElementById("homeError");

    error.textContent = "";


    if (!name) {

        error.textContent =
            "Введи имя.";

        return;
    }


    if (!room) {

        error.textContent =
            "Введи код комнаты.";

        return;
    }


    myName = name;


    socket = new WebSocket(
        `ws://${location.host}/ws`
    );


    socket.onopen = function() {

        socket.send(
            JSON.stringify({

                type: "join",

                name: name,

                room: room

            })
        );

    };


    socket.onmessage = function(event) {

        const data =
            JSON.parse(event.data);


        if (data.type === "error") {

            error.textContent =
                data.message;

            return;
        }


        if (data.type === "state") {

            currentState = data;

            showGame();

            renderState(data);

        }

    };


    socket.onclose = function() {

        console.log(
            "Соединение закрыто."
        );

    };

}


// ============================================================
// ПОКАЗ ИГРЫ
// ============================================================

function showGame() {

    document
        .getElementById("homeScreen")
        .classList
        .add("hidden");

    document
        .getElementById("gameScreen")
        .classList
        .remove("hidden");

}


// ============================================================
// ОТОБРАЖЕНИЕ СОСТОЯНИЯ
// ============================================================

function renderState(state) {

    document
        .getElementById("roomCode")
        .textContent =
        state.room;


    document
        .getElementById("phase")
        .textContent =
        state.phase;


    document
        .getElementById("timer")
        .textContent =
        state.time > 0
            ? state.time
            : "--";


    document
        .getElementById("announcement")
        .textContent =
        state.announcement;


    // ========================================================
    // МОЯ РОЛЬ
    // ========================================================

    const roleElement =
        document.getElementById("myRole");


    if (state.role) {

        roleElement.textContent =
            "Твоя роль: " +
            state.role;

    } else {

        roleElement.textContent =
            "Роль пока не назначена";

    }


    // ========================================================
    // ИГРОКИ
    // ========================================================

    const playersElement =
        document.getElementById("players");

    playersElement.innerHTML = "";


    state.players.forEach(player => {

        const div =
            document.createElement("div");

        div.className =
            "player " +
            (
                player.alive
                    ? ""
                    : "dead"
            );


        const name =
            document.createElement("span");

        name.className =
            "player-name";

        name.textContent =
            player.name;


        const badge =
            document.createElement("span");

        badge.className =
            "badge " +
            (
                player.alive
                    ? "alive"
                    : "dead-badge"
            );

        badge.textContent =
            player.alive
                ? "Жив"
                : "Мёртв";


        div.appendChild(name);

        div.appendChild(badge);

        playersElement.appendChild(div);

    });


    // ========================================================
    // ХОСТ
    // ========================================================

    const hostControls =
        document
        .getElementById("hostControls");


    if (
        state.host === myName
        &&
        (
            state.phase === "ЛОББИ"
            ||
            state.phase === "🏆 ПОБЕДА"
        )
    ) {

        hostControls
            .classList
            .remove("hidden");

    } else {

        hostControls
            .classList
            .add("hidden");

    }


    const startButton =
        document
        .getElementById("startButton");


    if (state.phase === "🏆 ПОБЕДА") {

        startButton.textContent =
            "🔄 Начать заново";

    } else {

        startButton.textContent =
            "▶ Начать игру";

    }


    // ========================================================
    // ДЕЙСТВИЯ
    // ========================================================

    renderActions(state);


    // ========================================================
    // РЕЗУЛЬТАТ
    // ========================================================

    renderResult(state);


    // ========================================================
    // ЛОГ
    // ========================================================

    const logElement =
        document.getElementById("log");

    logElement.innerHTML = "";


    state.log.forEach(item => {

        const div =
            document.createElement("div");

        div.className =
            "log-item";

        div.textContent =
            item;

        logElement.appendChild(div);

    });

}


// ============================================================
// ДЕЙСТВИЯ
// ============================================================

function renderActions(state) {

    const actions =
        document.getElementById("actions");

    actions.innerHTML = "";


    if (!state.role) {

        return;
    }


    const me =
        state.players.find(
            p => p.name === myName
        );


    if (!me || !me.alive) {

        return;
    }


    // ========================================================
    // УБИЙСТВО МАФИИ
    // ========================================================

    if (
        state.phase === "🌙 НОЧЬ — МАФИЯ"
        &&
        state.role === "Мафия"
    ) {

        const title =
            document.createElement("h3");

        title.textContent =
            "🔪 Выбери жертву";

        actions.appendChild(title);


        state.players.forEach(player => {

            if (
                player.name === myName
                ||
                !player.alive
            ) {

                return;
            }


            const button =
                document.createElement("button");

            button.className =
                "action-button danger";

            button.textContent =
                "Убить: " +
                player.name;


            button.onclick = function() {

                socket.send(
                    JSON.stringify({

                        type: "kill",

                        target:
                            player.name

                    })
                );

            };


            actions.appendChild(button);

        });

    }


    // ========================================================
    // ГОЛОСОВАНИЕ
    // ========================================================

    if (
        state.phase === "🗳️ ГОЛОСОВАНИЕ"
    ) {

        const title =
            document.createElement("h3");

        title.textContent =
            "🗳️ За кого голосовать?";

        actions.appendChild(title);


        state.players.forEach(player => {

            if (
                player.name === myName
                ||
                !player.alive
            ) {

                return;
            }


            const button =
                document.createElement("button");

            button.className =
                "action-button";

            button.textContent =
                "Голосовать против " +
                player.name;


            button.onclick = function() {

                socket.send(
                    JSON.stringify({

                        type: "vote",

                        target:
                            player.name

                    })
                );

            };


            actions.appendChild(button);

        });

    }

}


// ============================================================
// ПОКАЗ ВСЕХ РОЛЕЙ ПОСЛЕ ИГРЫ
// ============================================================

function renderResult(state) {

    const result =
        document.getElementById("result");


    if (state.phase !== "🏆 ПОБЕДА") {

        result
            .classList
            .add("hidden");

        result.innerHTML = "";

        return;
    }


    result
        .classList
        .remove("hidden");


    let html = "";

    html += "<h2>🏆 Игра окончена</h2>";

    html +=
        "<p style='text-align:center'>" +
        state.announcement +
        "</p>";


    html +=
        "<h3>🎭 Роли игроков</h3>";


    html +=
        "<div class='role-list'>";


    if (state.roles) {

        state.roles.forEach(player => {

            const roleClass =
                player.role === "Мафия"
                    ? "mafia-role"
                    : "citizen-role";


            html +=
                "<div class='role-player'>" +

                "<span>" +
                escapeHtml(player.name) +
                "</span>" +

                "<span class='" +
                roleClass +
                "'>" +
                escapeHtml(player.role) +
                "</span>" +

                "</div>";

        });

    }


    html += "</div>";


    if (state.host === myName) {

        html +=
            "<p style='text-align:center;margin-top:15px'>" +
            "Ты можешь запустить новую игру." +
            "</p>";

    }


    result.innerHTML = html;

}


// ============================================================
// ЗАПУСК / РЕСТАРТ
// ============================================================

function startGame() {

    if (!socket) {

        return;
    }


    socket.send(
        JSON.stringify({

            type: "start"

        })
    );

}


// ============================================================
// ЗАЩИТА HTML
// ============================================================

function escapeHtml(text) {

    return String(text)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}

</script>

</body>

</html>
"""


# ============================================================
# СОЗДАНИЕ КОДА КОМНАТЫ
# ============================================================

def generate_room_code():

    while True:

        code = "".join(
            random.choice(string.digits)
            for _ in range(4)
        )

        if code not in rooms:

            return code


# ============================================================
# СОСТОЯНИЕ КОМНАТЫ
# ============================================================

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


    # --------------------------------------------------------
    # Все роли показываем только после победы
    # --------------------------------------------------------

    roles = None


    if room["phase"] == "🏆 ПОБЕДА":

        roles = [

            {
                "name": p["name"],
                "role": p["role"]
            }

            for p in
            room["players"].values()

        ]


    return {

        "type":
            "state",

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
                    "name":
                        p["name"],

                    "alive":
                        p["alive"]
                }

                for p in
                room["players"].values()
            ],

        "announcement":
            room["announcement"],

        "log":
            room["log"],

        "roles":
            roles

    }


# ============================================================
# ОТПРАВКА СОСТОЯНИЯ
# ============================================================

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


# ============================================================
# ПРОВЕРКА ПОБЕДЫ
# ============================================================

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


    # --------------------------------------------------------
    # Мирные победили
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Мафия победила
    # --------------------------------------------------------

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


# ============================================================
# РАСПРЕДЕЛЕНИЕ РОЛЕЙ
# ============================================================

def assign_roles(room):

    names = list(
        room["players"]
    )


    random.shuffle(names)


    mafia_count = max(
        1,
        len(names) // 4
    )


    for index, name in enumerate(names):

        if index < mafia_count:

            room["players"][
                name
            ]["role"] = "Мафия"

        else:

            room["players"][
                name
            ]["role"] = "Мирный"


# ============================================================
# НАЧАЛО / РЕСТАРТ ИГРЫ
# ============================================================

async def start_new_game(room):

    # --------------------------------------------------------
    # Если старый игровой цикл ещё существует
    # --------------------------------------------------------

    old_task = room.get(
        "game_task"
    )


    if (
        old_task
        and
        not old_task.done()
        and
        old_task !=
        asyncio.current_task()
    ):

        old_task.cancel()


    # --------------------------------------------------------
    # Сбрасываем игроков
    # --------------------------------------------------------

    for player in (
        room["players"].values()
    ):

        player["alive"] = True

        player["role"] = None


    # --------------------------------------------------------
    # Очищаем данные прошлой игры
    # --------------------------------------------------------

    room["night_target"] = None

    room["votes"] = {}

    room["log"] = [
        "🎮 Новая игра начинается!"
    ]


    # --------------------------------------------------------
    # Назначаем новые роли
    # --------------------------------------------------------

    assign_roles(room)


    # --------------------------------------------------------
    # Начинаем ночь
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Запускаем игровой цикл
    # --------------------------------------------------------

    room["game_task"] = (
        asyncio.create_task(
            game_loop(room)
        )
    )


# ============================================================
# ИГРОВОЙ ЦИКЛ
# ============================================================

async def game_loop(room):

    try:

        while (
            room["phase"] !=
            "🏆 ПОБЕДА"
        ):

            now = (
                asyncio
                .get_running_loop()
                .time()
            )


            # ------------------------------------------------
            # Ждём окончания текущей фазы
            # ------------------------------------------------

            if room["ends"] > now:

                await broadcast(room)

                await asyncio.sleep(
                    min(
                        1,
                        room["ends"] -
                        now
                    )
                )

                continue


            # =================================================
            # КОНЕЦ НОЧИ
            # =================================================

            if (
                room["phase"] ==
                "🌙 НОЧЬ — МАФИЯ"
            ):

                target = (
                    room["night_target"]
                )


                if (
                    target
                    and
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


                # =============================================
                # ДЕНЬ
                # =============================================

                room["phase"] = (
                    "☀️ ДЕНЬ"
                )


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


                # =============================================
                # ГОЛОСОВАНИЕ
                # =============================================

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


            # =================================================
            # КОНЕЦ ГОЛОСОВАНИЯ
            # =================================================

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


                # =============================================
                # НОВАЯ НОЧЬ
                # =============================================

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

    except asyncio.CancelledError:

        # Игровой цикл был остановлен
        # для рестарта игры.

        return


# ============================================================
# ГЛАВНАЯ СТРАНИЦА
# ============================================================

@app.get("/")
async def home():

    return HTMLResponse(
        HTML
    )


# ============================================================
# СОЗДАНИЕ КОМНАТЫ
# ============================================================

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


# ============================================================
# WEBSOCKET
# ============================================================

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


        if (
            room["phase"] != "ЛОББИ"
            and
            room["phase"] != "🏆 ПОБЕДА"
        ):

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


        # ====================================================
        # ДОБАВЛЯЕМ ИГРОКА
        # ====================================================

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


        # ====================================================
        # КОМАНДЫ
        # ====================================================

        while True:

            data = (
                await websocket
                .receive_json()
            )


            command = data.get(
                "type"
            )


            # =================================================
            # START / RESTART
            # =================================================

            if command == "start":

                if (
                    player_name !=
                    room["host"]
                ):

                    continue


                # ---------------------------------------------
                # ОБЫЧНЫЙ СТАРТ
                # ---------------------------------------------

                if room["phase"] == "ЛОББИ":

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


                    await start_new_game(
                        room
                    )


                    await broadcast(room)

                    continue


                # ---------------------------------------------
                # РЕСТАРТ ПОСЛЕ ИГРЫ
                # ---------------------------------------------

                if room["phase"] == "🏆 ПОБЕДА":

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


                    await start_new_game(
                        room
                    )


                    await broadcast(room)

                    continue


            # =================================================
            # УБИЙСТВО
            # =================================================

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


            # =================================================
            # ГОЛОСОВАНИЕ
            # =================================================

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


            # ------------------------------------------------
            # Игрок выходит только из лобби
            # ------------------------------------------------

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


# ============================================================
# ЛОКАЛЬНЫЙ ЗАПУСК
# ============================================================

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
