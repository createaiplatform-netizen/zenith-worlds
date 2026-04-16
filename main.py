import time
import random

print("ZENITH RUNNING (SIMPLE MODE)")

while True:
    price = random.uniform(0.5, 1.5)

    if price > 1.2:
        signal = "BUY"
    elif price < 0.8:
        signal = "SELL"
    else:
        signal = "HOLD"

    print("PRICE:", price, "SIGNAL:", signal)

    time.sleep(3)