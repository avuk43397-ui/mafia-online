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

<title>Mafia Night</title>

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

    color: #ffffff;

    background:

        radial-gradient(
            circle at 50% -10%,
            #38234e 0%,
            #171321 38%,
            #09080d 80%
        );

    overflow-x: hidden;
}


/* ============================================================
   BACKGROUND
   ============================================================ */

body::before {

    content: "";

    position: fixed;

    inset: 0;

    pointer-events: none;

    background:

        radial-gradient(
            circle at 20% 20%,
            rgba(124,58,237,.08),
            transparent 30%
        ),

        radial-gradient(
            circle at 80% 70%,
            rgba(220,38,38,.07),
            transparent 30%
        );

}


/* ============================================================
   CONTAINER
   ============================================================ */

.container {

    width: min(
        1200px,
        calc(100% - 30px)
    );

    margin: 0 auto;

    padding: 30px 0 60px;

}


/* ============================================================
   HEADER
   ============================================================ */

.logo {

    text-align: center;

    margin-bottom: 25px;

}

.logo h1 {

    margin: 0;

    font-size: clamp(
        38px,
        7vw,
        72px
    );

    letter-spacing: 10px;

    font-weight: 900;

    text-shadow:
        0 0 30px
        rgba(255,255,255,.15);

}

.logo p {

    margin: 10px 0 0;

    color: #958ca4;

    letter-spacing: 3px;

    font-size: 12px;

}


/* ============================================================
   CARD
   ============================================================ */

.card {

    background:
        linear-gradient(
            145deg,
            rgba(30,26,41,.96),
            rgba(14,12,20,.96)
        );

    border:

        1px solid
        rgba(255,255,255,.07);

    border-radius: 22px;

    padding: 24px;

    box-shadow:

        0 25px 70px
        rgba(0,0,0,.4),

        inset 0 1px 0
        rgba(255,255,255,.03);

}


/* ============================================================
   LOGIN
   ============================================================ */

.login {

    max-width: 600px;

    margin: 30px auto;

}

.login h2 {

    text-align: center;

    margin-top: 0;

}

.inputs {

    display: grid;

    grid-template-columns:
        1fr 180px;

    gap: 10px;

}


input {

    width: 100%;

    padding: 16px;

    border-radius: 14px;

    border:

        1px solid
        #393244;

    background:
        #121019;

    color: white;

    outline: none;

    font-size: 15px;

}


input:focus {

    border-color:
        #8b5cf6;

    box-shadow:
        0 0 0 3px
        rgba(139,92,246,.12);

}


button {

    border: 0;

    border-radius: 14px;

    padding: 14px 20px;

    color: white;

    background:
        linear-gradient(
            135deg,
            #8b5cf6,
            #6d28d9
        );

    font-weight: 800;

    cursor: pointer;

    transition:
        .2s;

}


button:hover {

    transform:
        translateY(-2px);

    filter:
        brightness(1.1);

}


button:active {

    transform:
        translateY(0);

}


.secondary {

    background:
        #292431;

}


.red {

    background:
        linear-gradient(
            135deg,
            #ef4444,
            #991b1b
        );

}


.green {

    background:
        linear-gradient(
            135deg,
            #10b981,
            #047857
        );

}


.blue {

    background:
        linear-gradient(
            135deg,
            #3b82f6,
            #1d4ed8
        );

}


.actions {

    display: flex;

    flex-wrap: wrap;

    gap: 10px;

    margin-top: 15px;

}


.error {

    min-height: 22px;

    margin-top: 12px;

    color:
        #fb7185;

}


/* ============================================================
   GAME
   ============================================================ */

.hidden {

    display: none !important;

}


.game-top {

    display: grid;

    grid-template-columns:
        1fr
        1.3fr
        130px;

    gap: 15px;

    align-items: center;

}


.label {

    color:
        #81788d;

    font-size: 11px;

    letter-spacing: 2px;

}


.room-code {

    font-size: 32px;

    font-weight: 900;

    letter-spacing: 8px;

}


.phase {

    text-align: center;

    font-size: 22px;

    font-weight: 900;

}


.my-role {

    text-align: center;

    margin-top: 6px;

    color:
        #bca7ff;

    font-weight: 700;

}


.timer {

    font-size: 34px;

    font-weight: 900;

    text-align: center;

    padding: 12px;

    border-radius: 16px;

    background:
        #0e0c14;

}


.announcement {

    margin-top: 20px;

    padding: 17px;

    text-align: center;

    border-radius: 16px;

    background:
        rgba(124,58,237,.10);

    border:
        1px solid
        rgba(124,58,237,.25);

    color:
        #d9d2e4;

}


/* ============================================================
   GRID
   ============================================================ */

.grid {

    display: grid;

    grid-template-columns:
        1.3fr
        .7fr;

    gap: 20px;

    margin-top: 20px;

}


/* ============================================================
   PLAYERS
   ============================================================ */

