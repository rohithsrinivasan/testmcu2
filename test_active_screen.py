import pyautogui
import time
import random

print("Screen activity keeper started. Press Ctrl+C to exit.")

try:
    while True:
        # Get the current mouse position
        x, y = pyautogui.position()

        # Move the mouse a tiny, random amount
        dx = random.randint(-5, 5)
        dy = random.randint(-5, 5)
        pyautogui.move(dx, dy, duration=0.2)
        print(f"Mouse moved by ({dx}, {dy})")

        # Wait for a period of time before the next move
        # The time.sleep() value is in seconds. 
        # 60 seconds = 1 minute.
        # 300 seconds = 5 minutes.
        # 600 seconds = 10 minutes.
        time.sleep(300)

except KeyboardInterrupt:
    print("\nScreen activity keeper stopped.")