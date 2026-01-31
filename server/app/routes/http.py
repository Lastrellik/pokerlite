from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

INDEX_HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>PokerLite</title>
    <style>
      body { font-family: system-ui, sans-serif; margin: 20px; }
      #log { white-space: pre-wrap; background: #f6f6f6; padding: 10px; border-radius: 8px; }
      button { margin-right: 6px; }
      input { margin-right: 6px; }
      .row { margin: 8px 0; }
    </style>
  </head>
  <body>
    <h1>PokerLite</h1>

    <div class="row">
      <label>Table:</label>
      <input id="table" value="default" />
      <label>Name:</label>
      <input id="name" value="jason" />
      <button onclick="connect()">Connect</button>
      <button onclick="disconnect()">Disconnect</button>
      <button onclick="newPlayer()">New Player</button>
      <span id="pid-display" style="margin-left: 10px; color: #666;"></span>
    </div>

    <div class="row">
      <button onclick="sendStart()">Start</button>
      <button onclick="sendAction('check')">Check</button>
      <button onclick="sendAction('call')">Call</button>
      <label>Raise:</label>
      <input id="raiseAmount" type="number" value="20" style="width: 80px;" />
      <button onclick="sendRaise()">Raise</button>
      <button onclick="sendAction('fold')">Fold</button>
    </div>

    <div class="row">
      <strong>Pot:</strong> <span id="pot">0</span> |
      <strong>To Call:</strong> <span id="toCall">0</span> |
      <strong>Your Stack:</strong> <span id="myStack">0</span>
    </div>

    <h3>Log</h3>
    <div id="log"></div>

    <script>
      let ws = null;
      let pid = localStorage.getItem("pokerlite_pid") || null;

      function updatePidDisplay() {
        const el = document.getElementById("pid-display");
        el.textContent = pid ? `Player ID: ${pid}` : "No player ID (will get new one)";
      }

      function log(msg) {
        const el = document.getElementById("log");
        el.textContent = msg + "\\n" + el.textContent;
      }

      function newPlayer() {
        if (ws) ws.close();
        ws = null;
        pid = null;
        localStorage.removeItem("pokerlite_pid");
        updatePidDisplay();
        log("Player ID cleared - you will get a new ID on next connect");
      }

      updatePidDisplay();

      function connect() {
        const table = document.getElementById("table").value.trim();
        const name = document.getElementById("name").value.trim() || "player";
        if (ws) ws.close();

        const url = `ws://${location.host}/ws/${encodeURIComponent(table)}`;
        ws = new WebSocket(url);

        ws.onopen = () => {
          log("WS open: " + url);
          ws.send(JSON.stringify({type: "join", name, pid}));
        };

        ws.onmessage = (ev) => {
          try {
            const msg = JSON.parse(ev.data);
            if (msg.type === "welcome") {
              pid = msg.pid;
              localStorage.setItem("pokerlite_pid", pid);
              updatePidDisplay();
              log("welcome pid=" + pid);
            } else if (msg.type === "state") {
              const state = msg.state;

              // Update UI displays
              document.getElementById("pot").textContent = state.pot || 0;

              const myBet = (state.player_bets && state.player_bets[pid]) || 0;
              const toCall = Math.max(0, (state.current_bet || 0) - myBet);
              document.getElementById("toCall").textContent = toCall;

              // Find my player and show stack
              const myPlayer = (state.players || []).find(p => p.pid === pid);
              if (myPlayer) {
                document.getElementById("myStack").textContent = myPlayer.stack;
              }

              log("state:\\n" + JSON.stringify(msg.state, null, 2));
            } else if (msg.type === "info") {
              log("info: " + msg.message);
            } else {
              log("msg: " + ev.data);
            }
          } catch (e) {
            log("non-json msg: " + ev.data);
          }
        };

        ws.onclose = () => log("WS closed");
        ws.onerror = () => log("WS error (see console)");
      }

      function disconnect() {
        if (ws) ws.close();
        ws = null;
      }

      function sendStart() {
        if (!ws || ws.readyState !== 1) return log("not connected");
        ws.send(JSON.stringify({type: "start"}));
      }

      function sendAction(action) {
        if (!ws || ws.readyState !== 1) return log("not connected");
        ws.send(JSON.stringify({type: "action", action}));
      }

      function sendRaise() {
        if (!ws || ws.readyState !== 1) return log("not connected");
        const amount = parseInt(document.getElementById("raiseAmount").value) || 0;
        ws.send(JSON.stringify({type: "action", action: "raise", amount}));
      }
    </script>
  </body>
</html>
"""

@router.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(INDEX_HTML)

@router.get("/health")
def health():
    return {"ok": True}