.players {

    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(
                190px,
                1fr
            )
        );

    gap: 12px;

}


.player {

    position: relative;

    overflow: hidden;

    padding: 16px;

    border-radius: 17px;

    background:
        linear-gradient(
            145deg,
            #1b1724,
            #111018
        );

    border:
        1px solid
        rgba(255,255,255,.06);

    transition:
        .2s;

}


.player:hover {

    transform:
        translateY(-2px);

    border-color:
        rgba(139,92,246,.35);

}


.player.dead {

    opacity: .42;

    filter:
        grayscale(.7);

}


.player-top {

    display: flex;

    align-items: center;

    gap: 12px;

}


.avatar {

    width: 44px;

    height: 44px;

    border-radius: 50%;

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 22px;

    background:
        #292431;

}


.player-name {

    font-weight: 800;

}


.host {

    color:
        #facc15;

    font-size: 11px;

    margin-top: 4px;

}


.status {

    margin-top: 12px;

    font-size: 12px;

    font-weight: 800;

}


.alive {

    color:
        #34d399;

}


.dead-status {

    color:
        #fb7185;

}


/* ============================================================
   ACTIONS
   ============================================================ */

.action-list {

    display: grid;

    gap: 8px;

    margin-top: 15px;

}


.action-list button {

    width: 100%;

    text-align: left;

}


.action-title {

    margin-top: 20px;

    color:
        #bcb2c8;

    font-weight: 800;

}


/* ============================================================
   LOG
   ============================================================ */

.log {

    max-height: 470px;

    overflow-y: auto;

}


.log-item {

    padding: 12px 0;

    border-bottom:
        1px solid
        rgba(255,255,255,.06);

    color:
        #aaa1b0;

    font-size: 14px;

}


/* ============================================================
   RESULT
   ============================================================ */

.result {

    margin-top: 20px;

    padding: 24px;

    border-radius: 20px;

    background:
        radial-gradient(
            circle at top,
            rgba(124,58,237,.2),
            rgba(10,9,14,.3)
        );

    border:
        1px solid
        rgba(139,92,246,.25);

}


.result-title {

    text-align: center;

    font-size: 30px;

    font-weight: 900;

    margin-bottom: 20px;

}


.roles {

    display: grid;

    gap: 9px;

}


.role-row {

    display: flex;

    justify-content: space-between;

    align-items: center;

    padding: 13px 15px;

    border-radius: 12px;

    background:
        rgba(255,255,255,.04);

}


.role-mafia {

    color:
        #fb7185;

    font-weight: 900;

}


.role-neutral {

    color:
        #facc15;

    font-weight: 900;

}


.role-good {

    color:
        #34d399;

    font-weight: 900;

}


/* ============================================================
   LOBBY INFO
   ============================================================ */

.lobby-info {

    margin-top: 15px;

    padding: 15px;

    border-radius: 15px;

    background:
        rgba(255,255,255,.035);

    color:
        #a9a0b0;

    font-size: 14px;

}


.copy {

    margin-top: 10px;

}


/* ============================================================
   MOBILE
   ============================================================ */

@media(max-width: 800px) {

    .game-top {

        grid-template-columns:
            1fr;

    }

    .phase {

        text-align:
            left;

    }

    .my-role {

        text-align:
            left;

    }

    .grid {

        grid-template-columns:
            1fr;

    }

    .inputs {

        grid-template-columns:
            1fr;

    }

}

</style>

</head>


<body>


<div class="container">


<div class="logo">

    <h1>MAFIA</h1>

    <p>
        NIGHT • LIES • SURVIVAL
    </p>

</div>


<!-- =========================================================
     LOGIN
     ========================================================= -->

<div
    id="login"
    class="card login"
>

    <h2>
        🔥 Добро пожаловать
    </h2>

    <p
        style="
            text-align:center;
            color:#8f8798;
        "
    >
        Создай комнату или присоединись к друзьям
    </p>


    <div class="inputs">

        <input
            id="name"
            maxlength="18"
            placeholder="Твоё имя"
        >

        <input
            id="room"
            maxlength="4"
            placeholder="Код"
        >

    </div>


    <div class="actions">

        <button
            onclick="createRoom()"
            style="flex:1"
        >
            ✨ Создать комнату
        </button>

        <button
            class="secondary"
            onclick="joinRoom()"
            style="flex:1"
        >
            🚪 Войти
        </button>

    </div>


    <div
        id="loginError"
        class="error"
    ></div>


    <div class="lobby-info">

        <b>Система ролей</b><br><br>

        4–5 игроков →
        Мафия / Доктор / Шериф<br>

        6–7 игроков →
        2 Мафии / Доктор / Шериф<br>

        8–9 игроков →
        Дон / Телохранитель<br>

        10–12 игроков →
        Маньяк / Детектив

    </div>

</div>


<!-- =========================================================
     GAME
     ========================================================= -->

<div
    id="game"
    class="hidden"
>


