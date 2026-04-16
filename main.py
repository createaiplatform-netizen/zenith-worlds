import time
import random

log = "ZENITH RUNNING\n"

while True:
    price = round(random.uniform(0.5, 1.5), 4)

    if price > 1.2:
        signal = "BUY"
    elif price < 0.8:
        signal = "SELL"
    else:
        signal = "HOLD"

    log += f"PRICE: {price} | SIGNAL: {signal}\n"
    print(f"PRICE: {price} | SIGNAL: {signal}")

    time.sleep(3)