import base64
import io
import re
import json
import mss
import pyautogui
import time
from groq import Groq

API_KEY = "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"
client = Groq(api_key=API_KEY)

VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

screenshot_base64 = None


def take_screenshot():
    """Take a screenshot and return base64 encoded string."""
    with mss.mss() as sct:
        monitor = sct.monitors[0]  # full screen (all monitors)
        img = sct.grab(monitor)

        from PIL import Image
        pil_img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")

        # Downscale large captures for faster vision round-trips.
        max_width = 1366
        if pil_img.width > max_width:
            ratio = max_width / float(pil_img.width)
            new_h = max(1, int(pil_img.height * ratio))
            pil_img = pil_img.resize((max_width, new_h), Image.Resampling.LANCZOS)
        
        # Store dimensions for coordinate mapping
        global _last_screenshot_size
        _last_screenshot_size = pil_img.size  # (width, height)
        
        buffer = io.BytesIO()
        pil_img.save(buffer, format="JPEG", quality=55, optimize=True)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode("utf-8")


_last_screenshot_size = None


def _get_screen_dimensions():
    """Get actual screen dimensions."""
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        return monitor["width"], monitor["height"]


def ask_about_screenshot(question, b64_image):
    """Send question + screenshot to Groq Vision model."""
    completion = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64_image}",
                        },
                    },
                ],
            }
        ],
    )
    return completion.choices[0].message.content


def find_element_coordinates(description, b64_image=None):
    """
    Use vision AI to find a UI element on screen and return its (x, y) coordinates.
    
    Args:
        description: What to look for, e.g. "search bar", "play button", "text input field"
        b64_image: Optional pre-captured screenshot. If None, takes a fresh one.
    
    Returns:
        (x, y) tuple or None if not found
    """
    if b64_image is None:
        b64_image = take_screenshot()
    
    screen_w, screen_h = _get_screen_dimensions()
    
    prompt = f"""Look at this screenshot carefully. I need you to find the following UI element: "{description}"

Find the EXACT pixel coordinates of the CENTER of this element.

The screen resolution is {screen_w}x{screen_h} pixels.

You MUST respond with ONLY a JSON object in this exact format, nothing else:
{{"x": <number>, "y": <number>, "found": true, "element": "<what you found>"}}

If you cannot find the element, respond with:
{{"x": 0, "y": 0, "found": false, "element": "not found"}}

IMPORTANT: Give the coordinates as actual pixel positions on screen. Respond with ONLY the JSON, no other text."""

    try:
        response = ask_about_screenshot(prompt, b64_image)
        
        # Parse JSON from response
        # Try to extract JSON from the response
        json_match = re.search(r'\{[^{}]*\}', response)
        if json_match:
            data = json.loads(json_match.group())
            if data.get("found", False):
                x = int(data["x"])
                y = int(data["y"])
                # Clamp to screen bounds
                x = max(0, min(x, screen_w - 1))
                y = max(0, min(y, screen_h - 1))
                print(f"👁️ Found '{description}' at ({x}, {y}) — {data.get('element', '')}")
                return (x, y)
            else:
                print(f"👁️ Could not find '{description}' on screen")
                return None
        else:
            print(f"⚠️ Vision AI returned unparseable response: {response[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Screen AI error: {e}")
        return None


def find_and_click_element(description):
    """
    Take a screenshot, find the described element, and click on it.
    
    Args:
        description: What to click, e.g. "play button", "first video thumbnail", "search icon"
    
    Returns:
        True if clicked, False if element not found
    """
    print(f"🔍 Looking for '{description}' on screen...")
    b64_image = take_screenshot()
    coords = find_element_coordinates(description, b64_image)
    
    if coords:
        x, y = coords
        print(f"🖱️ Clicking at ({x}, {y})...")
        pyautogui.click(x, y)
        time.sleep(0.3)
        return True
    else:
        print(f"❌ Could not find '{description}' to click")
        return False


def find_and_type_in_field(text, field_description="text input field or search bar", press_enter=True):
    """
    Take a screenshot, find an input field, click on it, type text, and optionally press Enter.
    
    Args:
        text: The text to type
        field_description: What kind of input field to look for
        press_enter: Whether to press Enter after typing
    
    Returns:
        True if typed successfully, False if field not found
    """
    print(f"🔍 Looking for input field: '{field_description}'...")
    b64_image = take_screenshot()
    coords = find_element_coordinates(field_description, b64_image)
    
    if coords:
        x, y = coords
        print(f"🖱️ Clicking input field at ({x}, {y})...")
        pyautogui.click(x, y)
        time.sleep(0.5)
        
        # Clear existing text in the field
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        
        # Type the text using clipboard for Unicode support
        print(f"⌨️ Typing: {text}")
        import pyperclip
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.3)
        
        if press_enter:
            print("⏎ Pressing Enter...")
            pyautogui.press('enter')
            time.sleep(0.3)
        
        return True
    else:
        print(f"❌ Could not find input field: '{field_description}'")
        return False


