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


HTML = r"""<!doctype html>
<html lang="ru">

<head>

<meta charset="utf-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>

<title>Mafia Online</title>

<style>

:root {
    --accent: #9b5cff;
    --bg: #080a10;
    --panel: #10131d;
    --panel2: #151a27;
    --text: #f5f7ff;
    --muted: #8992a7;
    --danger: #ff4d67;
    --good: #39d98a;
    --gold: #f4c95d;
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background:
        radial-gradient(
            circle at 20% 0%,
            #20123a 0,
            #080a10 42%
        );
    color: var(--text);
    font-family: Inter, system-ui, Arial;
    min-height: 100vh;
}

button,
input,
select {
    font: inherit;
}

button {
    cursor: pointer;
    border: 0;
}

.hidden {
    display: none !important;
}


/* TOP */

.top {
    height: 68px;

    border-bottom:
        1px solid #ffffff12;

    background:
        #080a10cc;

    backdrop-filter:
        blur(16px);

    display: flex;

    align-items: center;

    justify-content:
        space-between;

    padding:
        0 22px;

    position:
        sticky;

    top: 0;

    z-index: 5;
}

.logo {
    font-size: 21px;

    font-weight: 900;

    letter-spacing: 2px;
}

.logo b {
    color:
        var(--accent);
}

.topright {
    display: flex;

    gap: 8px;

    align-items: center;
}

.pill {
    background:
        #ffffff0c;

    border:
        1px solid #ffffff12;

    padding:
        8px 12px;

    border-radius:
        12px;

    color:
        #cbd2e5;
}


/* CONTAINER */

.container {
    max-width:
        1250px;

    margin:
        22px auto;

    padding:
        0 16px;
}

.grid {
    display:
        grid;

    grid-template-columns:
        1.3fr .7fr;

    gap:
        16px;
}


/* PANEL */

.panel {
    background:
        linear-gradient(
            180deg,
            #111521f2,
            #0c0f17f2
        );

    border:
        1px solid #ffffff12;

    border-radius:
        20px;

    padding:
        18px;

    box-shadow:
        0 20px 60px #0006;
}

h2 {
    margin:
        0 0 14px;

    font-size:
        17px;
}


/* ANNOUNCEMENT */

.announcement {
    padding:
        14px 16px;

    border-radius:
        15px;

    background:
        #ffffff08;

    border:
        1px solid #ffffff10;

    margin-bottom:
        16px;

    font-weight:
        800;
}


/* PLAYERS */

.players {
    display:
        grid;

    grid-template-columns:
        repeat(
            auto-fill,
            minmax(
                220px,
                1fr
            )
        );

    gap:
        10px;
}

.player {
    background:
        var(--panel2);

    border:
        1px solid #ffffff0d;

    border-radius:
        16px;

    padding:
        11px;

    display:
        flex;

    align-items:
        center;

    gap:
        10px;

    position:
        relative;

    transition:
        .2s;
}

.player:hover {
    transform:
        translateY(-2px);

    border-color:
        var(--accent);
}

.avatar {
    width:
        46px;

    height:
        46px;

    border-radius:
        14px;

    object-fit:
        cover;

    background:
        #272c3b;

    display:
        grid;

    place-items:
        center;

    font-weight:
        900;

    flex:
        none;
}

.pname {
    font-weight:
        800;
}

.sub {
    font-size:
        12px;

    color:
        var(--muted);

    margin-top:
        3px;
}

.dead {
    opacity:
        .45;

    filter:
        grayscale(1);
}

.host {
    color:
        var(--gold);
}


/* BUTTONS */

.actions {
    display:
        flex;

    flex-wrap:
        wrap;

    gap:
        8px;

    margin-top:
        15px;

    align-items:
        center;
}

.btn {
    background:
        #ffffff0d;

    color:
        #fff;

    border:
        1px solid #ffffff12;

    border-radius:
        12px;

    padding:
        10px 13px;

    font-weight:
        800;

    transition:
        .15s;
}

.btn:hover {
    border-color:
        var(--accent);

    transform:
        translateY(-1px);
}

.accent {
    background:
        var(--accent);
}

.danger {
    background:
        #8f2435;
}

.gold {
    background:
        #6e5314;
}

.good {
    background:
        #176b49;
}


/* LOG */

.log {
    height:
        430px;

    overflow:
        auto;

    background:
        #090c13;

    border-radius:
        14px;

    padding:
        12px;

    font-size:
        13px;

    line-height:
        1.55;
}

.log div {
    padding:
        4px 0;

    border-bottom:
        1px solid #ffffff06;
}


/* TIMER */

.timer {
    font-size:
        25px;

    font-weight:
        900;

    color:
        var(--accent);
}


/* RESULT */

.result {
    margin-top:
        14px;

    padding:
        14px;

    border-radius:
        14px;

    background:
        #ffffff08;
}


/* MODAL */

.modal {
    position:
        fixed;

    inset:
        0;

    background:
        #000a;

    display:
        grid;

    place-items:
        center;

    z-index:
        20;

    padding:
        16px;
}

.modalbox {
    width:
        min(
            560px,
            100%
        );

    background:
        #10131d;

    border:
        1px solid #ffffff18;

    border-radius:
        22px;

    padding:
        22px;

    box-shadow:
        0 30px 100px #000;
}

input[type="text"] {
    width:
        100%;

    padding:
        12px;

    border-radius:
        12px;

    border:
        1px solid #ffffff15;

    background:
        #080b12;

    color:
        #fff;

    outline:
        0;

    margin:
        7px 0 12px;
}

input[type="file"] {
    width:
        100%;

    margin:
        8px 0 15px;

    color:
        #bbc2d4;
}

select {
    padding:
        10px;

    border-radius:
        12px;

    background:
        #090c13;

    color:
        white;

    border:
        1px solid #ffffff15;
}

.colors {
    display:
        flex;

    gap:
        9px;

    margin:
        8px 0 16px;

    flex-wrap:
        wrap;
}

.sw {
    width:
        30px;

    height:
        30px;

    border-radius:
        50%;

    border:
        2px solid transparent;
}

.sw.active {
    border-color:
        #fff;
}


/* TOAST */

.toast {
    position:
        fixed;

    right:
        18px;

    bottom:
        18px;

    z-index:
        30;

    background:
        #161b28;

    border:
        1px solid #ffffff18;

    border-radius:
        14px;

    padding:
        13px 16px;

    box-shadow:
        0 15px 40px #0008;
}


/* MOBILE */

@media(max-width:850px) {

    .grid {
        grid-template-columns:
            1fr;
    }

    .log {
        height:
            250px;
    }

    .players {
        grid-template-columns:
            1fr;
    }

    .topright .pill {
        display:
            none;
    }

}

</style>

</head>


<body>


<header class="top">

<div class="logo">
    MAFIA <b>ONLINE</b>
</div>


<div class="topright">

<span
    id="roomPill"
    class="pill"
>
    Комната —
</span>


<span
    id="phasePill"
    class="pill"
>
    ЛОББИ
</span>


<button
    class="btn"
    onclick="openProfile()"
>
    👤 Профиль
</button>


<button
    class="btn"
    onclick="openTheme()"
>
    🎨
</button>

</div>

</header>


<div class="container">


<div
    id="announcement"
    class="announcement"
>
    Подключение...
</div>


<div class="grid">


<section class="panel">

<h2>

👥 Игроки

<span
    id="timer"
    class="timer"
    style="float:right"
>
</span>

</h2>


<div
    id="players"
    class="players"
>
</div>


<div
    id="hostControls"
    class="actions hidden"
>
</div>


<div
    id="actions"
    class="actions"
>
</div>


<div
    id="result"
    class="result hidden"
>
</div>

</section>


<section class="panel">

<h2>
    📜 События
</h2>

<div
    id="log"
    class="log"
>
</div>

</section>


</div>

</div>


<!-- PROFILE -->


<div
    id="profileModal"
    class="modal hidden"
>

<div class="modalbox">

<h2>
    👤 Профиль
</h2>


<label>
    Имя
</label>


<input
    id="profileName"
    type="text"
    maxlength="18"
>


<label>
    Аватарка
</label>


<input
    id="avatarFile"
    type="file"
    accept="image/png,image/jpeg,image/webp,image/gif"
>


<label>
    Цвет профиля
</label>


<div
    class="colors"
    id="colors"
>
</div>


<div class="actions">

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


<!-- THEME -->


<div
    id="themeModal"
    class="modal hidden"
>

<div class="modalbox">

<h2>
    🎨 Цвет интерфейса
</h2>


<div
    class="colors"
    id="themeColors"
>
</div>


<div class="actions">

<button
    class="btn"
    onclick="closeModals()"
>
    Готово
</button>

</div>

</div>

</div>


<div
    id="toast"
    class="toast hidden"
>
</div>


<script>


let ws = null;

let me = "";

let room = "";

let state = null;

let avatar = "";

let profileColor = "#9b5cff";


const accents = [
    "#9b5cff",
    "#ff4d67",
    "#39d98a",
    "#38a8ff",
    "#f4c95d",
    "#ff7a45",
    "#e85dff"
];


function $(id) {
    return document.getElementById(id);
}


function toast(text) {

    $("toast").textContent = text;

    $("toast").classList.remove("hidden");

    setTimeout(
        () => $("toast").classList.add("hidden"),
        3000
    );
}


function send(data) {

    if (
        ws &&
        ws.readyState === 1
    ) {
        ws.send(
            JSON.stringify(data)
        );
    }

}


function esc(value) {

    return String(value).replace(
        /[&<>"']/g,
        function(c) {

            return {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;"
            }[c];

        }
    );

}


function openProfile() {

    $("profileName").value = me;

    $("profileModal")
        .classList
        .remove("hidden");

}


function openTheme() {

    $("themeModal")
        .classList
        .remove("hidden");

}


function closeModals() {

    document
        .querySelectorAll(".modal")
        .forEach(
            x => x.classList.add("hidden")
        );

}


function makeColors(
    id,
    callback
) {

    $(id).innerHTML =
        accents
        .map(
            c =>
                `<button
                    class="sw ${c === profileColor ? "active" : ""}"
                    style="background:${c}"
                    onclick="${callback}('${c}')"
                ></button>`
        )
        .join("");

}


function chooseColor(c) {

    profileColor = c;

    document
        .documentElement
        .style
        .setProperty(
            "--accent",
            c
        );

    makeColors(
        "colors",
        "chooseColor"
    );

}


function chooseTheme(c) {

    document
        .documentElement
        .style
        .setProperty(
            "--accent",
            c
        );

    localStorage.setItem(
        "accent",
        c
    );

    makeColors(
        "themeColors",
        "chooseTheme"
    );

}


function saveProfile() {

    const file =
        $("avatarFile").files[0];

    const name =
        $("profileName")
        .value
        .trim();


    if (!name) {

        toast("Введите имя");

        return;

    }


    me = name;


    if (file) {

        const reader =
            new FileReader();


        reader.onload =
            function() {

                avatar =
                    reader.result;

                localStorage.setItem(
                    "mafia_profile",
                    JSON.stringify({
                        name: me,
                        avatar: avatar,
                        color: profileColor
                    })
                );


                send({
                    type: "profile",
                    name: me,
                    avatar: avatar,
                    color: profileColor
                });

            };


        reader.readAsDataURL(file);

    } else {

        localStorage.setItem(
            "mafia_profile",
            JSON.stringify({
                name: me,
                avatar: avatar,
                color: profileColor
            })
        );


        send({
            type: "profile",
            name: me,
            avatar: avatar,
            color: profileColor
        });

    }


    closeModals();

}


function connect() {

    const proto =
        location.protocol === "https:"
            ? "wss"
            : "ws";


    ws = new WebSocket(
        `${proto}://${location.host}/ws`
    );


    ws.onopen =
        function() {

            send({
                type: "join",
                name: me,
                room: room,
                avatar: avatar,
                color: profileColor
            });

        };


    ws.onmessage =
        function(event) {

            const data =
                JSON.parse(event.data);


            if (data.type === "error") {

                toast(
                    "❌ " +
                    data.message
                );

                return;

            }


            if (data.type === "info") {

                toast(
                    data.message
                );

                return;

            }


            if (data.type === "state") {

                state = data;

                render();

            }

        };


    ws.onclose =
        function() {

            toast(
                "🔴 Соединение закрыто."
            );

        };

}


function render() {

    $("roomPill")
        .textContent =
        "Комната " +
        state.room;


    $("phasePill")
        .textContent =
        state.phase;


    $("announcement")
        .textContent =
        state.announcement;


    $("timer")
        .textContent =
        state.time
            ? `00:${String(state.time).padStart(2, "0")}`
            : "";


    $("log").innerHTML =
        state.log
        .map(
            x =>
                `<div>${esc(x)}</div>`
        )
        .join("");


    $("players").innerHTML =
        state.players
        .map(
            function(p) {

                const avatarHTML =
                    p.avatar
                        ?
                        `<img
                            class="avatar"
                            src="${esc(p.avatar)}"
                        >`
                        :
                        `<div
                            class="avatar"
                            style="background:${esc(p.color || "#272c3b")}"
                        >
                            ${esc(
                                p.name[0] || "?"
                            )}
                        </div>`;


                const host =
                    p.name === state.host
                        ?
                        ` <span class="host">👑</span>`
                        :
                        "";


                const dead =
                    p.alive
                        ? ""
                        : " dead";


                const admin =
                    me === state.host &&
                    p.name !== me &&
                    state.phase === "ЛОББИ";


                const adminButton =
                    admin
                        ?
                        `<button
                            class="btn danger"
                            onclick="kick('${esc(p.name)}')"
                        >
                            Кик
                        </button>`
                        :
                        "";


                return `
                    <div class="player${dead}">

                        ${avatarHTML}

                        <div style="flex:1">

                            <div class="pname">

                                ${esc(p.name)}

                                ${host}

                            </div>

                            <div class="sub">

                                ${
                                    p.alive
                                    ?
                                    "🟢 В игре"
                                    :
                                    "💀 Мёртв"
                                }

                                ${
                                    p.role &&
                                    state.phase === "🏆 ИГРА ОКОНЧЕНА"
                                    ?
                                    " • " +
                                    esc(p.role)
                                    :
                                    ""
                                }

                            </div>

                        </div>

                        ${adminButton}

                    </div>
                `;

            }
        )
        .join("");


    $("hostControls")
        .innerHTML = "";


    if (
        me === state.host &&
        state.phase === "ЛОББИ"
    ) {

        $("hostControls")
            .innerHTML =
                `
                <button
                    class="btn gold"
                    onclick="start()"
                >
                    ▶ Начать игру
                </button>
                `;

    }


    if (
        me === state.host &&
        state.phase !== "ЛОББИ" &&
        state.phase !== "🏆 ИГРА ОКОНЧЕНА"
    ) {

        $("hostControls")
            .innerHTML =
                state.players
                .filter(
                    p =>
                        p.name !== me &&
                        p.alive
                )
                .map(
                    p =>
                        `
                        <button
                            class="btn"
                            onclick="transfer('${esc(p.name)}')"
                        >
                            👑 Передать хоста:
                            ${esc(p.name)}
                        </button>
                        `
                )
                .join("");

    }


    renderActions();


    if (
        state.phase === "🏆 ИГРА ОКОНЧЕНА"
    ) {

        $("result")
            .classList
            .remove("hidden");


        $("result")
            .innerHTML =
                "<b>🏆 Роли игроков</b><br>" +

                (state.roles || [])
                .map(
                    r =>
                        `${esc(r.name)}
                        —
                        ${esc(r.role)}
                        ${r.alive ? "🟢" : "💀"}`
                )
                .join("<br>");

    } else {

        $("result")
            .classList
            .add("hidden");

    }

}


function renderActions() {

    const box =
        $("actions");

    box.innerHTML = "";


    if (!state.alive) {

        return;

    }


    const candidates =
        state.players
        .filter(
            p =>
                p.alive &&
                p.name !== me
        );


    if (!candidates.length) {

        return;

    }


    const select =
        `
        <select id="target">

            ${
                candidates
                .map(
                    p =>
                        `<option value="${esc(p.name)}">
                            ${esc(p.name)}
                        </option>`
                )
                .join("")
            }

        </select>
        `;


    if (state.phase === "🌙 НОЧЬ") {

        if (
            ["Мафия", "Дон"]
            .includes(state.role)
        ) {

            box.innerHTML +=
                select +

                `
                <button
                    class="btn danger"
                    onclick="act('kill')"
                >
                    🔪 Убить
                </button>
                `;

        }


        if (
            state.role === "Маньяк"
        ) {

            box.innerHTML +=
                select +

                `
                <button
                    class="btn danger"
                    onclick="act('maniac_kill')"
                >
                    🔪 Убить
                </button>
                `;

        }


        if (
            state.role === "Доктор"
        ) {

            box.innerHTML +=
                select +

                `
                <button
                    class="btn good"
                    onclick="act('heal')"
                >
                    🩺 Спасти
                </button>
                `;

        }


        if (
            state.role === "Телохранитель"
        ) {

            box.innerHTML +=
                select +

                `
                <button
                    class="btn"
                    onclick="act('protect')"
                >
                    🛡️ Защитить
                </button>
                `;

        }


        if (
            state.role === "Шериф"
        ) {

            if (
                state.sheriff_used
            ) {

                box.innerHTML +=
                    `
                    <span class="pill">
                        🔎 Проверка уже использована
                    </span>
                    `;

            } else {

                box.innerHTML +=
                    select +

                    `
                    <button
                        class="btn accent"
                        onclick="act('inspect')"
                    >
                        🔎 Проверить
                    </button>
                    `;

            }

        }


        if (
            state.role === "Детектив"
        ) {

            box.innerHTML +=
                select +

                `
                <button
                    class="btn accent"
                    onclick="act('detect')"
                >
                    🕵️ Узнать роль
                </button>
                `;

        }

    }


    if (
        state.phase === "🗳️ ГОЛОСОВАНИЕ"
    ) {

        box.innerHTML =
            select +

            `
            <button
                class="btn accent"
                onclick="act('vote')"
            >
                🗳️ Голосовать
            </button>
            `;

    }

}


function act(type) {

    const target =
        $("target")?.value;


    if (target) {

        send({
            type: type,
            target: target
        });

    }

}


function start() {

    send({
        type: "start"
    });

}


function kick(name) {

    if (
        confirm(
            "Кикнуть " +
            name +
            "?"
        )
    ) {

        send({
            type: "kick",
            target: name
        });

    }

}


function transfer(name) {

    if (
        confirm(
            "Передать хоста игроку " +
            name +
            "?"
        )
    ) {

        send({
            type: "transfer_host",
            target: name
        });

    }

}


const savedAccent =
    localStorage.getItem("accent");


if (savedAccent) {

    document
        .documentElement
        .style
        .setProperty(
            "--accent",
            savedAccent
        );

}


makeColors(
    "colors",
    "chooseColor"
);


makeColors(
    "themeColors",
    "chooseTheme"
);


/* INIT */

(function init() {

    const saved =
        JSON.parse(
            localStorage.getItem(
                "mafia_profile"
            ) || "{}"
        );


    me =
        saved.name || "";

    avatar =
        saved.avatar || "";

    profileColor =
        saved.color || "#9b5cff";


    const params =
        new URLSearchParams(
            location.search
        );


    room =
        (
            params.get("room") || ""
        ).toUpperCase();


    if (
        !me ||
        !room
    ) {

        document.body.innerHTML =
            `
            <div class="modal">

                <div class="modalbox">

                    <h2>
                        🎭 Mafia Online
                    </h2>

                    <p>
                        Введи имя и код комнаты.
                    </p>

                    <input
                        id="quickName"
                        placeholder="Твоё имя"
                        maxlength="18"
                    >

                    <input
                        id="quickRoom"
                        placeholder="Код комнаты"
                        maxlength="4"
                    >

                    <div class="actions">

                        <button
                            class="btn accent"
                            onclick="quickJoin()"
                        >
                            Войти
                        </button>

                    </div>

                </div>

            </div>
            `;

    } else {

        connect();

    }

})();


function quickJoin() {

    me =
        $("quickName")
        .value
        .trim();


    room =
        $("quickRoom")
        .value
        .trim()
        .toUpperCase();


    if (
        !me ||
        !room
    ) {

        return;

    }


    localStorage.setItem(
        "mafia_profile",
        JSON.stringify({
            name: me,
            avatar: avatar,
            color: profileColor
        })
    );


    location.search =
        "?room=" +
        encodeURIComponent(room);

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
            random.choice(string.digits)
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


    # 4 ИГРОКА:
    # 1 МАФИЯ + 3 МИРНЫХ

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
    ] * (count - 8)


def is_mafia(player):

    return player["role"] in {
        "Мафия",
        "Дон"
    }


def alive(room, name):

    player = room["players"].get(name)

    return bool(
        player and
        player["alive"]
    )


# ============================================================
# STATE
# ============================================================

def state_for(room, name):

    player = room["players"].get(name)

    remaining = 0

    if room["ends"]:

        remaining = max(
            0,
            int(
                room["ends"] - now()
            )
        )


    roles = None

    if room["phase"] == WIN:

        roles = [
            {
                "name": player["name"],
                "role": player["role"],
                "alive": player["alive"]
            }

            for player
            in room["players"].values()
        ]


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
            player["role"]
            if player
            else None,

        "alive":
            player["alive"]
            if player
            else False,

        "sheriff_used":
            player.get(
                "sheriff_used",
                False
            )
            if player
            else False,

        "players": [

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
            in room["players"].values()

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
        room["connections"].items()
    ):

        try:

            await websocket.send_json(
                state_for(
                    room,
                    name
                )
            )

        except Exception:

            room["connections"].pop(
                websocket,
                None
            )


# ============================================================
# ASSIGN ROLES
# ============================================================

def assign_roles(room):

    roles = role_set(
        len(room["players"])
    )


    if roles is None:

        return False


    players = list(
        room["players"].values()
    )


    random.shuffle(players)

    random.shuffle(roles)


    for player, role in zip(
        players,
        roles
    ):

        player["role"] = role

        player["sheriff_used"] = False


    return True


# ============================================================
# WINNER
# ============================================================

def winner(room):

    alive_players = [
        p
        for p
        in room["players"].values()
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
        if p["role"] == "Маньяк"
    ]


    citizens = [
        p
        for p
        in alive_players

        if (
            not is_mafia(p)
            and
            p["role"] != "Маньяк"
        )
    ]


    if not mafia and not maniac:

        room["phase"] = WIN

        room["ends"] = 0

        room["announcement"] = (
            "🟢 Мирные жители победили!"
        )

        room["log"].append(
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

        room["announcement"] = (
            "🔪 Маньяк победил!"
        )

        room["log"].append(
            "🏆 Победа маньяка."
        )

        return True


    if (
        len(mafia)
        >=
        len(citizens) + len(maniac)
    ):

        room["phase"] = WIN

        room["ends"] = 0

        room["announcement"] = (
            "🔴 Мафия захватила город!"
        )

        room["log"].append(
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
            room["doctor_target"],
            room["bodyguard_target"]
        )

        if target
    }


    deaths = []


    for target in (
        room["night_target"],
        room["maniac_target"]
    ):

        if (
            target
            and
            alive(room, target)
            and
            target not in protected
            and
            target not in deaths
        ):

            deaths.append(target)


    for name in deaths:

        room["players"][name][
            "alive"
        ] = False

        room["log"].append(
            f"💀 Ночью погиб {name}."
        )


    if deaths:

        room["announcement"] = (
            "☀️ Город просыпается. "
            "Ночью произошло убийство."
        )

    else:

        room["announcement"] = (
            "☀️ Город просыпается. "
            "Этой ночью никто не погиб."
        )


    room["night_target"] = None

    room["maniac_target"] = None

    room["doctor_target"] = None

    room["bodyguard_target"] = None


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
        task is not asyncio.current_task()
    ):

        task.cancel()

        with suppress(
            asyncio.CancelledError
        ):

            await task


    for player in room["players"].values():

        player["alive"] = True

        player["role"] = None

        player["sheriff_used"] = False


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
            "🌙 Город засыпает. "
            "Ночные роли просыпаются."

    })


    assign_roles(room)


    room["game_task"] = (
        asyncio.create_task(
            game_loop(room)
        )
    )


# ============================================================
# GAME LOOP
# ============================================================

async def game_loop(room):

    try:

        while room["phase"] != WIN:

            if room["ends"] > now():

                await broadcast(room)

                await asyncio.sleep(
                    min(
                        1,
                        room["ends"] - now()
                    )
                )

                continue


            # NIGHT

            if room["phase"] == NIGHT:

                resolve_night(room)


                if winner(room):

                    await broadcast(room)

                    return


                room["phase"] = DAY

                room["ends"] = (
                    now() + 8
                )

                room["announcement"] = (
                    "☀️ День. "
                    "Обсудите события."
                )


                await broadcast(room)

                await asyncio.sleep(8)


                if winner(room):

                    await broadcast(room)

                    return


                room["phase"] = VOTE

                room["ends"] = (
                    now() + 45
                )

                room["votes"] = {}

                room["announcement"] = (
                    "🗳️ Голосование началось."
                )


                await broadcast(room)


            # VOTE

            elif room["phase"] == VOTE:

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


                    top = [
                        name

                        for name, count
                        in counts.items()

                        if count == maximum
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


                        room["players"][
                            victim
                        ]["alive"] = False


                        room["log"].append(
                            f"⚖️ {victim} "
                            f"изгнан голосованием."
                        )


                        room["announcement"] = (
                            f"⚖️ {victim} "
                            f"был изгнан."
                        )

                    else:

                        room["announcement"] = (
                            "⚖️ Ничья. "
                            "Никто не изгнан."
                        )

                else:

                    room["announcement"] = (
                        "🤷 Голосов нет."
                    )


                room["votes"] = {}


                if winner(room):

                    await broadcast(room)

                    return


                room["phase"] = NIGHT

                room["ends"] = (
                    now() + 15
                )

                room["announcement"] = (
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


        if first.get("type") != "join":

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


        room = rooms[code]


        if room["phase"] not in {
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


        if name in room["players"]:

            await websocket.send_json({

                "type":
                    "error",

                "message":
                    "Это имя уже занято."

            })

            return


        if len(room["players"]) >= 12:

            await websocket.send_json({

                "type":
                    "error",

                "message":
                    "Максимум 12 игроков."

            })

            return


        room["players"][name] = {

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


        room["connections"][
            websocket
        ] = name


        if room["host"] is None:

            room["host"] = name


        room["log"].append(
            f"🟢 {name} вошёл в комнату."
        )


        await broadcast(room)


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
                command == "profile"
                and
                player
            ):

                new_name = str(
                    data.get(
                        "name",
                        name
                    )
                ).strip()[:18]


                if new_name != name:

                    if (
                        new_name
                        in room["players"]
                    ):

                        await websocket.send_json({

                            "type":
                                "error",

                            "message":
                                "Имя уже занято."

                        })

                        continue


                    room["players"][
                        new_name
                    ] = room[
                        "players"
                    ].pop(name)


                    room["players"][
                        new_name
                    ]["name"] = (
                        new_name
                    )


                    room["connections"][
                        websocket
                    ] = new_name


                    if room["host"] == name:

                        room["host"] = (
                            new_name
                        )


                    name = new_name

                    player = room[
                        "players"
                    ][name]


                player["avatar"] = str(
                    data.get(
                        "avatar",
                        ""
                    )
                )[:600000]


                player["color"] = str(
                    data.get(
                        "color",
                        "#9b5cff"
                    )
                )[:20]


                await broadcast(room)

                continue


            # ==================================================
            # START
            # ==================================================

            if command == "start":

                if name != room["host"]:

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


                if room["phase"] in {
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

                if name != room["host"]:

                    continue


                target = str(
                    data.get(
                        "target",
                        ""
                    )
                )


                if (
                    target
                    in room["players"]
                    and
                    target != name
                    and
                    room["phase"] == LOBBY
                ):

                    for ws, player_name in list(
                        room["connections"].items()
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


                    room["log"].append(
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

                if name != room["host"]:

                    continue


                target = str(
                    data.get(
                        "target",
                        ""
                    )
                )


                if (
                    target
                    in room["players"]
                    and
                    target != name
                ):

                    room["host"] = target


                    room["log"].append(
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
                not player["alive"]
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
                command == "kill"
                and
                room["phase"] == NIGHT
                and
                player["role"]
                in {
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
                command == "maniac_kill"
                and
                room["phase"] == NIGHT
                and
                player["role"]
                == "Маньяк"
            ):

                room[
                    "maniac_target"
                ] = target


            # ==================================================
            # DOCTOR
            # ==================================================

            elif (
                command == "heal"
                and
                room["phase"] == NIGHT
                and
                player["role"]
                == "Доктор"
            ):

                room[
                    "doctor_target"
                ] = target


            # ==================================================
            # BODYGUARD
            # ==================================================

            elif (
                command == "protect"
                and
                room["phase"] == NIGHT
                and
                player["role"]
                == "Телохранитель"
            ):

                room[
                    "bodyguard_target"
                ] = target


            # ==================================================
            # SHERIFF
            # ONE TIME
            # ==================================================

            elif (
                command == "inspect"
                and
                room["phase"] == NIGHT
                and
                player["role"]
                == "Шериф"
                and
                not player[
                    "sheriff_used"
                ]
            ):

                player[
                    "sheriff_used"
                ] = True


                target_player = room[
                    "players"
                ][target]


                if is_mafia(
                    target_player
                ):

                    result = (
                        "🔴 МАФИЯ"
                    )

                else:

                    result = (
                        "🟢 НЕ МАФИЯ"
                    )


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
                command == "detect"
                and
                room["phase"] == NIGHT
                and
                player["role"]
                == "Детектив"
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
                command == "vote"
                and
                room["phase"] == VOTE
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


                room["log"].append(
                    f"🔴 {name} "
                    f"вышел из игры."
                )


                # Если вышел хост
                # автоматически передаём хоста

                if room["host"] == name:

                    room["host"] = (
                        next(
                            iter(
                                room["players"]
                            ),
                            None
                        )
                    )


                    if room["host"]:

                        room["log"].append(
                            f"👑 Новый хост: "
                            f"{room['host']}"
                        )


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
