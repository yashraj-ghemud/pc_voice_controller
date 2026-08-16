import os
import time
import subprocess
import pyautogui
import pyperclip
import pygetwindow as gw

from .config import CONFIG


def _safe_hotkey(*keys):
    try:
        pyautogui.hotkey(*keys)
    except Exception as e:
        print(f"❌ Hotkey {keys} failed: {e}")


def _safe_press(key):
    try:
        pyautogui.press(key)
    except Exception as e:
        print(f"❌ Key press {key} failed: {e}")


def _safe_paste_text(text: str):
    try:
        pyperclip.copy(text)
        _safe_hotkey("ctrl", "v")
    except Exception as e:
        print(f"❌ Text paste failed: {e}")


def _safe_type_text(text: str):
    try:
        pyautogui.write(text, interval=0.02)
    except Exception as e:
        print(f"❌ Text typing failed: {e}")


def _focus_whatsapp_window() -> bool:
    try:
        for title in ["WhatsApp", "whatsapp"]:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                win = windows[0]
                win.activate()
                return True
    except Exception:
        pass
    return False


def _launch_whatsapp_if_needed() -> None:
    if _focus_whatsapp_window():
        return

    try:
        os.startfile("whatsapp://")
    except Exception:
        try:
            subprocess.run(["cmd", "/c", "start", "", "whatsapp://"], check=False)
        except Exception as e:
            print(f"❌ WhatsApp launch failed: {e}")

    time.sleep(CONFIG["DELAY_LONG"])
    _focus_whatsapp_window()


def open_whatsapp_chat(contact_name: str) -> bool:
    """Open WhatsApp Desktop, Ctrl+F, type contact, Enter. Returns success."""
    if not contact_name or not contact_name.strip():
        return False

    _launch_whatsapp_if_needed()
    time.sleep(CONFIG["DELAY_MEDIUM"])

    _safe_hotkey("ctrl", "f")
    time.sleep(CONFIG["DELAY_SHORT"])
    _safe_hotkey("ctrl", "a")
    time.sleep(0.2)
    # Important: do not use clipboard here, otherwise file/audio path clipboard gets overwritten.
    _safe_type_text(contact_name.strip())
    time.sleep(CONFIG["DELAY_MEDIUM"])
    _safe_press("enter")
    time.sleep(CONFIG["DELAY_MEDIUM"])
    return True


def paste_and_send(force_send: bool = False) -> None:
    """Ctrl+V then Enter to send pasted content.

    force_send=True bypasses TESTING_MODE and presses Enter.
    """
    _safe_hotkey("ctrl", "v")
    time.sleep(CONFIG["DELAY_MEDIUM"])
    if CONFIG["TESTING_MODE"] and not force_send:
        print("🧪 TESTING_MODE=True, skipping final Enter send")
        return
    _safe_press("enter")