<div class="card">

    <div class="game-top">

        <div>

            <div class="label">
                КОД КОМНАТЫ
            </div>

            <div
                id="roomCode"
                class="room-code"
            >
                ----
            </div>

            <button
                class="secondary copy"
                onclick="copyRoom()"
            >
                📋 Скопировать код
            </button>

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
                class="my-role"
            >
                Роль не назначена
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


<!-- =========================================================
     LEFT
     ========================================================= -->

<div class="card">

    <h2>
        👥 Игроки
    </h2>

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
    ></div>


    <div
        id="result"
        class="result hidden"
    ></div>

</div>


<!-- =========================================================
     RIGHT
     ========================================================= -->

<div class="card">

    <h2>
        📜 События
    </h2>

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

let state = null;


// ============================================================
// CREATE ROOM
// ============================================================

async function createRoom() {

    const name =
        document
        .getElementById("name")
        .value
        .trim();

    const error =
        document
        .getElementById("loginError");

    error.textContent = "";


    if (!name) {

        error.textContent =
            "Сначала введи имя.";

        return;

    }


    try {

        const response =
            await fetch(
                "/create?x=" +
                Date.now()
            );


        if (!response.ok) {

            throw new Error(
                "Ошибка сервера: " +
                response.status
            );

        }


        const data =
            await response.json();


        if (!data.room) {

            throw new Error(
                "Код комнаты не получен."
            );

        }


        document
            .getElementById("room")
            .value =
            data.room;


        joinRoom();


    } catch (error) {

        console.error(error);

        document
            .getElementById("loginError")
            .textContent =
            "Не удалось создать комнату.";

    }

}


