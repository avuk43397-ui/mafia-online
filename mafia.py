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

<title>MAFIA ONLINE</title>

<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    min-height: 100vh;

    background:
        radial-gradient(
            circle at 20% 0%,
            rgba(155, 92, 255, .18),
            transparent 35%
        ),
        radial-gradient(
            circle at 90% 100%,
            rgba(255, 60, 90, .12),
            transparent 35%
        ),
        #07070c;

    color: white;

    font-family:
        Arial,
        Helvetica,
        sans-serif;
}


/* ============================================================
   GENERAL
============================================================ */

button,
input,
select {

    font: inherit;
}

button {

    cursor: pointer;
}

.hidden {

    display: none !important;
}


.screen {

    min-height: 100vh;

    display: flex;

    justify-content: center;

    align-items: center;

    padding: 20px;
}


.card {

    width: min(560px, 100%);

    background: rgba(17, 17, 26, .94);

    border:
        1px solid
        rgba(255, 255, 255, .08);

    border-radius: 28px;

    padding: 30px;

    box-shadow:
        0 30px 100px
        rgba(0, 0, 0, .65);
}


.logo {

    text-align: center;

    font-size: 52px;

    font-weight: 900;

    letter-spacing: 7px;

    margin-bottom: 8px;
}


.subtitle {

    text-align: center;

    color: #888896;

    margin-bottom: 30px;

    letter-spacing: 2px;
}


.menu {

    display: grid;

    gap: 12px;

    max-width: 360px;

    margin: auto;
}


.btn {

    border:
        1px solid
        rgba(255, 255, 255, .08);

    background: #191923;

    color: white;

    border-radius: 15px;

    padding: 14px 18px;

    min-height: 48px;

    transition: .2s;
}


.btn:hover {

    transform: translateY(-2px);

    background: #252532;
}


.btn:disabled {

    opacity: .4;

    cursor: not-allowed;

    transform: none;
}


.btn.accent {

    border: 0;

    background:
        linear-gradient(
            135deg,
            #854cff,
            #bd6cff
        );
}


.btn.danger {

    background: #35151e;

    color: #ff9cab;
}


.input {

    width: 100%;

    margin: 7px 0;

    padding: 14px;

    border:
        1px solid
        rgba(255, 255, 255, .08);

    border-radius: 14px;

    background: #0c0c12;

    color: white;

    outline: none;
}


.input:focus {

    border-color: #9b5cff;
}


/* ============================================================
   GAME
============================================================ */

#gameScreen {

    display: none;

    min-height: 100vh;

    padding: 85px 15px 30px;
}


#gameScreen.active {

    display: block;
}


.topbar {

    position: fixed;

    top: 0;

    left: 0;

    right: 0;

    z-index: 20;

    display: flex;

    align-items: center;

    gap: 8px;

    padding: 12px;

    background:
        rgba(7, 7, 12, .88);

    backdrop-filter: blur(15px);

    border-bottom:
        1px solid
        rgba(255, 255, 255, .08);
}


.spacer {

    flex: 1;
}


.pill {

    padding: 8px 12px;

    border-radius: 999px;

    background: #171720;

    border:
        1px solid
        rgba(255, 255, 255, .08);

    font-size: 13px;
}


.game {

    width: min(1200px, 100%);

    margin: auto;
}


.layout {

    display: grid;

    grid-template-columns:
        1fr
        330px;

    gap: 15px;
}


.panel {

    background:
        rgba(17, 17, 26, .94);

    border:
        1px solid
        rgba(255, 255, 255, .08);

    border-radius: 22px;

    padding: 18px;
}


.phase {

    text-align: center;

    padding: 24px;
}


.phase h2 {

    margin: 0 0 10px;

    font-size: 30px;
}


.timer {

    font-size: 35px;

    font-weight: 900;

    color: #ffc857;
}


.announcement {

    color: #d0d0d8;

    min-height: 25px;
}


.players {

    display: grid;

    grid-template-columns:
        repeat(
            auto-fill,
            minmax(150px, 1fr)
        );

    gap: 10px;
}


.player {

    position: relative;

    min-height: 115px;

    padding: 12px;

    border-radius: 17px;

    background: #15151f;

    border:
        1px solid
        rgba(255, 255, 255, .08);
}


.player.dead {

    opacity: .4;

    filter: grayscale(1);
}


.avatar {

    width: 50px;

    height: 50px;

    object-fit: cover;

    border-radius: 50%;

    background: #292936;

    display: block;

    margin-bottom: 8px;
}


.dot {

    display: inline-block;

    width: 8px;

    height: 8px;

    margin-right: 5px;

    border-radius: 50%;

    background: #42e695;
}


.dead .dot {

    background: #777;
}


.playername {

    font-weight: 800;

    word-break: break-word;
}


.host {

    color: #ffc857;

    font-size: 12px;

    margin-top: 4px;
}


.small {

    color: #8f8f9d;

    font-size: 12px;
}


.rolebox {

    margin-top: 18px;

    padding: 16px;

    background: #0c0c12;

    border-radius: 18px;

    border:
        1px solid
        rgba(255, 255, 255, .08);
}


.rolebig {

    font-size: 23px;

    font-weight: 900;

    margin: 5px 0;
}


.actions {

    display: grid;

    grid-template-columns:
        repeat(2, 1fr);

    gap: 7px;

    margin-top: 10px;
}


.log {

    max-height: 400px;

    overflow-y: auto;

    display: flex;

    flex-direction: column;

    gap: 7px;
}


.log div {

    padding: 9px;

    border-radius: 10px;

    background: #0c0c12;

    color: #c9c9d4;

    font-size: 13px;
}


/* ============================================================
   MODAL
============================================================ */

.modal {

    position: fixed;

    inset: 0;

    z-index: 100;

    display: none;

    align-items: center;

    justify-content: center;

    padding: 20px;

    background: rgba(0, 0, 0, .78);
}


