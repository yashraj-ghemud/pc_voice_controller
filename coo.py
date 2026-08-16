import pyautogui
import os

while True:
    os.system('cls')
    x, y = pyautogui.position()
    print(f"X: {x}, Y: {y}")