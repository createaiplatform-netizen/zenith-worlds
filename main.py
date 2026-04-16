import time
import random
import json

print("ZENITH SIMULATION STARTED")

state = []

while True:
    price = round(random.uniform(0.5, 1.5), 4)

    if price > 1.2:
        signal = "BUY"
    elif price < 0.8:
        signal = "SELL"
    else:
        signal = "HOLD"

    entry = {
        "time": time.time(),
        "price": price,
        "signal": signal
    }

    state.append(entry)

    # show output in GitHub "Actions" logs if run there
    print(json.dumps(entry))

    time.sleep(3)