.modal.active {

    display: flex;
}


.modalbox {

    width: min(480px, 100%);

    padding: 24px;

    border-radius: 24px;

    background: #15151f;

    border:
        1px solid
        rgba(255, 255, 255, .08);
}


.avatar-preview {

    width: 90px;

    height: 90px;

    object-fit: cover;

    display: block;

    margin: 15px auto;

    border-radius: 50%;

    background: #292936;
}


.row {

    display: flex;

    gap: 8px;
}


.row > * {

    flex: 1;
}


/* ============================================================
   TOAST
============================================================ */

.toast {

    position: fixed;

    left: 50%;

    bottom: 20px;

    transform: translateX(-50%);

    z-index: 200;

    display: none;

    padding: 13px 20px;

    border-radius: 14px;

    background: #222230;

    border:
        1px solid
        rgba(255, 255, 255, .1);
}


.toast.show {

    display: block;
}


.kick {

    position: absolute;

    right: 7px;

    top: 7px;

    border: 0;

    border-radius: 8px;

    padding: 4px 7px;

    background: #451b26;

    color: #ff9aaa;
}


@media (max-width: 800px) {

    .layout {

        grid-template-columns: 1fr;
    }

}


@media (max-width: 450px) {

    .logo {

        font-size: 38px;
    }

    .players {

        grid-template-columns:
            repeat(2, 1fr);
    }

    .actions {

        grid-template-columns: 1fr;
    }

}

</style>

</head>


<body>


<!-- ============================================================
     HOME
============================================================ -->

<div
    id="homeScreen"
    class="screen"
>

    <div class="card">

        <div class="logo">
            MAFIA
        </div>

        <div class="subtitle">
            ONLINE • NIGHT • LIES • SURVIVAL
        </div>

        <div class="menu">

            <button
                class="btn accent"
                onclick="openPlay()"
            >
                🎮 Играть
            </button>

            <button
                class="btn"
                onclick="openSettings()"
            >
                ⚙️ Настройки
            </button>

            <button
                class="btn"
                onclick="openProfile()"
            >
                👤 Профиль
            </button>

        </div>

    </div>

</div>


<!-- ============================================================
     PLAY
============================================================ -->

<div
    id="playScreen"
    class="screen hidden"
>

    <div class="card">

        <h2>
            🎮 Играть
        </h2>

        <button
            class="btn accent"
            style="width:100%"
            onclick="createRoom()"
        >
            ➕ Создать игру
        </button>

        <div
            style="
                text-align:center;
                color:#888;
                margin:15px
            "
        >
            или
        </div>

        <input
            id="roomInput"
            class="input"
            maxlength="4"
            placeholder="Код комнаты"
        >

        <button
            class="btn"
            style="width:100%"
            onclick="joinRoom()"
        >
            🔑 Ввести код
        </button>

        <button
            class="btn"
            style="
                width:100%;
                margin-top:10px
            "
            onclick="showHome()"
        >
            ← Назад
        </button>

    </div>

</div>


<!-- ============================================================
     GAME
============================================================ -->

<div
    id="gameScreen"
>

    <div class="topbar">

        <span
            id="roomPill"
            class="pill"
        >
            Комната
        </span>

        <span
            id="phasePill"
            class="pill"
        >
            ЛОББИ
        </span>

        <span
            id="timer"
            class="pill"
        >
            —
        </span>

        <div class="spacer"></div>

        <button
            class="btn"
            onclick="openProfile()"
        >
            👤
        </button>

        <button
            class="btn"
            onclick="leaveGame()"
        >
            🚪
        </button>

    </div>


    <div class="game">

        <div class="layout">

            <main>

                <div
                    class="panel phase"
                >

                    <h2 id="phaseTitle">
                        ЛОББИ
                    </h2>

                    <div
                        id="announcement"
                        class="announcement"
                    >
                        Ожидание игроков...
                    </div>

                    <div
                        id="roleBox"
                        class="rolebox hidden"
                    >
                    </div>

                </div>


                <div
                    class="panel"
                    style="margin-top:15px"
                >

                    <h3>
                        👥 Игроки
                        <span
                            id="playerCount"
                            class="small"
                        >
                        </span>
                    </h3>

                    <div
                        id="players"
                        class="players"
                    >
                    </div>

                </div>

            </main>


            <aside>

                <div class="panel">

                    <h3>
                        📜 События
                    </h3>

                    <div
                        id="log"
                        class="log"
                    >
                    </div>

                </div>

            </aside>

        </div>

    </div>

</div>


<!-- ============================================================
     PROFILE
============================================================ -->

<div
    id="profileModal"
    class="modal"
>

    <div class="modalbox">

        <h2>
            👤 Профиль
        </h2>

        <img
            id="avatarPreview"
            class="avatar-preview"
            alt=""
        >

        <input
            id="profileName"
            class="input"
            maxlength="18"
            placeholder="Твоё имя"
        >

        <input
            id="avatarFile"
            class="input"
            type="file"
            accept="image/png,image/jpeg,image/webp,image/gif"
        >

        <label class="small">
            Цвет профиля
        </label>

        <input
            id="profileColor"
            class="input"
            type="color"
            value="#9b5cff"
        >

        <div class="row">

            <button
                class="btn accent"
                onclick="saveProfile()"
            >
                Сохранить
            </button>

            <button
                class="btn"
                onclick="closeModals()"
            >
                Закрыть
            </button>

        </div>

    </div>

</div>


<!-- ============================================================
     SETTINGS
============================================================ -->

<div
    id="settingsModal"
    class="modal"
