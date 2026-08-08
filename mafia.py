from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import random
import string
import time
import uvicorn

app = FastAPI()

rooms = {}

MAX_PLAYERS = 15
NIGHT_TIME = 15
DAY_TIME = 60


def make_code():
    while True:
        code = "".join(
            random.choices(
                string.ascii_uppercase + string.digits,
                k=6
            )
        )

        if code not in rooms:
            return code


def make_roles(players):
    names = list(players.keys())
    random.shuffle(names)

    roles = {}

    mafia_count = max(1, len(names) // 4)

    for name in names[:mafia_count]:
        roles[name] = "Мафия"

    left = [
        name for name in names
        if name not in roles
    ]

    if len(names) >= 5 and left:
        roles[left.pop()] = "Комиссар"

    if len(names) >= 6 and left:
        roles[left.pop()] = "Доктор"

    for name in left:
        roles[name] = "Мирный"

    return roles


def alive_players(room):
    return [
        name
        for name, player in room["players"].items()
        if player["alive"]
    ]


def check_winner(room):
    alive = alive_players(room)

    mafia = sum(
        room["players"][name]["role"] == "Мафия"
        for name in alive
    )

    citizens = len(alive) - mafia

    if mafia == 0:
        room["phase"] = "end"
        room["winner"] = "Мирные"
        room["message"] = "🎉 Мирные победили!"
        room["timer_end"] = None
        return True

    if mafia >= citizens:
        room["phase"] = "end"
        room["winner"] = "Мафия"
        room["message"] = "🔪 Мафия победила!"
        room["timer_end"] = None
        return True

    return False


def start_day(room, message):
    room["phase"] = "day"
    room["message"] = message
    room["votes"] = {}
    room["timer_end"] = time.time() + DAY_TIME


def start_night(room):
    room["phase"] = "night"
    room["message"] = "🌙 Город засыпает..."
    room["night_actions"] = {}
    room["timer_end"] = time.time() + NIGHT_TIME


def finish_night(room):
    night = room["night_actions"]

    mafia_target = None
    doctor_target = None

    for actor, target in night.items():

        if actor not in room["players"]:
            continue

        player = room["players"][actor]

        if not player["alive"]:
            continue

        if player["role"] == "Мафия":
            mafia_target = target

        elif player["role"] == "Доктор":
            doctor_target = target

        elif player["role"] == "Комиссар":

            checked = room["players"].get(target)

            if checked:
                player["result"] = (
                    f"🔎 {target}: "
                    + (
                        "МАФИЯ"
                        if checked["role"] == "Мафия"
                        else "НЕ МАФИЯ"
                    )
                )

    killed = None

    if (
        mafia_target
        and mafia_target in room["players"]
        and mafia_target != doctor_target
    ):
        if room["players"][mafia_target]["alive"]:
            room["players"][mafia_target]["alive"] = False
            killed = mafia_target

    room["night_actions"] = {}

    if killed:
        message = (
            f"☀️ Город просыпается. "
            f"Ночью погиб {killed}."
        )
    else:
        message = (
            "☀️ Город просыпается. "
            "Этой ночью никто не погиб."
        )

    if check_winner(room):
        return

    start_day(room, message)


def finish_day(room):
    votes = room["votes"]

    if not votes:
        start_night(
            room
        )
        return

    counts = {}

    for target in votes.values():
        counts[target] = counts.get(target, 0) + 1

    maximum = max(counts.values())

    leaders = [
        name
        for name, count in counts.items()
        if count == maximum
    ]

    if len(leaders) == 1:

        eliminated = leaders[0]

        if eliminated in room["players"]:
            room["players"][eliminated]["alive"] = False

        message = (
            f"⚖️ Голосование окончено. "
            f"{eliminated} покидает игру."
        )

    else:

        message = (
            "⚖️ Голосование окончено. "
            "Ничья — никто не покидает игру."
        )

    room["votes"] = {}

    if check_winner(room):
        return

    room["message"] = message

    start_night(room)

    room["message"] = (
        message +
        " 🌙 Город засыпает..."
    )


def update_room(room):
    if room["phase"] == "night":

        if room["timer_end"] is not None:

            if time.time() >= room["timer_end"]:
                finish_night(room)

    elif room["phase"] == "day":

        if room["timer_end"] is not None:

            if time.time() >= room["timer_end"]:
                finish_day(room)


def get_state(room, name):
    update_room(room)

    player = room["players"][name]

    targets = []

    if player["alive"]:

        if room["phase"] == "night":

            if player["role"] in [
                "Мафия",
                "Комиссар",
                "Доктор"
            ]:

                for target, data in room["players"].items():

                    if target == name:
                        continue

                    if not data["alive"]:
                        continue

                    if (
                        player["role"] == "Мафия"
                        and data["role"] == "Мафия"
                    ):
                        continue

                    targets.append(target)

        elif room["phase"] == "day":

            targets = [
                target
                for target, data
                in room["players"].items()
                if (
                    target != name
                    and data["alive"]
                )
            ]

    remaining = 0

    if room["timer_end"] is not None:

        remaining = max(
            0,
            int(
                room["timer_end"]
                - time.time()
            )
        )

    mafia_alive = (
        player["role"] == "Мафия"
        and player["alive"]
    )

    chat = []

    for message in room["chat"]:

        if (
            message["type"] == "mafia"
            and not mafia_alive
        ):
            continue

        chat.append(message)

    return {
        "code": room["code"],
        "host": room["host"],
        "you": name,

        "phase": room["phase"],

        "message": room["message"],

        "winner": room["winner"],

        "role": player["role"],

        "alive": player["alive"],

        "result": player["result"],

        "targets": targets,

        "time": remaining,

        "chat": chat,

        "players": [
            {
                "name": player_name,
                "alive": data["alive"]
            }
            for player_name, data
            in room["players"].items()
        ]
    }


HTML = r"""
<!DOCTYPE html>

<html lang="ru">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width,initial-scale=1">

<title>Mafia Online</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    min-height: 100vh;

    font-family:
        Arial,
        sans-serif;

    color: white;

    background:
        radial-gradient(
            circle at top,
            #65172d,
            #07090d 65%
        );
}

.container {
    width: 94%;
    max-width: 1050px;
    margin: auto;
    padding: 30px 0;
}

.logo {
    text-align: center;

    font-size: 65px;

    font-weight: 900;

    letter-spacing: 10px;

    color: #ef3857;

    text-shadow:
        0 0 15px #ef3857,
        0 0 50px #ef385755;
}

.subtitle {
    text-align: center;

    color: #777;

    letter-spacing: 5px;

    margin-bottom: 25px;
}

.card {
    background: #12151df5;

    border:
        1px solid #303540;

    border-radius: 20px;

    padding: 20px;

    box-shadow:
        0 20px 70px #0009;
}

.home {
    max-width: 430px;
    margin: auto;
}

input {
    width: 100%;

    padding: 14px;

    margin: 5px 0;

    border-radius: 10px;

    border:
        1px solid #353a46;

    background: #080a0e;

    color: white;

    font-size: 16px;

    outline: none;
}

button {
    width: 100%;

    padding: 13px;

    margin-top: 7px;

    border: 0;

    border-radius: 10px;

    background: #c92543;

    color: white;

    font-weight: bold;

    cursor: pointer;

    transition: .2s;
}

button:hover {
    background: #ed3857;

    transform:
        translateY(-1px);
}

.gray {
    background: #292e38;
}

.hidden {
    display: none !important;
}

.error {
    min-height: 24px;

    margin-top: 8px;

    text-align: center;

    color: #ff637a;
}

.top {
    display: grid;

    grid-template-columns:
        1fr
        auto
        1fr;

    gap: 15px;

    align-items: center;
}

.room-code {
    font-size: 28px;

    font-weight: 900;

    letter-spacing: 4px;
}

.phase {
    padding:
        10px
        18px;

    border-radius: 30px;

    background: #1b1f28;

    border:
        1px solid #353a46;

    font-weight: bold;

    text-align: center;
}

.role {
    text-align: right;

    color: #e8bd68;

    font-weight: bold;
}

.timer {
    text-align: center;

    font-size: 52px;

    font-weight: 900;

    margin: 20px 0;

    color: #ef3857;

    text-shadow:
        0 0 20px #ef3857;
}

.message {
    padding: 14px;

    margin: 15px 0;

    text-align: center;

    background: #10131a;

    border-radius: 12px;

    border:
        1px solid #292e38;
}

.grid {
    display: grid;

    grid-template-columns:
        1fr
        1fr;

    gap: 18px;
}

.player {
    display: flex;

    justify-content: space-between;

    padding: 10px;

    margin: 6px 0;

    background: #10131a;

    border-radius: 10px;
}

.dead {
    opacity: .35;

    text-decoration:
        line-through;
}

.target {
    margin-top: 6px;
}

.chat {
    height: 230px;

    overflow-y: auto;

    padding: 10px;

    background: #090b10;

    border-radius: 10px;

    border:
        1px solid #292e38;
}

.chat-message {
    padding: 6px 0;

    border-bottom:
        1px solid #20242d;
}

.chat-name {
    color: #e63855;

    font-weight: bold;
}

.gold {
    color: #e8bd68;
}

.result {
    margin-top: 10px;

    padding: 10px;

    background: #191c24;

    border-radius: 10px;

    color: #e8bd68;
}

@media(max-width:700px) {

    .grid {
        grid-template-columns: 1fr;
    }

    .top {
        grid-template-columns: 1fr 1fr;
    }

    .role {
        text-align: left;
    }

    .logo {
        font-size: 45px;
    }
}

</style>

</head>

<body>

<div class="container">

<section id="home">

<div class="logo">
MAFIA
</div>

<div class="subtitle">
ONLINE • FRIENDS
</div>

<div class="card home">

<input
id="name"
maxlength="18"
placeholder="Твоё имя"
>

<button onclick="createRoom()">
СОЗДАТЬ КОМНАТУ
</button>

<div
style="
text-align:center;
color:#666;
margin:14px
"
>
ИЛИ
</div>

<input
id="code"
maxlength="6"
placeholder="КОД КОМНАТЫ"
>

<button
class="gray"
onclick="joinRoom()"
>
ВОЙТИ В КОМНАТУ
</button>

<div
id="error"
class="error"
></div>

</div>

</section>


<section
id="game"
class="hidden"
>

<div class="top">

<div>

<small>КОМНАТА</small>

<div
id="roomCode"
class="room-code"
></div>

</div>

<div
id="phase"
class="phase"
>
ЛОББИ
</div>

<div
id="role"
class="role"
></div>

</div>


<div
id="timer"
class="timer"
>
--
</div>


<div
id="message"
class="message"
>
Ожидание...
</div>


<div class="grid">


<div class="card">

<h3>
👥 ИГРОКИ
</h3>

<div id="players"></div>

</div>


<div class="card">

<h3 id="actionTitle">
ЛОББИ
</h3>

<div id="actionText">
Ожидание игроков...
</div>

<div id="targets"></div>

<button
id="start"
onclick="startGame()"
>
НАЧАТЬ ИГРУ
</button>

<button
id="newGame"
class="gray hidden"
onclick="newGame()"
>
НОВАЯ ИГРА
</button>

<div
id="result"
class="result hidden"
></div>

</div>


<div class="card">

<h3>
💬 ЧАТ
</h3>

<div
id="chat"
class="chat"
></div>

<input
id="chatInput"
maxlength="120"
placeholder="Написать..."
>

<button onclick="sendChat()">
ОТПРАВИТЬ
</button>

</div>


</div>

</section>

</div>


<script>

let room = "";
let me = "";
let timer = null;

let lastPhase = "";


async function post(url, data) {

    const response =
        await fetch(
            url,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body:
                    JSON.stringify(data)
            }
        );

    return await response.json();
}


function say(text) {

    if (
        !("speechSynthesis" in window)
    ) {
        return;
    }

    speechSynthesis.cancel();

    const voice =
        new SpeechSynthesisUtterance(text);

    voice.lang = "ru-RU";

    voice.rate = 0.82;

    voice.pitch = 0.72;

    voice.volume = 1;

    speechSynthesis.speak(voice);
}


function showError(text) {

    document.getElementById(
        "error"
    ).textContent = text;
}


async function createRoom() {

    const name =
        document.getElementById(
            "name"
        ).value.trim();

    if (!name) {

        showError(
            "Введите имя"
        );

        return;
    }

    const data =
        await post(
            "/create",
            {
                name: name
            }
        );

    openGame(data);
}


async function joinRoom() {

    const name =
        document.getElementById(
            "name"
        ).value.trim();

    const code =
        document.getElementById(
            "code"
        ).value
        .trim()
        .toUpperCase();

    if (!name || !code) {

        showError(
            "Введите имя и код"
        );

        return;
    }

    const data =
        await post(
            "/join",
            {
                name: name,
                code: code
            }
        );

    if (data.error) {

        showError(
            data.error
        );

        return;
    }

    openGame(data);
}


function openGame(data) {

    if (data.error) {

        showError(
            data.error
        );

        return;
    }

    room = data.code;

    me = data.you;

    lastPhase = data.phase;

    document
        .getElementById("home")
        .classList
        .add("hidden");

    document
        .getElementById("game")
        .classList
        .remove("hidden");

    render(data);

    clearInterval(timer);

    timer =
        setInterval(
            update,
            500
        );
}


async function update() {

    if (!room || !me) {
        return;
    }

    const response =
        await fetch(
            "/state/"
            + encodeURIComponent(room)
            + "/"
            + encodeURIComponent(me)
        );

    const data =
        await response.json();

    if (!data.error) {

        if (
            data.phase !== lastPhase
        ) {

            announcePhase(data);

            lastPhase =
                data.phase;
        }

        render(data);
    }
}


function announcePhase(data) {

    if (data.phase === "night") {

        say(
            "Город засыпает. "
            + "Мафия просыпается."
        );

    }

    else if (
        data.phase === "day"
    ) {

        say(
            "Город просыпается. "
            + "Начинается голосование."
        );

    }

    else if (
        data.phase === "end"
    ) {

        say(
            "Игра окончена."
        );
    }
}


function render(data) {

    document.getElementById(
        "roomCode"
    ).textContent =
        data.code;


    const phases = {

        lobby: "ЛОББИ",

        night: "🌙 НОЧЬ",

        day: "☀️ ДЕНЬ",

        end: "🏆 КОНЕЦ"
    };


    document.getElementById(
        "phase"
    ).textContent =
        phases[data.phase];


    document.getElementById(
        "role"
    ).textContent =
        data.role
        ? "РОЛЬ: " + data.role
        : "";


    document.getElementById(
        "timer"
    ).textContent =
        data.time > 0
        ? data.time
        : "--";


    document.getElementById(
        "message"
    ).textContent =
        data.message;


    const players =
        document.getElementById(
            "players"
        );

    players.innerHTML = "";


    data.players.forEach(
        player => {

            const div =
                document.createElement(
                    "div"
                );

            div.className =
                "player "
                + (
                    player.alive
                    ? ""
                    : "dead"
                );

            const host =
                player.name === data.host
                ? " 👑"
                : "";

            div.innerHTML =
                "<span>"
                + player.name
                + host
                + "</span>"
                +
                "<span>"
                + (
                    player.alive
                    ? "●"
                    : "☠"
                )
                + "</span>";

            players.appendChild(
                div
            );
        }
    );


    const targets =
        document.getElementById(
            "targets"
        );

    targets.innerHTML = "";


    document.getElementById(
        "start"
    ).classList.add(
        "hidden"
    );


    document.getElementById(
        "newGame"
    ).classList.add(
        "hidden"
    );


    document.getElementById(
        "result"
    ).classList.add(
        "hidden"
    );


    if (
        data.result
    ) {

        const result =
            document.getElementById(
                "result"
            );

        result.textContent =
            data.result;

        result.classList.remove(
            "hidden"
        );
    }


    if (
        data.phase === "lobby"
    ) {

        document.getElementById(
            "actionTitle"
        ).textContent =
            "ЛОББИ";


        if (
            data.players.length < 4
        ) {

            document.getElementById(
                "actionText"
            ).textContent =
                "Нужно минимум 4 игрока.";

        }

        else if (
            data.you === data.host
        ) {

            document.getElementById(
                "actionText"
            ).textContent =
                "Вы хост. Можно начинать.";

            document.getElementById(
                "start"
            ).classList.remove(
                "hidden"
            );

        }

        else {

            document.getElementById(
                "actionText"
            ).textContent =
                "Ждите хоста.";
        }

        renderChat(data);

        return;
    }


    if (
        data.phase === "end"
    ) {

        document.getElementById(
            "actionTitle"
        ).textContent =
            "🏆 ПОБЕДА";


        document.getElementById(
            "actionText"
        ).innerHTML =
            "<span class='gold'>"
            + data.winner
            + "</span>";


        if (
            data.you === data.host
        ) {

            document.getElementById(
                "newGame"
            ).classList.remove(
                "hidden"
            );
        }

        renderChat(data);

        return;
    }


    if (!data.alive) {

        document.getElementById(
            "actionTitle"
        ).textContent =
            "☠ ВЫ ПОГИБЛИ";


        document.getElementById(
            "actionText"
        ).textContent =
            "Наблюдайте за игрой.";

        renderChat(data);

        return;
    }


    if (
        data.phase === "night"
    ) {

        document.getElementById(
            "actionTitle"
        ).textContent =
            data.role;


        if (
            data.role === "Мафия"
        ) {

            document.getElementById(
                "actionText"
            ).textContent =
                "Выберите жертву.";

        }

        else if (
            data.role === "Комиссар"
        ) {

            document.getElementById(
                "actionText"
            ).textContent =
                "Проверьте игрока.";

        }

        else if (
            data.role === "Доктор"
        ) {

            document.getElementById(
                "actionText"
            ).textContent =
                "Выберите кого лечить.";

        }

        else {

            document.getElementById(
                "actionText"
            ).textContent =
                "Ждите утра.";
        }
    }


    if (
        data.phase === "day"
    ) {

        document.getElementById(
            "actionTitle"
        ).textContent =
            "🗳 ГОЛОСОВАНИЕ";


        document.getElementById(
            "actionText"
        ).textContent =
            "Выберите игрока.";
    }


    data.targets.forEach(
        target => {

            const button =
                document.createElement(
                    "button"
                );

            button.className =
                "target";

            button.textContent =
                target;

            button.onclick =
                () => action(target);

            targets.appendChild(
                button
            );
        }
    );


    renderChat(data);
}


function renderChat(data) {

    const chat =
        document.getElementById(
            "chat"
        );

    chat.innerHTML = "";


    data.chat.forEach(
        message => {

            const div =
                document.createElement(
                    "div"
                );

            div.className =
                "chat-message";

            div.innerHTML =
                "<span class='chat-name'>"
                + escapeHtml(
                    message.name
                )
                + ":</span> "
                + escapeHtml(
                    message.text
                );

            chat.appendChild(div);
        }
    );

    chat.scrollTop =
        chat.scrollHeight;
}


function escapeHtml(text) {

    return text
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


async function action(target) {

    const data =
        await post(
            "/action",
            {
                code: room,
                player: me,
                target: target
            }
        );

    if (data.error) {

        alert(
            data.error
        );

        return;
    }

    render(data);
}


async function startGame() {

    const data =
        await post(
            "/start",
            {
                code: room,
                player: me
            }
        );

    if (data.error) {

        alert(
            data.error
        );

        return;
    }

    render(data);

    lastPhase = data.phase;

    say(
        "Город засыпает. "
        + "Мафия просыпается."
    );
}


async function newGame() {

    const data =
        await post(
            "/new",
            {
                code: room,
                player: me
            }
        );

    if (data.error) {

        alert(
            data.error
        );

        return;
    }

    render(data);

    lastPhase =
        data.phase;
}


async function sendChat() {

    const input =
        document.getElementById(
            "chatInput"
        );

    const text =
        input.value.trim();

    if (!text) {
        return;
    }

    const data =
        await post(
            "/chat",
            {
                code: room,
                player: me,
                text: text
            }
        );

    if (data.error) {

        alert(
            data.error
        );

        return;
    }

    input.value = "";

    render(data);
}


document
    .getElementById("chatInput")
    .addEventListener(
        "keydown",
        function(event) {

            if (
                event.key === "Enter"
            ) {

                sendChat();
            }
        }
    );

</script>

</body>

</html>
"""


@app.get("/")
def home():
    return HTMLResponse(HTML)


@app.post("/create")
def create(data: dict):

    name = str(
        data.get("name", "")
    ).strip()

    if not name:
        return {
            "error":
                "Введите имя"
        }

    code = make_code()

    rooms[code] = {

        "code": code,

        "host": name,

        "players": {

            name: {

                "alive": True,

                "role": None,

                "result": None
            }
        },

        "phase": "lobby",

        "message":
            "Ожидание игроков...",

        "winner": None,

        "votes": {},

        "night_actions": {},

        "timer_end": None,

        "chat": []
    }

    return get_state(
        rooms[code],
        name
    )


@app.post("/join")
def join(data: dict):

    name = str(
        data.get("name", "")
    ).strip()

    code = str(
        data.get("code", "")
    ).upper().strip()

    room = rooms.get(code)

    if not room:
        return {
            "error":
                "Комната не найдена"
        }

    if room["phase"] != "lobby":
        return {
            "error":
                "Игра уже началась"
        }

    if name in room["players"]:
        return {
            "error":
                "Это имя уже занято"
        }

    if len(room["players"]) >= MAX_PLAYERS:
        return {
            "error":
                "Комната заполнена"
        }

    room["players"][name] = {

        "alive": True,

        "role": None,

        "result": None
    }

    # Последний вошедший становится хостом.

    room["host"] = name

    room["chat"].append({
        "name": "Система",
        "text": f"{name} вошёл в комнату.",
        "type": "system"
    })

    return get_state(
        room,
        name
    )


@app.get("/state/{code}/{name}")
def state_route(
    code: str,
    name: str
):

    room = rooms.get(code)

    if not room:
        return {
            "error":
                "Комната не найдена"
        }

    if name not in room["players"]:
        return {
            "error":
                "Игрок не найден"
        }

    return get_state(
        room,
        name
    )


@app.post("/start")
def start(data: dict):

    code = str(
        data.get("code", "")
    ).upper()

    name = str(
        data.get("player", "")
    )

    room = rooms.get(code)

    if not room:
        return {
            "error":
                "Комната не найдена"
        }

    if name != room["host"]:
        return {
            "error":
                "Только хост может начать игру"
        }

    if len(room["players"]) < 4:
        return {
            "error":
                "Нужно минимум 4 игрока"
        }

    roles = make_roles(
        room["players"]
    )

    for player_name in room["players"]:

        room["players"][player_name]["role"] = \
            roles[player_name]

        room["players"][player_name]["alive"] = True

        room["players"][player_name]["result"] = None

    room["winner"] = None

    room["votes"] = {}

    room["night_actions"] = {}

    room["chat"] = []

    start_night(room)

    room["message"] = (
        "🌙 Город засыпает. "
        "Мафия просыпается."
    )

    return get_state(
        room,
        name
    )


@app.post("/action")
def action(data: dict):

    code = str(
        data.get("code", "")
    ).upper()

    name = str(
        data.get("player", "")
    )

    target = str(
        data.get("target", "")
    )

    room = rooms.get(code)

    if not room:
        return {
            "error":
                "Комната не найдена"
        }

    if name not in room["players"]:
        return {
            "error":
                "Игрок не найден"
        }

    update_room(room)

    if room["phase"] not in [
        "night",
        "day"
    ]:
        return get_state(
            room,
            name
        )

    player = room["players"][name]

    if not player["alive"]:
        return {
            "error":
                "Вы погибли"
        }

    if target not in room["players"]:
        return {
            "error":
                "Игрок не найден"
        }

    if not room["players"][target]["alive"]:
        return {
            "error":
                "Игрок уже погиб"
        }

    if target == name:
        return {
            "error":
                "Нельзя выбрать себя"
        }


    # НОЧЬ

    if room["phase"] == "night":

        if player["role"] not in [
            "Мафия",
            "Комиссар",
            "Доктор"
        ]:
            return get_state(
                room,
                name
            )

        if (
            player["role"] == "Мафия"
            and room["players"][target]["role"]
            == "Мафия"
        ):
            return {
                "error":
                    "Нельзя выбрать другую мафию"
            }

        room["night_actions"][name] = target

        special = [
            n
            for n, p
            in room["players"].items()
            if (
                p["alive"]
                and p["role"] in [
                    "Мафия",
                    "Комиссар",
                    "Доктор"
                ]
            )
        ]

        if len(room["night_actions"]) >= len(special):
            finish_night(room)

        return get_state(
            room,
            name
        )


    # ДЕНЬ

    if room["phase"] == "day":

        room["votes"][name] = target

        alive = alive_players(room)

        if len(room["votes"]) >= len(alive):
            finish_day(room)

        return get_state(
            room,
            name
        )

    return get_state(
        room,
        name
    )


@app.post("/chat")
def chat(data: dict):

    code = str(
        data.get("code", "")
    ).upper()

    name = str(
        data.get("player", "")
    )

    text = str(
        data.get("text", "")
    ).strip()

    room = rooms.get(code)

    if not room:
        return {
            "error":
                "Комната не найдена"
        }

    if name not in room["players"]:
        return {
            "error":
                "Игрок не найден"
        }

    if not text:
        return get_state(
            room,
            name
        )

    if len(text) > 120:
        return {
            "error":
                "Сообщение слишком длинное"
        }

    player = room["players"][name]

    if not player["alive"]:
        return {
            "error":
                "Мёртвые не могут писать"
        }

    message_type = "normal"

    if (
        room["phase"] == "night"
        and player["role"] == "Мафия"
    ):
        message_type = "mafia"

    room["chat"].append({
        "name": name,
        "text": text,
        "type": message_type
    })

    if len(room["chat"]) > 100:
        room["chat"] = room["chat"][-100:]

    return get_state(
        room,
        name
    )


@app.post("/new")
def new_game(data: dict):

    code = str(
        data.get("code", "")
    ).upper()

    name = str(
        data.get("player", "")
    )

    room = rooms.get(code)

    if not room:
        return {
            "error":
                "Комната не найдена"
        }

    if name != room["host"]:
        return {
            "error":
                "Только хост может начать новую игру"
        }

    names = list(
        room["players"].keys()
    )

    if not names:
        return {
            "error":
                "Нет игроков"
        }

    current = names.index(
        room["host"]
    )

    room["host"] = names[
        (current + 1) % len(names)
    ]

    for player in room["players"].values():

        player["alive"] = True

        player["role"] = None

        player["result"] = None

    room["phase"] = "lobby"

    room["message"] = (
        "Новый хост: "
        + room["host"]
        + " 👑"
    )

    room["winner"] = None

    room["votes"] = {}

    room["night_actions"] = {}

    room["timer_end"] = None

    room["chat"] = []

    return get_state(
        room,
        name
    )


if __name__ == "__main__":

    print()
    print("==============================")
    print("        MAFIA ONLINE 2.0")
    print("==============================")
    print()
    print("Открой:")
    print("http://127.0.0.1:8001")
    print()

    import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)