def analyze_screen(question=None):
    """
    Take a screenshot and analyze what's currently on screen.
    
    Args:
        question: Specific question about the screen. If None, gives a general overview.
    
    Returns:
        String description of what's on screen
    """
    b64_image = take_screenshot()
    
    if not question:
        question = "Describe what is currently visible on this screen. What applications are open? What is the user looking at? Be concise."
    
    try:
        return ask_about_screenshot(question, b64_image)
    except Exception as e:
        return f"Error analyzing screen: {e}"


def check_visual_condition(condition_description, b64_image=None):
    """
    Ask vision model whether a condition is met on the current screen.

    Returns:
        dict: {"met": bool, "reason": str}
    """
    if b64_image is None:
        b64_image = take_screenshot()

    prompt = f"""You are checking whether a UI condition is currently true.

Condition to verify: {condition_description}

Respond with ONLY valid JSON in this exact format:
{{"met": true/false, "reason": "short reason"}}

Rules:
- Use met=true only if the condition is clearly visible on screen.
- If uncertain, use met=false.
- Return only JSON, no extra text."""

    try:
        response = ask_about_screenshot(prompt, b64_image)
        json_match = re.search(r'\{[^{}]*\}', response)
        if not json_match:
            return {"met": False, "reason": "unparseable response"}

        data = json.loads(json_match.group())
        met = bool(data.get("met", False))
        reason = str(data.get("reason", ""))
        return {"met": met, "reason": reason}
    except Exception as e:
        return {"met": False, "reason": f"vision error: {e}"}


def wait_for_visual_condition(condition_description, timeout=120, interval=4, stable_checks=2):
    """
    Poll the screen until the condition is met for a stable number of checks.

    Args:
        condition_description: Natural language condition to verify.
        timeout: Max seconds to wait.
        interval: Seconds between checks.
        stable_checks: Number of consecutive true checks required.

    Returns:
        True if condition is met before timeout, else False.
    """
    start = time.time()
    consecutive = 0

    while (time.time() - start) < timeout:
        loop_start = time.time()
        result = check_visual_condition(condition_description)
        met = result.get("met", False)
        reason = result.get("reason", "")

        print(f"👁️ Condition check -> met={met} | reason={reason}")

        if met:
            consecutive += 1
            if consecutive >= stable_checks:
                return True
        else:
            consecutive = 0

        elapsed = time.time() - loop_start
        remaining = interval - elapsed
        if remaining > 0:
            time.sleep(remaining)

    return False


# ─── Standalone interactive mode ─────────────────────────────────────────────
def main():
    global screenshot_base64

    print("=" * 50)
    print("  SCREEN AI - Screenshot Analyzer")
    print("=" * 50)
    print()
    print("Commands:")
    print("  ss    -> Take a screenshot")
    print("  find  -> Find and click an element")
    print("  type  -> Find input field and type")
    print("  quit  -> Exit the program")
    print()
    print("After taking a screenshot, type any question")
    print("to ask about it.")
    print("-" * 50)

    while True:
        user_input = input("\n> ").strip()

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Bye!")
            break

        if user_input.lower() == "ss":
            print("Taking screenshot...")
            try:
                screenshot_base64 = take_screenshot()
                print("Screenshot captured! Now ask anything about it.")
            except Exception as e:
                print(f"Error taking screenshot: {e}")
            continue

        if user_input.lower() == "find":
            desc = input("What to find and click? > ").strip()
            if desc:
                find_and_click_element(desc)
            continue

        if user_input.lower() == "type":
            field = input("Describe the input field: > ").strip()
            text = input("What to type: > ").strip()
            if text:
                find_and_type_in_field(text, field or "text input field")
            continue

        # Any other input is treated as a question about the screenshot
        if screenshot_base64 is None:
            print("No screenshot yet! Type 'ss' first to take one.")
            continue

        print("Thinking...")
        try:
            answer = ask_about_screenshot(user_input, screenshot_base64)
            print(f"\nAI: {answer}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