>

    <div class="modalbox">

        <h2>
            ⚙️ Настройки
        </h2>

        <button
            id="soundButton"
            class="btn"
            style="width:100%"
            onclick="toggleSound()"
        >
            🔊 Звуки: ВКЛ
        </button>

        <button
            class="btn"
            style="
                width:100%;
                margin-top:10px
            "
            onclick="closeModals()"
        >
            Готово
        </button>

    </div>

</div>


<div
    id="toast"
    class="toast"
>
</div>


<script>

let ws = null;

let state = null;

let currentRoom = "";

let soundEnabled =
    localStorage.getItem(
        "mafiaSound"
    ) !== "off";


let profile = {

    name:
        localStorage.getItem(
            "mafiaName"
        ) || "Игрок",

    avatar:
        localStorage.getItem(
            "mafiaAvatar"
        ) || "",

    color:
        localStorage.getItem(
            "mafiaColor"
        ) || "#9b5cff"

};


const ROLE_INFO = {

    "Мафия":
        ["🔴", "Ночью выбирает жертву."],

    "Дон":
        ["👑", "Глава мафии."],

    "Доктор":
        ["🩺", "Ночью спасает игрока."],

    "Шериф":
        ["🔎", "Один раз за игру проверяет игрока."],

    "Телохранитель":
        ["🛡️", "Ночью защищает игрока."],

    "Маньяк":
        ["🔪", "Ночью убивает игроков."],

    "Детектив":
        ["🕵️", "Ночью узнаёт точную роль."],

    "Мирный":
        ["🟢", "Голосует днём."]

};


/* ============================================================
   HELPERS
============================================================ */

function $(id) {

    return document.getElementById(id);

}


function toast(message) {

    const element =
        $("toast");

    element.textContent =
        message;

    element.classList.add(
        "show"
    );

    setTimeout(
        () => {
            element.classList.remove(
                "show"
            );
        },
        2500
    );

}


