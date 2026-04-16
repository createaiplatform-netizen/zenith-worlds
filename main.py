import json
import time
from datetime import datetime
from flask import Flask, jsonify, request

# =========================
# SYSTEM STATE
# =========================
state = {
    "system_status": "RUNNING",
    "kill_switch": False,
    "risk_level": "LOW",
    "last_signal": None,
    "last_action": None,
    "error_count": 0,
    "performance": {
        "trades": 0,
        "wins": 0,
        "losses": 0
    }
}

# =========================
# PERFORMANCE ENGINE
# =========================
def update_performance(result):
    state["performance"]["trades"] += 1

    if "EXECUTED" in result or "PAPER TRADE" in result:
        state["performance"]["wins"] += 1
    else:
        state["performance"]["losses"] += 1

# =========================
# RISK ENGINE (GLOBAL OVERRIDE)
# =========================
def evaluate_risk():
    p = state["performance"]

    if p["trades"] > 0:
        win_rate = p["wins"] / p["trades"]

        if win_rate < 0.3 and p["trades"] > 10:
            state["risk_level"] = "HIGH"
            state["kill_switch"] = True

        elif win_rate < 0.5:
            state["risk_level"] = "MEDIUM"

        else:
            state["risk_level"] = "LOW"

# =========================
# LOGGING
# =========================
def log_event(event):
    event["time"] = str(datetime.utcnow())

    with open("control_log.jsonl", "a") as f:
        f.write(json.dumps(event) + "\n")

# =========================
# CONTROL API (REMOTE ACCESS)
# =========================
app = Flask(__name__)

@app.route("/status")
def status():
    evaluate_risk()
    return jsonify(state)

@app.route("/kill", methods=["POST"])
def kill():
    state["kill_switch"] = True
    state["system_status"] = "KILLED"
    log_event({"action": "KILL_SWITCH_TRIGGERED"})
    return jsonify({"ok": True})

@app.route("/resume", methods=["POST"])
def resume():
    state["kill_switch"] = False
    state["system_status"] = "RUNNING"
    log_event({"action": "SYSTEM_RESUMED"})
    return jsonify({"ok": True})

@app.route("/update", methods=["POST"])
def update():
    data = request.json
    state["last_signal"] = data.get("signal")
    state["last_action"] = data.get("result")

    update_performance(data.get("result", ""))

    log_event(data)
    return jsonify({"ok": True})

# =========================
# MONITOR LOOP (HEARTBEAT)
# =========================
def heartbeat():
    while True:
        evaluate_risk()

        log_event({
            "heartbeat": True,
            "state": state
        })

        time.sleep(60)

# =========================
# START SYSTEM
# =========================
if __name__ == "__main__":
    from threading import Thread

    Thread(target=heartbeat).start()

    print("ZENITH CONTROL CENTER LIVE")
    app.run(host="0.0.0.0", port=8000)