// ============================================================
// JOIN
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
        document
        .getElementById("loginError");


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


    const protocol =
        location.protocol === "https:"
            ? "wss:"
            : "ws:";


    socket = new WebSocket(
        protocol +
        "//" +
        location.host +
        "/ws"
    );


    socket.onopen = function() {

        socket.send(
            JSON.stringify({

                type:
                    "join",

                name:
                    name,

                room:
                    room

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
            data.type ===
            "error"
        ) {

            error.textContent =
                data.message;

            return;

        }


        if (
            data.type ===
            "state"
        ) {

            state = data;

            showGame();

            render(data);

        }

    };


    socket.onerror =
        function() {

        error.textContent =
            "Ошибка подключения к серверу.";

    };

}


// ============================================================
// SHOW GAME
// ============================================================

function showGame() {

    document
        .getElementById("login")
        .classList
        .add("hidden");


    document
        .getElementById("game")
        .classList
        .remove("hidden");

}


// ============================================================
// RENDER
// ============================================================

function render(data) {


    document
        .getElementById("roomCode")
        .textContent =
        data.room;


    document
        .getElementById("phase")
        .textContent =
        data.phase;


    document
        .getElementById("timer")
        .textContent =
        data.time > 0
            ? data.time
            : "--";


    document
        .getElementById("announcement")
        .textContent =
        data.announcement;


    const role =
        document
        .getElementById("myRole");


    if (data.role) {

        role.textContent =
            "🎭 Твоя роль: " +
            data.role;

    } else {

        role.textContent =
            "Роль не назначена";

    }


    renderPlayers(data);

    renderHost(data);

    renderActions(data);

    renderLog(data);

    renderResult(data);

}


// ============================================================
// PLAYERS
// ============================================================

function renderPlayers(data) {

    const box =
        document
        .getElementById("players");

    box.innerHTML = "";


    data.players.forEach(
        player => {

        const div =
            document.createElement(
                "div"
            );


        div.className =
            "player " +
            (
                player.alive
                    ? ""
                    : "dead"
            );


        const avatar =
            player.alive
                ? "👤"
                : "💀";


        div.innerHTML = `

            <div class="player-top">

                <div class="avatar">
                    ${avatar}
                </div>

                <div>

                    <div class="player-name">
                        ${escapeHtml(player.name)}
                    </div>

                    ${
                        player.name === data.host
                        ?
                        `
                        <div class="host">
                            👑 ХОСТ
                        </div>
                        `
                        :
                        ""
                    }

                </div>

            </div>

            <div
                class="status
                ${
                    player.alive
                        ? "alive"
                        : "dead-status"
                }"
            >

                ${
                    player.alive
                        ? "● ЖИВ"
                        : "✕ МЁРТ"
                }

            </div>

        `;


        box.appendChild(div);

    });

}


// ============================================================
// HOST
// ============================================================

function renderHost(data) {

    const controls =
        document
        .getElementById(
            "hostControls"
        );


    const button =
        document
        .getElementById(
            "startButton"
        );


    if (
        data.host === myName
        &&
        (
            data.phase === "ЛОББИ"
            ||
            data.phase === "🏆 ПОБЕДА"
        )
    ) {

        controls
            .classList
            .remove("hidden");


        if (
            data.phase ===
            "🏆 ПОБЕДА"
        ) {

            button.textContent =
                "🔄 Начать заново";

        } else {

            button.textContent =
                "▶ Начать игру";

        }

    } else {

        controls
            .classList
            .add("hidden");

    }

}


// ============================================================
// ACTIONS
// ============================================================

function renderActions(data) {

    const box =
        document
        .getElementById(
            "actions"
        );


    box.innerHTML = "";


    const me =
        data.players.find(
            p => p.name === myName
        );


    if (!me || !me.alive) {

        return;

    }


    // ========================================================
    // MAFIA
    // ========================================================

    if (
        data.phase ===
        "🌙 НОЧЬ — МАФИЯ"
        &&
        (
            data.role === "Мафия"
            ||
            data.role === "Дон"
        )
    ) {

        addTitle(
            box,
            "🔪 Выбери жертву"
        );


        data.players.forEach(
            player => {

            if (
                !player.alive
                ||
                player.name === myName
            ) {

                return;

            }


            addAction(
                box,
                "🔪 Убить " +
                player.name,
                "kill",
                player.name,
                "red"
            );

        });

    }


    // ========================================================
    // MANIAC
    // ========================================================

    if (
        data.phase ===
        "🌙 НОЧЬ — МАФИЯ"
        &&
        data.role ===
        "Маньяк"
    ) {

        addTitle(
            box,
            "🔪 Маньяк выбирает жертву"
        );


        data.players.forEach(
            player => {

            if (
                !player.alive
                ||
                player.name === myName
            ) {

                return;

            }


            addAction(
                box,
                "🔪 Убить " +
                player.name,
                "maniac_kill",
                player.name,
                "red"
            );

        });

    }


    // ========================================================
    // DOCTOR
    // ========================================================

    if (
        data.phase ===
        "🌙 НОЧЬ — МАФИЯ"
        &&
        data.role ===
        "Доктор"
    ) {

        addTitle(
            box,
            "🩺 Кого лечить?"
        );


        data.players.forEach(
            player => {

            if (!player.alive) {

                return;

            }


            addAction(
                box,
                "🩺 Лечить " +
                player.name,
                "heal",
                player.name,
                "green"
            );

        });

    }


    // ========================================================
    // BODYGUARD
    // ========================================================

    if (
        data.phase ===
        "🌙 НОЧЬ — МАФИЯ"
        &&
        data.role ===
        "Телохранитель"
    ) {

        addTitle(
            box,
            "🛡️ Кого защищать?"
        );


        data.players.forEach(
            player => {

            if (!player.alive) {

                return;

            }


            addAction(
                box,
                "🛡️ Защитить " +
                player.name,
                "protect",
                player.name,
                "blue"
            );

        });

    }


    // ========================================================
    // SHERIFF
    // ========================================================

    if (
        data.phase ===
        "🌙 НОЧЬ — МАФИЯ"
        &&
        data.role ===
        "Шериф"
    ) {

        addTitle(
            box,
            "🕵️ Кого проверить?"
        );


        data.players.forEach(
            player => {

            if (
                !player.alive
                ||
                player.name === myName
            ) {

                return;

            }


            addAction(
                box,
                "🕵️ Проверить " +
                player.name,
                "inspect",
                player.name,
                "blue"
            );

        });

    }


    // ========================================================
    // DETECTIVE
    // ========================================================

    if (
        data.phase ===
        "🌙 НОЧЬ — МАФИЯ"
        &&
        data.role ===
        "Детектив"
    ) {

        addTitle(
            box,
            "🔎 Исследовать игрока"
        );


        data.players.forEach(
            player => {

            if (
                !player.alive
                ||
                player.name === myName
            ) {

                return;

            }


            addAction(
                box,
                "🔎 Узнать роль " +
                player.name,
                "detect",
                player.name,
                "blue"
            );

        });

    }


    // ========================================================
    // VOTING
    // ========================================================

    if (
        data.phase ===
        "🗳️ ГОЛОСОВАНИЕ"
    ) {

        addTitle(
            box,
            "🗳️ За кого голосовать?"
        );


        data.players.forEach(
            player => {

            if (
                !player.alive
                ||
                player.name === myName
            ) {

                return;

            }


            addAction(
                box,
                "🗳️ Против " +
                player.name,
                "vote",
                player.name,
                ""
            );

        });

    }

}


// ============================================================
// ACTION BUTTON
// ============================================================

function addAction(
    box,
    text,
    type,
    target,
    color
) {

    const button =
        document.createElement(
            "button"
        );


    button.textContent =
        text;


    if (color) {

        button.classList.add(color);

    }


    button.onclick =
        function() {

        if (!socket) {

            return;

        }


        socket.send(
            JSON.stringify({

                type:
                    type,

                target:
                    target

            })
        );

    };


    box.appendChild(button);

}


// ============================================================
// TITLE
// ============================================================

function addTitle(
    box,
    text
) {

    const div =
        document.createElement(
            "div"
        );


    div.className =
        "action-title";


    div.textContent =
        text;


    box.appendChild(div);

}


// ============================================================
// LOG
// ============================================================

function renderLog(data) {

    const box =
        document
        .getElementById("log");


    box.innerHTML = "";


    data.log.forEach(
        item => {

        const div =
            document.createElement(
                "div"
            );


        div.className =
            "log-item";


        div.textContent =
            item;


        box.appendChild(div);

    });

}


// ============================================================
// RESULT
// ============================================================

function renderResult(data) {

    const box =
        document
        .getElementById(
            "result"
        );


    if (
        data.phase !==
        "🏆 ПОБЕДА"
    ) {

        box.classList.add(
            "hidden"
        );

        return;

    }


    box.classList.remove(
        "hidden"
    );


    let html = "";


    html += `

        <div class="result-title">
            🏆 ИГРА ОКОНЧЕНА
        </div>

        <div
            style="
                text-align:center;
                color:#aaa0b1;
                margin-bottom:20px;
            "
        >
            ${escapeHtml(data.announcement)}
        </div>

        <h3>
            🎭 Все роли
        </h3>

        <div class="roles">

    `;


    if (data.roles) {

        data.roles.forEach(
            player => {

            let cls =
                "role-good";


            if (
                player.role ===
                "Мафия"
                ||
                player.role ===
                "Дон"
            ) {

                cls =
                    "role-mafia";

            }


            if (
                player.role ===
                "Маньяк"
            ) {

                cls =
                    "role-neutral";

            }


            html += `

                <div class="role-row">

                    <span>
                        ${escapeHtml(player.name)}
                    </span>

                    <span
                        class="${cls}"
                    >
                        ${escapeHtml(player.role)}
                    </span>

                </div>

            `;

        });

    }


    html += `
        </div>
    `;


    box.innerHTML =
        html;

}


// ============================================================
// COPY
// ============================================================

function copyRoom() {

    if (!state) {

        return;

    }


    navigator.clipboard.writeText(
        state.room
    );


    alert(
        "Код комнаты скопирован: " +
        state.room
    );

}


// ============================================================
// START / RESTART
// ============================================================

function startGame() {

    if (!socket) {

        return;

    }


    socket.send(
        JSON.stringify({

            type:
                "start"

        })
    );

}


// ============================================================
// ESCAPE
// ============================================================

function escapeHtml(text) {

    return String(text)
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );

}

