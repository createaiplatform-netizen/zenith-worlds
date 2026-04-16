import time
import random
import os

print("ZENITH RUNNING (GITHUB LOG MODE)")

log_file = "run_log.txt"

while True:
    price = random.uniform(0.5, 1.5)

    if price > 1.2:
        signal = "BUY"
    elif price < 0.8:
        signal = "SELL"
    else:
        signal = "HOLD"

    line = f"PRICE: {price} | SIGNAL: {signal}\n"

    print(line)

    with open(log_file, "a") as f:
        f.write(line)

    time.sleep(3)