function escapeHTML(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


function showHome() {

    $("homeScreen")
        .classList.remove(
            "hidden"
        );

    $("homeScreen")
        .style.display = "flex";

    $("playScreen")
        .classList.add(
            "hidden"
        );

    $("playScreen")
        .style.display = "none";

    $("gameScreen")
        .classList.remove(
            "active"
        );

}


function openPlay() {

    $("homeScreen")
        .style.display = "none";

    $("playScreen")
        .classList.remove(
            "hidden"
        );

    $("playScreen")
        .style.display = "flex";

}


function openSettings() {

    $("settingsModal")
        .classList.add(
            "active"
        );

    updateSoundButton();

}


function closeModals() {

    document
        .querySelectorAll(".modal")
        .forEach(
            element =>
                element.classList.remove(
                    "active"
                )
        );

}


/* ============================================================
   PROFILE
============================================================ */

function openProfile() {

    $("profileName").value =
        profile.name;

    $("profileColor").value =
        profile.color;

    $("avatarPreview").src =
        profile.avatar || "";

    $("profileModal")
        .classList.add(
            "active"
        );

}


$("avatarFile")
    .addEventListener(
        "change",
        function(event) {

            const file =
                event.target.files[0];

            if (!file) {
                return;
            }

            if (
                file.size >
                400000
            ) {

                toast(
                    "Аватар слишком большой. Максимум 400 КБ."
                );

                return;

            }

            const reader =
                new FileReader();

            reader.onload =
                function() {

                    profile.avatar =
                        reader.result;

                    $("avatarPreview")
                        .src =
                        reader.result;

                };

            reader.readAsDataURL(
                file
            );

        }
    );


function saveProfile() {

    profile.name =
        (
            $("profileName")
                .value
                .trim()
            ||
            "Игрок"
        ).slice(
            0,
            18
        );


    profile.color =
        $("profileColor")
            .value;


    localStorage.setItem(
        "mafiaName",
        profile.name
    );

    localStorage.setItem(
        "mafiaAvatar",
        profile.avatar
    );

    localStorage.setItem(
        "mafiaColor",
        profile.color
    );


    if (
        ws &&
        ws.readyState === 1
    ) {

        ws.send(
            JSON.stringify({

                type:
                    "profile",

                name:
                    profile.name,

                avatar:
                    profile.avatar,

                color:
                    profile.color

            })
        );

    }


    closeModals();

    toast(
        "Профиль сохранён"
    );

}


/* ============================================================
   SOUND
============================================================ */

function updateSoundButton() {

    $("soundButton")
        .textContent =
        soundEnabled
        ? "🔊 Звуки: ВКЛ"
        : "🔇 Звуки: ВЫКЛ";

}


function toggleSound() {

    soundEnabled =
        !soundEnabled;

    localStorage.setItem(
        "mafiaSound",
        soundEnabled
            ? "on"
            : "off"
    );

    updateSoundButton();

}


/* ============================================================
   CREATE / JOIN
============================================================ */

async function createRoom() {

    try {

        const response =
            await fetch(
                "/create"
            );

        const data =
            await response.json();

        connect(
            data.room
        );

    }
    catch {

        toast(
            "Не удалось создать комнату"
        );

    }

}


function joinRoom() {

    const code =
        $("roomInput")
            .value
            .trim()
            .toUpperCase();


    if (
        !/^\d{4}$/.test(
            code
        )
    ) {

        toast(
            "Код должен состоять из 4 цифр"
        );

        return;

    }


    connect(code);

}


/* ============================================================
   WEBSOCKET
============================================================ */

function connect(code) {

    currentRoom =
        code;


    if (ws) {

        try {
            ws.close();
        }
        catch {}

    }


    const protocol =
        location.protocol === "https:"
        ? "wss://"
        : "ws://";


    ws =
        new WebSocket(
            protocol +
            location.host +
            "/ws"
        );


    ws.onopen =
        function() {

            ws.send(
                JSON.stringify({

                    type:
                        "join",

                    room:
                        code,

                    name:
                        profile.name,

                    avatar:
                        profile.avatar,

                    color:
                        profile.color

                })
            );

        };


    ws.onmessage =
        function(event) {

            const data =
                JSON.parse(
                    event.data
                );


            if (
                data.type ===
                "error"
            ) {

                toast(
                    data.message
                );

                return;

            }


            if (
                data.type ===
                "info"
            ) {

                toast(
                    data.message
                );

                return;

            }


            if (
                data.type ===
                "state"
            ) {

                state =
                    data;

                renderGame();

            }

        };


    ws.onclose =
        function() {

            if (
                $("gameScreen")
                    .classList
                    .contains(
                        "active"
                    )
            ) {

                toast(
                    "Соединение с игрой закрыто"
                );

            }

        };


    ws.onerror =
        function() {

            toast(
                "Ошибка подключения"
            );

        };

}


/* ============================================================
   SEND
============================================================ */

function send(
    type,
    target = ""
) {

    if (
        !ws ||
        ws.readyState !== 1
    ) {

        return;

    }


    ws.send(
        JSON.stringify({

            type:
                type,

            target:
                target

        })
    );

}


/* ============================================================
   GAME RENDER
============================================================ */

function renderGame() {

    $("homeScreen")
        .style.display = "none";

    $("playScreen")
        .style.display = "none";

    $("gameScreen")
        .classList.add(
            "active"
        );


    $("roomPill")
        .textContent =
        "Комната " +
        state.room;


    $("phasePill")
        .textContent =
        state.phase;


    $("phaseTitle")
        .textContent =
        state.phase;


    $("timer")
        .textContent =
        state.time > 0
        ? "⏱ " +
          state.time +
          "с"
        : "—";


    $("announcement")
        .textContent =
        state.announcement ||
        "";


    renderRole();

    renderPlayers();

    renderLog();

}


function renderRole() {

    const box =
        $("roleBox");


    if (!state.role) {

        box.classList.add(
            "hidden"
        );

        return;

    }


    const info =
        ROLE_INFO[
            state.role
        ] ||
        ["🎭", ""];


    box.classList.remove(
        "hidden"
    );


    box.innerHTML =

        "<div class='small'>ТВОЯ РОЛЬ</div>" +

        "<div class='rolebig'>" +

        info[0] +

        " " +

        escapeHTML(
            state.role
        ) +

        "</div>" +

        "<div class='small'>" +

        info[1] +

        "</div>";

}


/* ============================================================
   PLAYERS
============================================================ */

function renderPlayers() {

    const container =
        $("players");


    container.innerHTML =
        "";


    $("playerCount")
        .textContent =
        "(" +
        state.players.length +
        "/12)";


    state.players.forEach(
        function(player) {

            const element =
                document.createElement(
                    "div"
                );


            element.className =
                "player" +
                (
                    player.alive
                    ? ""
                    : " dead"
                );


            element.style.borderColor =
                player.color ||
                "#9b5cff";


            let html = "";


            html +=

                "<img " +

                "class='avatar' " +

                "src='" +

                (
                    player.avatar ||
                    ""
                ) +

                "'>";


            html +=

                "<div>" +

                "<span class='dot'></span>" +

                "<span class='playername'>" +

                escapeHTML(
                    player.name
                ) +

                "</span>" +

                "</div>";


            if (
                player.name ===
                state.host
            ) {

                html +=

                    "<div class='host'>" +

                    "👑 ХОСТ" +

                    "</div>";

            }


            if (
                !player.alive
            ) {

                html +=

                    "<div class='small'>" +

                    "💀 ВЫБЫЛ" +

                    "</div>";

            }


            /*
             * ACTIONS
             */

            let actions =
                "";


            if (
                state.alive &&
                player.alive &&
                player.name !== profile.name
            ) {


                /*
                 * NIGHT
                 */

                if (
                    state.phase ===
                    NIGHT
                ) {


                    if (
                        state.role ===
                            "Мафия" ||
                        state.role ===
                            "Дон"
                    ) {

                        actions +=

                            actionButton(
                                "🔪 Убить",
                                "kill",
                                player.name
                            );

                    }


                    if (
                        state.role ===
                        "Маньяк"
                    ) {

                        actions +=

                            actionButton(
                                "🔪 Убить",
                                "maniac_kill",
                                player.name
                            );

                    }


                    if (
                        state.role ===
                        "Доктор"
                    ) {

                        actions +=

                            actionButton(
                                "🩺 Лечить",
                                "heal",
                                player.name
                            );

                    }


                    if (
                        state.role ===
                        "Телохранитель"
                    ) {

                        actions +=

                            actionButton(
                                "🛡️ Защитить",
                                "protect",
                                player.name
                            );

                    }


                    if (
                        state.role ===
                            "Шериф" &&
                        !state.sheriff_used
                    ) {

                        actions +=

                            actionButton(
                                "🔎 Проверить",
                                "inspect",
                                player.name
                            );

                    }


                    if (
                        state.role ===
                        "Детектив"
                    ) {

                        actions +=

                            actionButton(
                                "🕵️ Узнать роль",
                                "detect",
                                player.name
                            );

                    }

                }


                /*
                 * VOTE
                 */

                if (
                    state.phase ===
                    VOTE
                ) {

                    actions +=

                        actionButton(
                            "🗳️ Голос",
                            "vote",
                            player.name
                        );

                }

            }


            /*
             * HOST KICK
             */

            if (
                state.host ===
                    profile.name &&
                state.phase ===
                    LOBBY &&
                player.name !==
                    profile.name
            ) {

                actions +=

                    "<button " +

                    "class='kick' " +

                    "onclick='kickPlayer(\"" +

                    encodeURIComponent(
                        player.name
                    ) +

                    "\")'>" +

                    "✕" +

                    "</button>";

            }


            html +=

                "<div class='actions'>" +

                actions +

                "</div>";


            element.innerHTML =
                html;


            container.appendChild(
                element
            );

        }
    );


    /*
     * HOST CONTROLS
     */

    if (
        state.phase ===
            LOBBY &&
        state.host ===
            profile.name
    ) {

        const controls =
            document.createElement(
                "div"
            );


        controls.style.marginTop =
            "15px";


        const start =
            document.createElement(
                "button"
            );


        start.className =
            "btn accent";


        start.style.width =
            "100%";


        start.textContent =

            state.players.length >= 4

            ? "🎬 Начать игру"

            : "🔒 Нужно минимум 4 игрока";


        start.disabled =
            state.players.length < 4;


        start.onclick =
            function() {

                send(
                    "start"
                );

            };


        controls.appendChild(
            start
        );


        if (
            state.players.length > 1
        ) {

            const select =
                document.createElement(
                    "select"
                );


            select.className =
                "input";


            select.innerHTML =

                "<option value=''>" +

                "👑 Передать хоста..." +

                "</option>";


            state.players
                .filter(
                    p =>
                        p.name !==
                        profile.name
                )
                .forEach(
                    function(p) {

                        const option =
                            document.createElement(
                                "option"
                            );

                        option.value =
                            p.name;

                        option.textContent =
                            p.name;

                        select.appendChild(
                            option
                        );

                    }
                );


            select.onchange =
                function() {

                    if (
                        select.value
                    ) {

                        send(
                            "transfer_host",
                            select.value
                        );

                    }

                };


            controls.appendChild(
                select
            );

        }


        container.appendChild(
            controls
        );

    }

}


function actionButton(
    text,
    type,
    target
) {

    return (

        "<button " +

        "class='btn' " +

        "onclick='send(\"" +

        type +

        "\", decodeURIComponent(\"" +

        encodeURIComponent(
            target
        ) +

        "\"))'>" +

        text +

        "</button>"

    );

}


function kickPlayer(
    encodedName
) {

    const name =
        decodeURIComponent(
            encodedName
        );


    if (
        confirm(
            "Исключить " +
            name +
            "?"
        )
    ) {

        send(
            "kick",
            name
        );

    }

}


/* ============================================================
   LOG
============================================================ */

function renderLog() {

    const log =
        $("log");


    log.innerHTML =
        "";


    [...state.log]
        .reverse()
        .forEach(
            function(message) {

                const div =
                    document.createElement(
                        "div"
                    );


                div.textContent =
                    message;


                log.appendChild(
                    div
                );

            }
        );

}


/* ============================================================
   LEAVE
============================================================ */

function leaveGame() {

    if (ws) {

        try {

            ws.close();

        }
        catch {}

    }


    ws = null;

    state = null;

    $("gameScreen")
        .classList
        .remove(
            "active"
        );


    showHome();

}

</script>

</body>

</html>
"""


# ============================================================
# ROOM
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


def now():

    return asyncio.get_running_loop().time()


# ============================================================
# ROLES
# ============================================================

def role_set(count):

    if count < 4:

        return None


    if count == 4:

        return [
            "Мафия",
            "Мирный",
            "Мирный",
            "Мирный"
        ]


    if count == 5:

        return [
            "Мафия",
            "Доктор",
            "Мирный",
            "Мирный",
            "Мирный"
        ]


    if count == 6:

        return [
            "Мафия",
            "Шериф",
            "Доктор",
            "Мирный",
            "Мирный",
            "Мирный"
        ]


    if count == 7:

        return [
            "Мафия",
            "Мафия",
            "Шериф",
            "Доктор",
            "Мирный",
            "Мирный",
            "Мирный"
        ]


    if count == 8:

        return [
            "Мафия",
            "Дон",
            "Шериф",
            "Доктор",
            "Телохранитель",
            "Мирный",
            "Мирный",
            "Мирный"
        ]


    if count == 9:

        return [
            "Мафия",
            "Дон",
            "Шериф",
            "Доктор",
            "Телохранитель",
            "Маньяк",
            "Мирный",
            "Мирный",
            "Мирный"
        ]


    if count == 10:

        return [
            "Мафия",
            "Дон",
            "Шериф",
            "Доктор",
            "Телохранитель",
            "Маньяк",
            "Детектив",
            "Мирный",
            "Мирный",
            "Мирный"
        ]


    return [
        "Мафия",
        "Мафия",
        "Дон",
        "Шериф",
        "Доктор",
        "Телохранитель",
        "Маньяк",
        "Детектив"
    ] + [
        "Мирный"
    ] * (
        count - 8
    )


def is_mafia(player):

    return player.get(
        "role"
    ) in {
        "Мафия",
        "Дон"
    }


def alive(room, name):

    player = room[
        "players"
    ].get(name)

    return bool(
        player
        and
        player["alive"]
    )


# ============================================================
# STATE
# ============================================================

def state_for(
    room,
    name
):

    player = room[
        "players"
    ].get(name)


    if room["ends"]:

        remaining = max(
            0,
            int(
                room["ends"] - now()
            )
        )

    else:

        remaining = 0


    roles = None


    if room["phase"] == WIN:

        roles = [

            {
                "name":
                    p["name"],

                "role":
                    p["role"],

                "alive":
                    p["alive"]

            }

            for p
            in room[
                "players"
            ].values()

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
            player.get(
                "role"
            )
            if player
            else None,

        "alive":
            player.get(
                "alive",
                False
            )
            if player
            else False,

        "sheriff_used":
            player.get(
                "sheriff_used",
                False
            )
            if player
            else False,

        "players":

            [

                {

                    "name":
                        p["name"],

                    "alive":
                        p["alive"],

                    "avatar":
                        p.get(
                            "avatar",
                            ""
                        ),

                    "color":
                        p.get(
                            "color",
                            "#9b5cff"
                        )

                }

                for p
                in room[
                    "players"
                ].values()

            ],

        "announcement":
            room["announcement"],

        "log":
            room["log"][-80:],

        "roles":
            roles

    }


async def broadcast(room):

    for websocket, name in list(
        room[
            "connections"
        ].items()
    ):

        try:

            await websocket.send_json(
                state_for(
                    room,
                    name
                )
            )

        except Exception:

            room[
                "connections"
            ].pop(
                websocket,
                None
            )


# ============================================================
# ASSIGN ROLES
# ============================================================

def assign_roles(room):

    roles = role_set(
        len(
            room["players"]
        )
    )


    if roles is None:

        return False


    players = list(
        room[
            "players"
        ].values()
    )


    random.shuffle(
        players
    )

    random.shuffle(
        roles
    )


    for player, role in zip(
        players,
        roles
    ):

        player[
            "role"
        ] = role

        player[
            "sheriff_used"
        ] = False


    return True


# ============================================================
# WINNER
# ============================================================

def winner(room):

    alive_players = [

        p

        for p
        in room[
            "players"
        ].values()

        if p["alive"]

    ]


    mafia = [

        p

        for p
        in alive_players

        if is_mafia(p)

    ]


    maniac = [

        p

        for p
        in alive_players

        if p["role"] ==
        "Маньяк"

    ]


    citizens = [

        p

        for p
        in alive_players

        if (
            not is_mafia(p)
            and
            p["role"] !=
            "Маньяк"
        )

    ]


    if not mafia and not maniac:

        room["phase"] = WIN

        room["ends"] = 0

        room[
            "announcement"
        ] = (
            "🟢 Мирные жители победили!"
        )

        room[
            "log"
        ].append(
            "🏆 Победа мирных жителей."
        )

        return True


    if (
        maniac
        and
        len(alive_players) == 1
    ):

        room["phase"] = WIN

        room["ends"] = 0

        room[
            "announcement"
        ] = (
            "🔪 Маньяк победил!"
        )

        room[
            "log"
        ].append(
            "🏆 Победа маньяка."
        )

        return True


    if (
        len(mafia)
        >=
        len(citizens)
        +
        len(maniac)
    ):

        room["phase"] = WIN

        room["ends"] = 0

        room[
            "announcement"
        ] = (
            "🔴 Мафия захватила город!"
        )

        room[
            "log"
        ].append(
            "🏆 Победа мафии."
        )

        return True


    return False


# ============================================================
# NIGHT
# ============================================================

def resolve_night(room):

    protected = {

        target

        for target
        in (
            room[
                "doctor_target"
            ],

            room[
                "bodyguard_target"
            ]
        )

        if target

    }


    deaths = []


    for target in (

        room[
            "night_target"
        ],

        room[
            "maniac_target"
        ]

    ):

        if (

            target

            and

            alive(
                room,
                target
            )

            and

            target
            not in
            protected

            and

            target
            not in
            deaths

        ):

            deaths.append(
                target
            )


    for name in deaths:

        room[
            "players"
        ][name][
            "alive"
        ] = False


        room[
            "log"
        ].append(

            f"💀 Ночью погиб {name}."

        )


    if deaths:

        room[
            "announcement"
        ] = (

            "☀️ Город просыпается. "
            "Ночью произошло убийство."

        )

    else:

        room[
            "announcement"
        ] = (

            "☀️ Город просыпается. "
            "Этой ночью никто не погиб."

        )


    room[
        "night_target"
    ] = None

    room[
        "maniac_target"
    ] = None

    room[
        "doctor_target"
    ] = None

    room[
        "bodyguard_target"
    ] = None


# ============================================================
# START GAME
# ============================================================

async def start_game(room):

    old_task = room.get(
        "game_task"
    )


    if (
        old_task
        and
        not old_task.done()
        and
        old_task
        is not
        asyncio.current_task()
    ):

        old_task.cancel()

        with suppress(
            asyncio.CancelledError
        ):

            await old_task


    for player in room[
        "players"
    ].values():

        player[
            "alive"
        ] = True

        player[
            "role"
        ] = None

        player[
            "sheriff_used"
        ] = False


    room.update({

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

        "log":
            [
                "🎬 Новая игра началась!"
            ],

        "phase":
            NIGHT,

        "ends":
            now() + 15,

        "announcement":
            (
                "🌙 Город засыпает. "
                "Ночные роли просыпаются."
            )

    })


    assign_roles(
        room
    )


    room[
        "game_task"
    ] = asyncio.create_task(
        game_loop(room)
    )


# ============================================================
# GAME LOOP
# ============================================================

async def game_loop(room):

    try:

        while room[
            "phase"
        ] != WIN:


            if room[
                "ends"
            ] > now():

                await broadcast(
                    room
                )

                await asyncio.sleep(
                    min(
                        1,
                        room[
                            "ends"
                        ] - now()
                    )
                )

                continue


            # ==================================================
            # NIGHT
            # ==================================================

            if room[
                "phase"
            ] == NIGHT:

                resolve_night(
                    room
                )


                if winner(
                    room
                ):

                    await broadcast(
                        room
                    )

                    return


                room[
                    "phase"
                ] = DAY


                room[
                    "ends"
                ] = (
                    now() + 8
                )


                room[
                    "announcement"
                ] = (
                    "☀️ День. "
                    "Обсудите события."
                )


                await broadcast(
                    room
                )


                await asyncio.sleep(
                    8
                )


                if winner(
                    room
                ):

                    await broadcast(
                        room
                    )

                    return


                room[
                    "phase"
                ] = VOTE


                room[
                    "ends"
                ] = (
                    now() + 45
                )


                room[
                    "votes"
                ] = {}


                room[
                    "announcement"
                ] = (
                    "🗳️ Голосование началось."
                )


                await broadcast(
                    room
                )


            # ==================================================
            # VOTE
            # ==================================================

            elif room[
                "phase"
            ] == VOTE:

                counts = {}


                for target in room[
                    "votes"
                ].values():

                    counts[
                        target
                    ] = (
                        counts.get(
                            target,
                            0
                        )
                        +
                        1
                    )


                if counts:

                    maximum = max(
                        counts.values()
                    )


                    top = [

                        name

                        for name,
                        count
                        in counts.items()

                        if count ==
                        maximum

                    ]


                    if (

                        len(top) == 1

                        and

                        alive(
                            room,
                            top[0]
                        )

                    ):

                        victim = top[0]


                        room[
                            "players"
                        ][victim][
                            "alive"
                        ] = False


                        room[
                            "log"
                        ].append(

                            f"⚖️ {victim} "
                            f"изгнан голосованием."

                        )


                        room[
                            "announcement"
                        ] = (

                            f"⚖️ {victim} "
                            f"был изгнан."

                        )

                    else:

                        room[
                            "announcement"
                        ] = (
                            "⚖️ Ничья. "
                            "Никто не изгнан."
                        )

                else:

                    room[
                        "announcement"
                    ] = (
                        "🤷 Голосов нет."
                    )


                room[
                    "votes"
                ] = {}


                if winner(
                    room
                ):

                    await broadcast(
                        room
                    )

                    return


                room[
                    "phase"
                ] = NIGHT


                room[
                    "ends"
                ] = (
                    now() + 15
                )


                room[
                    "announcement"
                ] = (
                    "🌙 Город засыпает."
                )


    except asyncio.CancelledError:

        pass


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
async def create():

    code = generate_room_code()


    rooms[
        code
    ] = {

        "code":
            code,

        "host":
            None,

        "players":
            {},

        "connections":
            {},

        "phase":
            LOBBY,

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

        "log":
            [],

        "game_task":
            None

    }


    return {

        "room":
            code,

        "url":
            f"/?room={code}"

    }


# ============================================================
# WEBSOCKET
# ============================================================

@app.websocket("/ws")
async def ws_endpoint(
    websocket: WebSocket
):

    await websocket.accept()


    room = None

    name = None


    try:

        first = (
            await websocket.receive_json()
        )


        if first.get(
            "type"
        ) != "join":

            return


        name = str(
            first.get(
                "name",
                ""
            )
        ).strip()[:18]


        code = str(
            first.get(
                "room",
                ""
            )
        ).strip().upper()


        if (
            not name
            or
            code not in rooms
        ):

            await websocket.send_json({

                "type":
                    "error",

                "message":
                    "Неверное имя или комната."

            })

            return


        room = rooms[
            code
        ]


        if room[
            "phase"
        ] not in {
            LOBBY,
            WIN
        }:

            await websocket.send_json({

                "type":
                    "error",

                "message":
                    "Игра уже идёт."

            })

            return


        if name in room[
            "players"
        ]:

            await websocket.send_json({

                "type":
                    "error",

                "message":
                    "Это имя уже занято."

            })

            return


        if len(
            room[
                "players"
            ]
        ) >= 12:

            await websocket.send_json({

                "type":
                    "error",

                "message":
                    "Максимум 12 игроков."

            })

            return


        room[
            "players"
        ][name] = {

            "name":
                name,

            "alive":
                True,

            "role":
                None,

            "avatar":
                str(
                    first.get(
                        "avatar",
                        ""
                    )
                )[:600000],

            "color":
                str(
                    first.get(
                        "color",
                        "#9b5cff"
                    )
                )[:20],

            "sheriff_used":
                False

        }


        room[
            "connections"
        ][
            websocket
        ] = name


        if room[
            "host"
        ] is None:

            room[
                "host"
            ] = name


        room[
            "log"
        ].append(

            f"🟢 {name} вошёл в комнату."

        )


        await broadcast(
            room
        )


        while True:

            data = (
                await websocket.receive_json()
            )


            player = room[
                "players"
            ].get(name)


            command = data.get(
                "type"
            )


            # ==================================================
            # PROFILE
            # ==================================================

            if (
                command ==
                "profile"
                and
                player
            ):

                new_name = str(
                    data.get(
                        "name",
                        name
                    )
                ).strip()[:18]


                if not new_name:

                    new_name = name


                if new_name != name:

                    if new_name in room[
                        "players"
                    ]:

                        await websocket.send_json({

                            "type":
                                "error",

                            "message":
                                "Имя уже занято."

                        })

                        continue


                    room[
                        "players"
                    ][new_name] = room[
                        "players"
                    ].pop(name)


                    room[
                        "players"
                    ][new_name][
                        "name"
                    ] = new_name


                    room[
                        "connections"
                    ][
                        websocket
                    ] = new_name


                    if room[
                        "host"
                    ] == name:

                        room[
                            "host"
                        ] = new_name


                    name = new_name


                    player = room[
                        "players"
                    ][name]


                player[
                    "avatar"
                ] = str(
                    data.get(
                        "avatar",
                        ""
                    )
                )[:600000]


                player[
                    "color"
                ] = str(
                    data.get(
                        "color",
                        "#9b5cff"
                    )
                )[:20]


                await broadcast(
                    room
                )

                continue


            # ==================================================
            # START
            # ==================================================

            if command == "start":

                if name != room[
                    "host"
                ]:

                    continue


                if len(
                    room[
                        "players"
                    ]
                ) < 4:

                    await websocket.send_json({

                        "type":
                            "error",

                        "message":
                            "Нужно минимум 4 игрока."

                    })

                    continue


                if room[
                    "phase"
                ] in {
                    LOBBY,
                    WIN
                }:

                    await start_game(
                        room
                    )

                    await broadcast(
                        room
                    )


                continue


            # ==================================================
            # KICK
            # ==================================================

            if command == "kick":

                if (
                    name != room[
                        "host"
                    ]
                    or
                    room[
                        "phase"
                    ] != LOBBY
                ):

                    continue


                target = str(
                    data.get(
                        "target",
                        ""
                    )
                )


                if (

                    target
                    in room[
                        "players"
                    ]

                    and

                    target != name

                ):


                    for ws, player_name in list(
                        room[
                            "connections"
                        ].items()
                    ):

                        if player_name == target:

                            try:

                                await ws.send_json({

                                    "type":
                                        "error",

                                    "message":
                                        "Ты был исключён хостом."

                                })


                                await ws.close()

                            except Exception:

                                pass


                            room[
                                "connections"
                            ].pop(
                                ws,
                                None
                            )


                    room[
                        "players"
                    ].pop(
                        target,
                        None
                    )


                    room[
                        "log"
                    ].append(

                        f"👢 {target} "
                        f"был исключён хостом."

                    )


                    await broadcast(
                        room
                    )


                continue


            # ==================================================
            # TRANSFER HOST
            # ==================================================

            if command == "transfer_host":

                if name != room[
                    "host"
                ]:

                    continue


                target = str(
                    data.get(
                        "target",
                        ""
                    )
                )


                if (

                    target
                    in room[
                        "players"
                    ]

                    and

                    target != name

                ):

                    room[
                        "host"
                    ] = target


                    room[
                        "log"
                    ].append(

                        f"👑 {name} "
                        f"передал хоста "
                        f"{target}."

                    )


                    await broadcast(
                        room
                    )


                continue


            # ==================================================
            # DEAD PLAYER
            # ==================================================

            if (
                not player
                or
                not player[
                    "alive"
                ]
            ):

                continue


            target = str(
                data.get(
                    "target",
                    ""
                )
            ).strip()


            if (
                target == name
                or
                not alive(
                    room,
                    target
                )
            ):

                continue


            # ==================================================
            # MAFIA
            # ==================================================

            if (

                command ==
                "kill"

                and

                room[
                    "phase"
                ] == NIGHT

                and

                player[
                    "role"
                ] in {
                    "Мафия",
                    "Дон"
                }

            ):

                room[
                    "night_target"
                ] = target


            # ==================================================
            # MANIAC
            # ==================================================

            elif (

                command ==
                "maniac_kill"

                and

                room[
                    "phase"
                ] == NIGHT

                and

                player[
                    "role"
                ] ==
                "Маньяк"

            ):

                room[
                    "maniac_target"
                ] = target


            # ==================================================
            # DOCTOR
            # ==================================================

            elif (

                command ==
                "heal"

                and

                room[
                    "phase"
                ] == NIGHT

                and

                player[
                    "role"
                ] ==
                "Доктор"

            ):

                room[
                    "doctor_target"
                ] = target


            # ==================================================
            # BODYGUARD
            # ==================================================

            elif (

                command ==
                "protect"

                and

                room[
                    "phase"
                ] == NIGHT

                and

                player[
                    "role"
                ] ==
                "Телохранитель"

            ):

                room[
                    "bodyguard_target"
                ] = target


            # ==================================================
            # SHERIFF
            # ==================================================

            elif (

                command ==
                "inspect"

                and

                room[
                    "phase"
                ] == NIGHT

                and

                player[
                    "role"
                ] ==
                "Шериф"

                and

                not player[
                    "sheriff_used"
                ]

            ):

                player[
                    "sheriff_used"
                ] = True


                target_player =
                    room[
                        "players"
                    ][target]


                if is_mafia(
                    target_player
                ):

                    result =
                        "🔴 МАФИЯ"

                else:

                    result =
                        "🟢 НЕ МАФИЯ"


                await websocket.send_json({

                    "type":
                        "info",

                    "message":
                        f"🔎 {target}: "
                        f"{result}"

                })


            # ==================================================
            # DETECTIVE
            # ==================================================

            elif (

                command ==
                "detect"

                and

                room[
                    "phase"
                ] == NIGHT

                and

                player[
                    "role"
                ] ==
                "Детектив"

            ):

                await websocket.send_json({

                    "type":
                        "info",

                    "message":
                        f"🕵️ {target}: "
                        f"роль «"
                        f"{room['players'][target]['role']}"
                        f"»"

                })


            # ==================================================
            # VOTE
            # ==================================================

            elif (

                command ==
                "vote"

                and

                room[
                    "phase"
                ] == VOTE

            ):

                room[
                    "votes"
                ][name] = target


            await broadcast(
                room
            )


    except WebSocketDisconnect:

        pass


    except Exception as error:

        print(
            "WebSocket error:",
            repr(error)
        )


    finally:

        if room and name:

            room[
                "connections"
            ].pop(
                websocket,
                None
            )


            if name in room[
                "players"
            ]:

                room[
                    "players"
                ].pop(
                    name,
                    None
                )


                room[
                    "votes"
                ].pop(
                    name,
                    None
                )


                room[
                    "log"
                ].append(

                    f"🔴 {name} "
                    f"вышел из игры."

                )


                # ==========================================
                # HOST LEFT
                # ==========================================

                if room[
                    "host"
                ] == name:

                    room[
                        "host"
                    ] = next(
                        iter(
                            room[
                                "players"
                            ]
                        ),
                        None
                    )


                    if room[
                        "host"
                    ]:

                        room[
                            "log"
                        ].append(

                            f"👑 Новый хост: "
                            f"{room['host']}"

                        )


                # ==========================================
                # EMPTY ROOM
                # ==========================================

                if not room[
                    "players"
                ]:

                    task = room.get(
                        "game_task"
                    )


                    if (
                        task
                        and
                        not task.done()
                    ):

                        task.cancel()


                    rooms.pop(
                        room[
                            "code"
                        ],
                        None
                    )

                else:

                    await broadcast(
                        room
                    )


# ============================================================
# MAIN
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