</script>

</body>

</html>
"""


# ============================================================
# ROOM CODE
# ============================================================

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


# ============================================================
# TIME
# ============================================================

def now():

    return (
        asyncio
        .get_running_loop()
        .time()
    )


# ============================================================
# ROLE SET
# ============================================================

def get_roles_for_players(count):

    if count < 4:

        return None


    if count <= 5:

        return [
            "Мафия",
            "Доктор",
            "Шериф"
        ]


    if count <= 7:

        return [
            "Мафия",
            "Мафия",
            "Доктор",
            "Шериф"
        ]


    if count <= 9:

        return [
            "Мафия",
            "Мафия",
            "Дон",
            "Доктор",
            "Шериф",
            "Телохранитель"
        ]


    if count <= 11:

        return [
            "Мафия",
            "Мафия",
            "Дон",
            "Доктор",
            "Шериф",
            "Телохранитель",
            "Маньяк"
        ]


    return [
        "Мафия",
        "Мафия",
        "Дон",
        "Доктор",
        "Шериф",
        "Телохранитель",
        "Маньяк",
        "Детектив"
    ]


# ============================================================
# ASSIGN ROLES
# ============================================================

def assign_roles(room):

    players = list(
        room["players"].values()
    )


    roles = get_roles_for_players(
        len(players)
    )


    if roles is None:

        return


    while len(roles) < len(players):

        roles.append(
            "Мирный"
        )


    random.shuffle(roles)


    random.shuffle(players)


    for player, role in zip(
        players,
        roles
    ):

        player["role"] = role


# ============================================================
# MAJOR ROLE CHECKS
# ============================================================

def is_mafia(player):

    return player["role"] in (
        "Мафия",
        "Дон"
    )


def is_alive(room, name):

    player = room["players"].get(
        name
    )

    return bool(
        player
        and
        player["alive"]
    )


# ============================================================
# STATE
# ============================================================

def get_state(
    room,
    player_name
):

    player = room["players"].get(
        player_name
    )


    remaining = 0


    if room["ends"]:

        remaining = max(
            0,
            int(
                room["ends"] -
                now()
            )
        )


    roles = None


    # Роли становятся видны
    # только после окончания игры

    if (
        room["phase"] ==
        "🏆 ПОБЕДА"
    ):

        roles = [

            {
                "name":
                    p["name"],

                "role":
                    p["role"]
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
            player["role"]
            if player
            else None,

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
# BROADCAST
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
# WINNER
# ============================================================

def check_winner(room):

    alive = [

        p

        for p in
        room["players"].values()

        if p["alive"]

    ]


    mafia = [

        p

        for p in alive

        if is_mafia(p)

    ]


    maniac = [

        p

        for p in alive

        if p["role"] ==
        "Маньяк"

    ]


    citizens = [

        p

        for p in alive

        if not is_mafia(p)
        and
        p["role"] !=
        "Маньяк"

    ]


    # ========================================================
    # МАНЬЯК
    # ========================================================

    if maniac and len(alive) <= 2:

        room["phase"] = (
            "🏆 ПОБЕДА"
        )

        room["ends"] = 0

        room["announcement"] = (
            "🔪 Маньяк остался последним!"
        )

        room["log"].append(
            "🔪 Маньяк победил!"
        )

        return True


    # ========================================================
    # МИРНЫЕ
    # ========================================================

    if len(mafia) == 0:

        if not maniac:

            room["phase"] = (
                "🏆 ПОБЕДА"
            )

            room["ends"] = 0

            room["announcement"] = (
                "🟢 Мирные жители победили!"
            )

            room["log"].append(
                "🏆 Победа мирных!"
            )

            return True


    # ========================================================
    # МАФИЯ
    # ========================================================

    if len(mafia) >= len(citizens) + len(maniac):

        room["phase"] = (
            "🏆 ПОБЕДА"
        )

        room["ends"] = 0

        room["announcement"] = (
            "🔴 Мафия захватила город!"
        )

        room["log"].append(
            "🏆 Мафия победила!"
        )

        return True


    return False


# ============================================================
# START GAME
# ============================================================

async def start_game(room):

    task = room.get(
        "game_task"
    )


    if (
        task
        and
        not task.done()
        and
        task !=
        asyncio.current_task()
    ):

        task.cancel()


    for player in (
        room["players"].values()
    ):

        player["alive"] = True

        player["role"] = None


    room["night_target"] = None

    room["maniac_target"] = None

    room["doctor_target"] = None

    room["bodyguard_target"] = None

    room["votes"] = {}

    room["investigations"] = {}


    room["log"] = [
        "🎬 Новая игра началась!"
    ]


    assign_roles(room)


    room["phase"] = (
        "🌙 НОЧЬ — МАФИЯ"
    )


    room["ends"] = (
        now() + 15
    )


    room["announcement"] = (
        "Город засыпает..."
    )


    room["game_task"] = (
        asyncio.create_task(
            game_loop(room)
        )
    )


# ============================================================
# NIGHT RESOLUTION
# ============================================================

def resolve_night(room):

    deaths = []


    protected = set()


    if room["doctor_target"]:

        protected.add(
            room["doctor_target"]
        )


    if room["bodyguard_target"]:

        protected.add(
            room["bodyguard_target"]
        )


    # ========================================================
    # MAFIA
    # ========================================================

    mafia_target = (
        room["night_target"]
    )


    if (
        mafia_target
        and
        is_alive(
            room,
            mafia_target
        )
        and
        mafia_target
        not in protected
    ):

        deaths.append(
            (
                mafia_target,
                "Мафия"
            )
        )


    # ========================================================
    # MANIAC
    # ========================================================

    maniac_target = (
        room["maniac_target"]
    )


    if (
        maniac_target
        and
        is_alive(
            room,
            maniac_target
        )
        and
        maniac_target
        not in protected
    ):

        if not any(
            x[0] ==
            maniac_target
            for x in deaths
        ):

            deaths.append(
                (
                    maniac_target,
                    "Маньяк"
                )
            )


    # ========================================================
    # APPLY DEATHS
    # ========================================================

    for (
        name,
        killer
    ) in deaths:

        player = (
            room["players"]
            .get(name)
        )


        if (
            player
            and
            player["alive"]
        ):

            player["alive"] = False


            room["log"].append(
                f"💀 Ночью погиб {name}."
            )


    if deaths:

        room["announcement"] = (
            "Город просыпается. "
            "Ночью произошло убийство."
        )

    else:

        room["announcement"] = (
            "☀️ Город просыпается. "
            "Этой ночью никто не погиб."
        )


    # ========================================================
    # CLEAR NIGHT
    # ========================================================

    room["night_target"] = None

    room["maniac_target"] = None

    room["doctor_target"] = None

    room["bodyguard_target"] = None


# ============================================================
# GAME LOOP
# ============================================================

async def game_loop(room):

    try:

        while (
            room["phase"] !=
            "🏆 ПОБЕДА"
        ):

            current = now()


            if room["ends"] > current:

                await broadcast(room)

                await asyncio.sleep(
                    min(
                        1,
                        room["ends"] -
                        current
                    )
                )

                continue


            # =================================================
            # NIGHT
            # =================================================

            if (
                room["phase"] ==
                "🌙 НОЧЬ — МАФИЯ"
            ):

                resolve_night(room)


                if check_winner(room):

                    await broadcast(room)

                    return


                room["phase"] = (
                    "☀️ ДЕНЬ"
                )


                room["ends"] = (
                    now() + 8
                )


                await broadcast(room)


                await asyncio.sleep(8)


                if check_winner(room):

                    await broadcast(room)

                    return


                # =============================================
                # VOTING
                # =============================================

                room["phase"] = (
                    "🗳️ ГОЛОСОВАНИЕ"
                )


                room["ends"] = (
                    now() + 60
                )


                room["votes"] = {}


                room["announcement"] = (
                    "🗳️ Началось голосование. "
                    "У вас 60 секунд."
                )


                await broadcast(room)


            # =================================================
            # VOTING END
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

                    maximum = max(
                        counts.values()
                    )


                    winners = [

                        name

                        for name,
                        count
                        in counts.items()

                        if count ==
                        maximum

                    ]


                    # Ничья

                    if len(winners) > 1:

                        room["announcement"] = (
                            "⚖️ Ничья! "
                            "Никто не был изгнан."
                        )

                        room["log"].append(
                            "⚖️ Голоса разделились."
                        )

                    else:

                        victim =
                        winners[0]

                        if is_alive(
                            room,
                            victim
                        ):

                            room[
                                "players"
                            ][
                                victim
                            ][
                                "alive"
                            ] = False


                            room["announcement"] = (
                                f"⚖️ {victim} "
                                "был изгнан."
                            )


                            room["log"].append(
                                room["announcement"]
                            )

                else:

                    room["announcement"] = (
                        "Никто не проголосовал."
                    )


                room["votes"] = {}


                if check_winner(room):

                    await broadcast(room)

                    return


                # =============================================
                # NEXT NIGHT
                # =============================================

                room["phase"] = (
                    "🌙 НОЧЬ — МАФИЯ"
                )


                room["ends"] = (
                    now() + 15
                )


                room["announcement"] = (
                    "🌙 Город засыпает. "
                    "Мафия просыпается."
                )


                await broadcast(room)


    except asyncio.CancelledError:

        return


# ============================================================
# HOME
# ============================================================

@app.get("/")
async def home():

    return HTMLResponse(
        HTML
    )


# ============================================================
# CREATE ROOM
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

        "maniac_target":
            None,

        "doctor_target":
            None,

        "bodyguard_target":
            None,

        "votes":
            {},

        "investigations":
            {},

        "log":
            [],

        "game_task":
            None

    }


    print(
        "Создана комната:",
        code
    )


    return {
        "room":
            code
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

        first =
            await websocket.receive_json()


        if (
            first.get("type")
            !=
            "join"
        ):

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
        ).strip().upper()


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


        if room["phase"] not in (
            "ЛОББИ",
            "🏆 ПОБЕДА"
        ):

            await websocket.send_json({

                "type":
                    "error",

                "message":
                    "Игра уже идёт."

            })

            return


        if player_name in (
            room["players"]
        ):

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
                    "Максимум 12 игроков."

            })

            return


        # ====================================================
        # ADD PLAYER
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


        if room["host"] is None:

            room["host"] =
                player_name


        await broadcast(room)


        # ====================================================
        # COMMAND LOOP
        # ====================================================

        while True:

            data =
                await websocket.receive_json()


            command =
                data.get("type")


            # =================================================
            # START / RESTART
            # =================================================

            if command == "start":

                if (
                    player_name
                    !=
                    room["host"]
                ):

                    continue


                if room["phase"] not in (
                    "ЛОББИ",
                    "🏆 ПОБЕДА"
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


                await start_game(
                    room
                )


                await broadcast(
                    room
                )


            # =================================================
            # MAFIA KILL
            # =================================================

            elif command == "kill":

                if room["phase"] != (
                    "🌙 НОЧЬ — МАФИЯ"
                ):

                    continue


                player =
                    room["players"].get(
                        player_name
                    )


                if not player:

                    continue


                if not player["alive"]:

                    continue


                if not is_mafia(
                    player
                ):

                    continue


                target =
                    str(
                        data.get(
                            "target",
                            ""
                        )
                    ).strip()


                if target == player_name:

                    continue


                if not is_alive(
                    room,
                    target
                ):

                    continue


                room[
                    "night_target"
                ] = target


                room["announcement"] = (
                    "🔪 Мафия выбрала цель."
                )


                await broadcast(
                    room
                )


            # =================================================
            # MANIAC KILL
            # =================================================

            elif command == "maniac_kill":

                if room["phase"] != (
                    "🌙 НОЧЬ — МАФИЯ"
                ):

                    continue


                player =
                    room["players"].get(
                        player_name
                    )


                if (
                    not player
                    or
                    not player["alive"]
                    or
                    player["role"]
                    !=
                    "Маньяк"
                ):

                    continue


                target =
                    str(
                        data.get(
                            "target",
                            ""
                        )
                    ).strip()


                if target == player_name:

                    continue


                if not is_alive(
                    room,
                    target
                ):

                    continue


                room[
                    "maniac_target"
                ] = target


                await broadcast(
                    room
                )


            # =================================================
            # DOCTOR
            # =================================================

            elif command == "heal":

                if room["phase"] != (
                    "🌙 НОЧЬ — МАФИЯ"
                ):

                    continue


                player =
                    room["players"].get(
                        player_name
                    )


                if (
                    not player
                    or
                    not player["alive"]
                    or
                    player["role"]
                    !=
                    "Доктор"
                ):

                    continue


                target =
                    str(
                        data.get(
                            "target",
                            ""
                        )
                    ).strip()


                if is_alive(
                    room,
                    target
                ):

                    room[
                        "doctor_target"
                    ] = target


                    room["log"].append(
                        "🩺 Доктор сделал свой выбор."
                    )


                    await broadcast(
                        room
                    )


            # =================================================
            # BODYGUARD
            # =================================================

            elif command == "protect":

                if room["phase"] != (
                    "🌙 НОЧЬ — МАФИЯ"
                ):

                    continue


                player =
                    room["players"].get(
                        player_name
                    )


                if (
                    not player
                    or
                    not player["alive"]
                    or
                    player["role"]
                    !=
                    "Телохранитель"
                ):

                    continue


                target =
                    str(
                        data.get(
                            "target",
                            ""
                        )
                    ).strip()


                if is_alive(
                    room,
                    target
                ):

                    room[
                        "bodyguard_target"
                    ] = target


                    await broadcast(
                        room
                    )


            # =================================================
            # SHERIFF
            # =================================================

            elif command == "inspect":

                if room["phase"] != (
                    "🌙 НОЧЬ — МАФИЯ"
                ):

                    continue


                player =
                    room["players"].get(
                        player_name
                    )


                if (
                    not player
                    or
                    not player["alive"]
                    or
                    player["role"]
                    !=
                    "Шериф"
                ):

                    continue


                target =
                    str(
                        data.get(
                            "target",
                            ""
                        )
                    ).strip()


                target_player =
                    room["players"].get(
                        target
                    )


                if (
                    not target_player
                    or
                    not target_player["alive"]
                ):

                    continue


                if is_mafia(
                    target_player
                ):

                    result =
                        "🔴 МАФИЯ"

                elif (
                    target_player["role"]
                    ==
                    "Маньяк"
                ):

                    result =
                        "🟡 МАНЬЯК"

                else:

                    result =
                        "🟢 НЕ МАФИЯ"


                await websocket.send_json({

                    "type":
                        "info",

                    "message":
                        target +
                        ": " +
                        result

                })


            # =================================================
            # DETECTIVE
            # =================================================

            elif command == "detect":

                if room["phase"] != (
                    "🌙 НОЧЬ — МАФИЯ"
                ):

                    continue


                player =
                    room["players"].get(
                        player_name
                    )


                if (
                    not player
                    or
                    not player["alive"]
                    or
                    player["role"]
                    !=
                    "Детектив"
                ):

                    continue


                target =
                    str(
                        data.get(
                            "target",
                            ""
                        )
                    ).strip()


                target_player =
                    room["players"].get(
                        target
                    )


                if (
                    not target_player
                    or
                    not target_player["alive"]
                ):

                    continue


                await websocket.send_json({

                    "type":
                        "info",

                    "message":
                        target +
                        " — роль: " +
                        target_player[
                            "role"
                        ]

                })


            # =================================================
            # VOTE
            # =================================================

            elif command == "vote":

                if room["phase"] != (
                    "🗳️ ГОЛОСОВАНИЕ"
                ):

                    continue


                player =
                    room["players"].get(
                        player_name
                    )


                if (
                    not player
                    or
                    not player["alive"]
                ):

                    continue


                target =
                    str(
                        data.get(
                            "target",
                            ""
                        )
                    ).strip()


                if target == player_name:

                    continue


                if not is_alive(
                    room,
                    target
                ):

                    continue


                room["votes"][
                    player_name
                ] = target


                room["announcement"] = (
                    f"🗳️ {player_name} "
                    "проголосовал."
                )


                await broadcast(
                    room
                )


    except WebSocketDisconnect:

        pass


    except Exception as error:

        print(
            "WebSocket error:",
            error
        )


    finally:

        if (
            room
            and
            player_name
        ):

            room[
                "connections"
            ].pop(
                websocket,
                None
            )


            # Игрок удаляется
            # только из лобби

            if (
                room["phase"]
                ==
                "ЛОББИ"
                and
                player_name
                in
                room["players"]
            ):

                del room[
                    "players"
                ][
                    player_name
                ]


                if (
                    room["host"]
                    ==
                    player_name
                ):

                    if room["players"]:

                        room["host"] =
                            next(
                                iter(
                                    room[
                                        "players"
                                    ]
                                )
                            )

                    else:

                        room["host"] =
                            None


            await broadcast(room)


# ============================================================
# RUN
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
