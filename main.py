from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

state = {
    "last_price": None,
    "price": 0,
    "signal": "HOLD"
}

SYMBOL = "XRP-USD"

def get_price():
    r = requests.get("https://api.coinbase.com/v2/prices/XRP-USD/spot")
    return float(r.json()["data"]["amount"])

def compute_signal(price):
    if state["last_price"] is None:
        return "HOLD"

    change = (price - state["last_price"]) / state["last_price"]

    if change > 0.01:
        return "BUY"
    elif change < -0.01:
        return "SELL"
    return "HOLD"


@app.route("/data")
def data():
    return jsonify(state)


def update_loop():
    while True:
        try:
            price = get_price()
            signal = compute_signal(price)

            state["last_price"] = price
            state["price"] = price
            state["signal"] = signal

            time.sleep(5)

        except Exception as e:
            print("error:", e)
            time.sleep(5)


if __name__ == "__main__":
    from threading import Thread

    Thread(target=update_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)