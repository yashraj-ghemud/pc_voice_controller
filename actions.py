import os
import time
import json
import ctypes
import subprocess
import webbrowser
import platform
import pyautogui
import keyboard
from AppOpener import open as app_open, close as app_close
import screen_ai
from whatsapp_module.handler import handle_send_command as wa_handle_send_command
from whatsapp_module.handler import send_voice_note as wa_send_voice_note

# Disable pyautogui's built-in pause for faster execution
pyautogui.PAUSE = 0.02

# Improve coordinate accuracy on Windows when display scaling is enabled.
if os.name == "nt":
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def _native_click_at(x, y, button="left"):
    """DPI-safe native click for Windows; falls back to pyautogui elsewhere."""
    if os.name != "nt":
        pyautogui.click(x, y, button=button)
        return

    user32 = ctypes.windll.user32
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.06)

    # mouse_event flags
    LEFTDOWN, LEFTUP = 0x0002, 0x0004
    RIGHTDOWN, RIGHTUP = 0x0008, 0x0010
    MIDDLEDOWN, MIDDLEUP = 0x0020, 0x0040

    if button == "right":
        user32.mouse_event(RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(0.02)
        user32.mouse_event(RIGHTUP, 0, 0, 0, 0)
    elif button == "middle":
        user32.mouse_event(MIDDLEDOWN, 0, 0, 0, 0)
        time.sleep(0.02)
        user32.mouse_event(MIDDLEUP, 0, 0, 0, 0)
    else:
        user32.mouse_event(LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.02)
        user32.mouse_event(LEFTUP, 0, 0, 0, 0)

# --- Volume Control (pycaw with fallback to keyboard) ---

# Try to set up pycaw at import time
_PYCAW_OK = False
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    def _get_volume_interface():
        """Get IAudioEndpointVolume — handles both old and new pycaw."""
        device = AudioUtilities.GetSpeakers()
        # Old pycaw: device is IMMDevice with .Activate()
        # New pycaw: device is AudioDevice wrapper with ._dev
        raw = getattr(device, '_dev', device)
        interface = raw.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))

    # Test it once at startup
    _test = _get_volume_interface()
    _PYCAW_OK = True
    print("✅ [VOL] pycaw volume control ready")
except Exception as e:
    print(f"⚠️ [VOL] pycaw not available, using keyboard fallback: {e}")


def _normalize_level(level):
    """Convert any volume value to integer 0-100."""
    if isinstance(level, float) and level <= 1.0:
        level = int(level * 100)
    return max(0, min(100, int(level)))


def set_volume(level):
    """Set system volume to exact percentage (0-100)."""
    level = _normalize_level(level)

    if _PYCAW_OK:
        try:
            vol = _get_volume_interface()
            vol.SetMasterVolumeLevelScalar(level / 100.0, None)
            print(f"🔊 Volume set to {level}%")
            return
        except Exception as e:
            print(f"⚠️ pycaw failed, keyboard fallback: {e}")

    # Keyboard fallback (slower but always works)
    old_pause = pyautogui.PAUSE
    pyautogui.PAUSE = 0
    for _ in range(50):
        pyautogui.press("volumedown")
    for _ in range(level // 2):
        pyautogui.press("volumeup")
    pyautogui.PAUSE = old_pause
    print(f"🔊 Volume set to ~{level}%")


def change_volume(change):
    """Change volume up/down by a relative amount."""
    try:
        steps = max(1, int(abs(change) / 2))
        key = "volumeup" if change > 0 else "volumedown"
        for _ in range(steps):
            pyautogui.press(key)
        print(f"🔊 Volume {'increased' if change > 0 else 'decreased'}")
    except Exception as e:
        print(f"❌ Error changing volume: {e}")

def mute_volume():
    pyautogui.press("volumemute")
    print("🔇 Muted")

def unmute_volume():
    pyautogui.press("volumemute")
    print("🔊 Unmuted")


# --- App Management ---
MANUAL_APP_MAP = {
    "chrome": "google chrome",
    "youtube": "google chrome",
    "notepad": "notepad",
    "calc": "calculator",
    "calculator": "calculator",
    "vscode": "visual studio code",
    "code": "visual studio code",
}

def open_via_search(app_name):
    print(f"🔎 Opening {app_name} via Windows Search...")
    pyautogui.press("win")
    time.sleep(0.3)
    pyautogui.write(app_name, interval=0.03)
    time.sleep(0.4)
    pyautogui.press("enter")

def open_application(app_name):
    print(f"🚀 Opening {app_name}...")
    search_name = MANUAL_APP_MAP.get(app_name.lower(), app_name)

    if "chrome" in search_name.lower() or "google" in search_name.lower():
        open_via_search(search_name)
        return

    try:
        app_open(search_name, match_closest=True, throw_error=True)
    except:
        open_via_search(search_name)

def close_application(app_name):
    print(f"🛑 Closing {app_name}...")
    try:
        app_close(app_name, match_closest=True, throw_error=True)
    except:
        try:
            os.system(f"taskkill /f /im {app_name}.exe")
        except Exception as e:
            print(f"❌ Failed to close {app_name}: {e}")

# --- Web Browser ---
def search_web(query):
    print(f"🌍 Searching for: {query}")
    webbrowser.open(f"https://www.google.com/search?q={query}")

def open_url(url):
    """Open a specific URL in the default browser."""
    print(f"🌐 Opening URL: {url}")
    # Ensure URL has a protocol
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    webbrowser.open(url)

# --- Input Control ---
def type_text(text):
    print(f"⌨️ Typing: {text}")
    # Use clipboard for Unicode/Hindi support
    import pyperclip
    pyperclip.copy(text)
    pyautogui.hotkey('ctrl', 'v')

def press_key(key_name):
    print(f"🎹 Pressing key: {key_name}")
    try:
        keyboard.send(key_name)
    except Exception as e:
        print(f"❌ Error pressing key {key_name}: {e}")

def click_mouse():
    pyautogui.click()

def move_mouse(x, y):
    pyautogui.moveTo(x, y)

# --- Virtual Desktop Switching ---

def switch_desktop_left():
    """Switch to the left virtual desktop (Win+Ctrl+Left)."""
    print("🖥️ Switching to LEFT desktop...")
    pyautogui.hotkey('win', 'ctrl', 'left')
    time.sleep(0.8)  # Wait for desktop switch animation
    print("✅ Switched to left desktop")

def switch_desktop_right():
    """Switch to the right virtual desktop (Win+Ctrl+Right)."""
    print("🖥️ Switching to RIGHT desktop...")
    pyautogui.hotkey('win', 'ctrl', 'right')
    time.sleep(0.8)  # Wait for desktop switch animation
    print("✅ Switched to right desktop")

# --- Media Controls ---

def play_media():
    """Press media play/pause key."""
    print("▶️ Playing media...")
    pyautogui.press("playpause")

def pause_media():
    """Press media play/pause key to pause."""
    print("⏸️ Pausing media...")
    pyautogui.press("playpause")

def next_track():
    """Skip to next track."""
    print("⏭️ Next track...")
    pyautogui.press("nexttrack")

def prev_track():
    """Go to previous track."""
    print("⏮️ Previous track...")
    pyautogui.press("prevtrack")

def stop_media():
    """Stop media playback."""
    print("⏹️ Stopping media...")
    pyautogui.press("stop")

# --- Screen AI Actions ---

def screen_click_element(description):
    """Use vision AI to find and click a UI element on screen."""
    print(f"👁️ Screen AI: Finding and clicking '{description}'...")
    success = screen_ai.find_and_click_element(description)
    if not success:
        print(f"⚠️ Could not find '{description}' on screen")
    return success

def screen_type_in_field(text, field_description=None):
    """Use vision AI to find an input field, click it, and type text."""
    field_desc = field_description or "text input field, search bar, or prompt box"
    print(f"👁️ Screen AI: Finding input field and typing '{text}'...")
    success = screen_ai.find_and_type_in_field(text, field_desc, press_enter=True)
    if not success:
        print(f"⚠️ Could not find input field on screen")
    return success


# --- Flow Automation (Image -> Video -> Download) ---

FLOW_HOME_URL = "https://labs.google/fx/tools/flow"

FLOW_IMAGE_PROMPT_TEMPLATE = (
    "Shot in extreme macro perspective, a flawless, crystal-clear, and detail-rich {coloru} natural texture "
    "{object} rests on a wooden cutting board and sunlight casts a warm glow, creating a dramatic shadow. "
    "The camera captures the shimmering highlights and rainbow-like prismatic flares on the surface of the "
    "{object}. A black gloved hand holding a knife is poised above the {object}, with the blade reflecting "
    "light. The overall composition is centered, with the {object} as the focal point, and the background is "
    "softly blurred, emphasizing the subject's vivid colors and textures."
)

FLOW_VIDEO_PROMPT_TEMPLATE = (
    "Ultra-realistic 8K ASMR video of a human hand slicing a hyper-detailed {object} made of {material} on a wooden cutting board. "
    "The scene shows the dominant hand holding the knife above the object, fingers curled slightly inward, while the non-dominant "
    "hand gently steadies the object with fingertips resting lightly on top or at the side. The knife blade is angled diagonally "
    "with the tip slightly downward, beginning the slice at the front edge and following through toward the back, clearly revealing "
    "textures and interiors as it moves. "
    "The {object} has a smooth {surface_effect} surface with faint etched rind stripes, with a glossy, mirror-like reflective finish, "
    "with subtle glowing veins beneath the surface that emit a steady neon green radiance and intensify at the point of contact. "
    "As the knife cuts slowly and steadily with controlled pressure, a fine glowing fracture line forms instantly and travels smoothly "
    "along the blade edge, accompanied by tiny sparkling glass particles is revealed. Inside, layered neon glass flesh with a bright "
    "luminous core appears, glowing more intensely and softly pulsing once exposed to air. "
    "The slices separate cleanly with a precise, satisfying split, producing a crisp sequence of high-pitched glass scoring, a sharp "
    "clean crack, delicate cascading micro-tinkles, and a smooth crystalline glide followed by a soft resonant ring. The exposed "
    "interior emits a vibrant neon glow, casting sharp refracted light patterns and subtle green reflections across the wooden surface. "
    "Close-up macro shot with shallow depth of field and cinematic lighting to emphasize the glowing fracture line and the knife edge "
    "passing through the glass. The frame remains completely still throughout the entire cut, with no camera movement, no zoom, and "
    "no transition to another frame, maintaining a natural uninterrupted viewing experience. No background distractions, only the "
    "wooden surface in view. No voice, just immersive ASMR audio: fine glass scoring, crisp crack transitions, layered micro-tinkling "
    "shards, smooth slicing resonance, and a lingering high-frequency glass chime that gently fades into silence. "
    "Cinematic improvement: Add ultra-subtle light bloom at the cut line to heighten realism. "
    "Material consistency: Introduce slight internal tension lines before the crack for more believable physics. "
    "ASMR sound enhancement: Include a faint pre-contact micro-scrape plus tension hum just before the blade fully engages, microscopic "
    "crackle textures layered under the main snap, and a brief shimmering resonance after separation for a premium ASMR finish."
)


def _flow_wait(condition, timeout, interval=4, stable_checks=2):
    """Wait for a visual condition to become true."""
    print(f"⏳ Waiting for: {condition}")
    ok = screen_ai.wait_for_visual_condition(
        condition_description=condition,
        timeout=timeout,
        interval=interval,
        stable_checks=stable_checks,
    )
    print("✅ Condition reached" if ok else "⚠️ Condition wait timed out")
    return ok


def _safe_format_flow_template(template, **kwargs):
    """Format template with fallbacks for optional placeholders."""
    try:
        return template.format(**kwargs)
    except KeyError:
        return template


def _build_flow_prompts(subject, image_prompt=None, video_prompt=None, color="iridescent", material="glass", surface_effect="crystalline"):
    subject = (subject or "apple").strip()
    color = (color or "iridescent").strip()
    material = (material or "glass").strip()
    surface_effect = (surface_effect or "crystalline").strip()
    img = (
        image_prompt.strip()
        if image_prompt
        else _safe_format_flow_template(
            FLOW_IMAGE_PROMPT_TEMPLATE,
            subject=subject,
            object=subject,
            coloru=color,
            color=color,
        )
    )
    vid = (
        video_prompt.strip()
        if video_prompt
        else _safe_format_flow_template(
            FLOW_VIDEO_PROMPT_TEMPLATE,
            subject=subject,
            object=subject,
            material=material,
            surface_effect=surface_effect,
        )
    )
    return subject, img, vid


def _parse_flow_payload(target=None, value=None):
    """Support value as dict or JSON string for Gemini compatibility."""
    payload = {}

    if isinstance(value, dict):
        payload = value
    elif isinstance(value, str):
        raw = value.strip()
        if raw.startswith("{") and raw.endswith("}"):
            try:
                payload = json.loads(raw)
            except Exception:
                payload = {"subject": raw}
        elif raw:
            payload = {"subject": raw}

    subject = payload.get("subject") or target or "apple"
    color = payload.get("color") or payload.get("colour") or "iridescent"
    material = payload.get("material") or "glass"
    surface_effect = payload.get("surface_effect") or payload.get("surface") or "crystalline"
    image_prompt = payload.get("image_prompt")
    video_prompt = payload.get("video_prompt")
    image_timeout = int(payload.get("image_timeout", 120))
    video_timeout = int(payload.get("video_timeout", 240))

    return {
        "subject": subject,
        "color": color,
        "material": material,
        "surface_effect": surface_effect,
        "image_prompt": image_prompt,
        "video_prompt": video_prompt,
        "image_timeout": image_timeout,
        "video_timeout": video_timeout,
    }


FLOW_15_STEPS = {
    1: "open/create project",
    2: "select model picker",
    3: "select image mode",
    4: "focus image prompt input",
    5: "submit image generation",
    6: "select model picker again",
    7: "select model picker again",
    8: "select video mode",
    9: "select ingredient video mode",
    10: "select portrait mode",
    11: "click plus icon to add image",
    12: "focus video prompt input and submit",
    13: "open generated video thumbnail",
    14: "open download button",
    15: "select 720p option",
}


# Hardcoded click plan for Flow 15-step automation.
# Coordinates are project-owned and written directly in this file.
FLOW_15_CLICK_PLAN = [
    {"step": 1, "button": "left", "x": 1430, "y": 1534, "gap": 4.0},
    {"step": 2, "button": "left", "x": 1873, "y": 1669, "gap": 1.0},
    {"step": 3, "button": "left", "x": 1553, "y": 1194, "gap": 1.0},
    {"step": 4, "button": "left", "x": 1024, "y": 1599, "gap": 1.0},
    {"step": 5, "button": "left", "x": 1992, "y": 1676, "gap": 1.0},
    {"step": 6, "button": "left", "x": 1873, "y": 1669, "gap": 1.0},
    {"step": 7, "button": "left", "x": 1815, "y": 1193, "gap": 1.0},
    {"step": 8, "button": "left", "x": 1795, "y": 1261, "gap": 1.0},
    {"step": 9, "button": "left", "x": 1526, "y": 1336, "gap": 1.0},
    {"step": 10, "button": "left", "x": 894, "y": 1669, "gap": 1.0},
    {"step": 11, "button": "left", "x": 894, "y": 584, "gap": 1.0},
    {"step": 12, "button": "left", "x": 1024, "y": 1599, "gap": 1.0},
    {"step": 13, "button": "left", "x": 390, "y": 701, "gap": 1.0},
    {"step": 14, "button": "left", "x": 2374, "y": 229, "gap": 1.0},
    {"step": 15, "button": "left", "x": 2262, "y": 449, "gap": 1.0},
]


def _click_for_step(step_no, click):
    button = click.get("button", "left")
    if button not in ["left", "right", "middle"]:
        button = "left"
    x, y = click["x"], click["y"]
    _native_click_at(x, y, button=button)
    print(f"🖱️ Step {step_no}/15 ({FLOW_15_STEPS.get(step_no, 'step')}) -> {button} click at ({x}, {y})")


def _run_flow_coded_steps(image_prompt, video_prompt, image_timeout=120, video_timeout=240):
    """
    Coded 15-step engine:
    - Steps 1..15 are executed in order.
    - Coordinates are hardcoded in FLOW_15_CLICK_PLAN.
    - Delay behavior uses fixed per-step gaps from FLOW_15_CLICK_PLAN.
        - Special rules:
      step 4 -> paste image prompt
            step 9 -> every 3s observe image generation status
      step 12 -> paste video prompt and press Enter
      after step 12 -> every 5s observe video generation status
    """
    import pyperclip

    print("🎯 Running coded 15-step flow from in-code coordinates")
    print("🧭 Active coordinate map (step -> x,y):")
    for item in FLOW_15_CLICK_PLAN:
        print(f"   {item['step']}: ({item['x']}, {item['y']})")

    for item in FLOW_15_CLICK_PLAN:
        step_no = int(item["step"])
        _click_for_step(step_no, item)

        if step_no == 1:
            loaded = _flow_wait(
                "Flow project editor is visible with bottom prompt bar and page has loaded.",
                timeout=20,
                interval=2,
                stable_checks=1,
            )
            if not loaded:
                print("⚠️ Step 1 load check timed out; continuing with fixed-gap flow")

        time.sleep(max(0.0, float(item.get("gap", 1.0))))

        if step_no == 4:
            pyperclip.copy(image_prompt)
            pyautogui.hotkey("ctrl", "v")
            print("⌨️ Image prompt pasted after step 4")
            time.sleep(1.0)

        elif step_no == 9:
            print("👁️ Checking image generation status every 3 seconds...")
            image_ready = _flow_wait(
                "Image generation is complete: generated image result thumbnail is visible and there is no active loading spinner or percentage.",
                timeout=image_timeout,
                interval=3,
                stable_checks=1,
            )
            if not image_ready:
                print("⚠️ Image wait timed out after step 9")

        elif step_no == 12:
            time.sleep(1.0)
            pyperclip.copy(video_prompt)
            pyautogui.hotkey("ctrl", "v")
            print("⌨️ Video prompt pasted after step 12")
            time.sleep(1.0)
            pyautogui.press("enter")
            print("⏎ Enter pressed after step 12")

            # After 3 seconds, observe every 5s for completion signal.
            time.sleep(3.0)
            video_ready = _flow_wait(
                "Video generation is complete: a play button icon appears at top-left of thumbnail and there is no active loading percentage or spinner.",
                timeout=video_timeout,
                interval=5,
                stable_checks=1,
            )
            if not video_ready:
                print("⚠️ Video wait timed out after step 12")

    print("✅ Coded 15-step flow completed")
    return True


def run_flow_image_to_video(
    subject,
    image_prompt=None,
    video_prompt=None,
    image_timeout=120,
    video_timeout=240,
    color="iridescent",
    material="glass",
    surface_effect="crystalline",
):
    """
    Automate Google Flow pipeline:
    1) Open Flow
    2) Enter project editor (from any Flow page)
    3) Switch to image mode and generate image
    4) Wait for image completion
    5) Switch to video mode and generate video from that image
    6) Wait for video completion and download result
    """
    subject, image_prompt, video_prompt = _build_flow_prompts(
        subject,
        image_prompt,
        video_prompt,
        color=color,
        material=material,
        surface_effect=surface_effect,
    )

    print("=" * 70)
    print(f"🎬 Flow automation started for subject: {subject}")
    print(f"🖼️ Image prompt: {image_prompt}")
    print(f"🎥 Video prompt: {video_prompt}")
    print("=" * 70)

    # Start from Flow entry URL; click coordinates then drive full 15-step coded flow.
    open_url(FLOW_HOME_URL)
    time.sleep(2.5)

    preloaded = _flow_wait(
        "Flow home page is loaded and New project is visible.",
        timeout=20,
        interval=2,
        stable_checks=1,
    )
    if not preloaded:
        print("⚠️ Pre-step load check timed out (New project not confirmed); continuing")

    print("📂 Using in-code 15-step coordinate plan from actions.py")
    try:
        ok = _run_flow_coded_steps(
            image_prompt=image_prompt,
            video_prompt=video_prompt,
            image_timeout=image_timeout,
            video_timeout=video_timeout,
        )
        if ok:
            print("🏁 Flow automation finished (strict coded mode)")
            return True
        print("❌ Coded click flow execution did not complete")
        return False
    except Exception as e:
        print(f"❌ Strict coded mode failed: {e}")
        return False


# --- Brightness Control (Windows WMI via PowerShell) ---

def set_brightness(level):
    """Set screen brightness to a specific percentage."""
    level = max(0, min(100, int(level)))
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})"],
            capture_output=True, timeout=5
        )
        print(f"🔆 Brightness set to {level}%")
    except Exception as e:
        print(f"❌ Brightness error: {e}")

def change_brightness(change):
    """Change brightness up/down by a relative amount."""
    try:
        # Get current brightness
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness"],
            capture_output=True, text=True, timeout=5
        )
        current = int(result.stdout.strip()) if result.stdout.strip() else 50
        new_level = max(0, min(100, current + change))
        set_brightness(new_level)
    except Exception as e:
        print(f"❌ Brightness error: {e}")


# --- WiFi Control (netsh) ---

def wifi_on():
    try:
        subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "enabled"], capture_output=True, timeout=5)
        print("📶 WiFi enabled")
    except Exception as e:
        print(f"❌ WiFi error: {e}")

def wifi_off():
    try:
        subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "disabled"], capture_output=True, timeout=5)
        print("📴 WiFi disabled")
    except Exception as e:
        print(f"❌ WiFi error: {e}")


# --- Bluetooth Control (PowerShell) ---

def bluetooth_on():
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Add-Type -AssemblyName System.Runtime.WindowsRuntime; "
             "$radio = [Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime]::GetRadiosAsync().GetAwaiter().GetResult() | Where-Object { $_.Kind -eq 'Bluetooth' }; "
             "if ($radio) { $radio.SetStateAsync('On').GetAwaiter().GetResult() }"],
            capture_output=True, timeout=10
        )
        print("🔵 Bluetooth enabled")
    except Exception as e:
        # Fallback: open Bluetooth settings
        os.system("start ms-settings:bluetooth")
        print(f"🔵 Opened Bluetooth settings (auto-toggle failed: {e})")

def bluetooth_off():
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Add-Type -AssemblyName System.Runtime.WindowsRuntime; "
             "$radio = [Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime]::GetRadiosAsync().GetAwaiter().GetResult() | Where-Object { $_.Kind -eq 'Bluetooth' }; "
             "if ($radio) { $radio.SetStateAsync('Off').GetAwaiter().GetResult() }"],
            capture_output=True, timeout=10
        )
        print("⚫ Bluetooth disabled")
    except Exception as e:
        os.system("start ms-settings:bluetooth")
        print(f"⚫ Opened Bluetooth settings (auto-toggle failed: {e})")


# --- System Control ---
def system_action(action):
    if action == "SHUTDOWN":
        os.system("shutdown /s /t 1")
    elif action == "RESTART":
        os.system("shutdown /r /t 1")
    elif action == "SLEEP":
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    elif action == "LOCK":
        os.system("rundll32.exe user32.dll,LockWorkStation")
    elif action == "SCREENSHOT":
        img = pyautogui.screenshot()
        filename = f"screenshot_{int(time.time())}.png"
        img.save(filename)
        print(f"📸 Screenshot saved: {filename}")


# --- WhatsApp Messaging (WhatsApp Desktop automation via pyautogui) ---

def send_whatsapp_message(recipient, message):
    """Open WhatsApp Desktop, search for recipient, open chat, type message, send."""
    print(f"📱 WhatsApp: Sending to '{recipient}' → '{message}'")
    try:
        # Step 1: Open WhatsApp Desktop
        open_application("whatsapp")
        time.sleep(3)  # Wait for WhatsApp to fully load

        # Step 2: Focus on the search bar using Ctrl+F (WhatsApp Desktop shortcut)
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.5)

        # Step 3: Clear any existing text in search and type recipient name
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)

        # Type the recipient name character by character for reliability
        import pyperclip
        pyperclip.copy(recipient)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1.5)  # Wait for search results to populate

        # Step 4: Press Enter to select the top search result (open the chat)
        pyautogui.press('enter')
        time.sleep(1)  # Wait for chat to open

        # Step 5: Type the message (use clipboard for Unicode/Hindi support)
        pyperclip.copy(message)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.3)

        # Step 6: Press Enter to send the message
        pyautogui.press('enter')
        print(f"✅ WhatsApp message sent to {recipient}!")

    except Exception as e:
        print(f"❌ WhatsApp error: {e}")


# --- Single Action Executor (used by intent classifier) ---
def execute_action(action, target=None, value=None):
    """Execute a single action directly. Used by local intent classifier."""
    print(f"⚙️ Executing: {action} | Target: {target} | Value: {value}")
    try:
        if action == "VOLUME_UP":
            change_volume(10)
        elif action == "VOLUME_DOWN":
            change_volume(-10)
        elif action == "SET_VOLUME":
            if value is not None:
                set_volume(value)
        elif action == "MUTE":
            mute_volume()
        elif action == "UNMUTE":
            unmute_volume()

        elif action == "BRIGHTNESS_UP":
            change_brightness(10)
        elif action == "BRIGHTNESS_DOWN":
            change_brightness(-10)
        elif action == "SET_BRIGHTNESS":
            if value is not None:
                set_brightness(int(value))

        elif action == "WIFI_ON":
            wifi_on()
        elif action == "WIFI_OFF":
            wifi_off()
        elif action == "BLUETOOTH_ON":
            bluetooth_on()
        elif action == "BLUETOOTH_OFF":
            bluetooth_off()

        elif action == "OPEN_APP":
            if target:
                open_application(target)
        elif action == "CLOSE_APP":
            if target:
                close_application(target)

        elif action == "SEARCH_WEB":
            if value:
                search_web(value)
            elif target:
                search_web(target)

        elif action == "OPEN_URL":
            url = value or target
            if url:
                open_url(str(url))

        elif action == "TYPE_TEXT":
            if value:
                type_text(str(value))

        elif action == "PRESS_KEYBOARD_KEY":
            if value:
                press_key(str(value))
            elif target:
                press_key(str(target))

        elif action == "CLICK_MOUSE":
            click_mouse()

        elif action == "MOVE_MOUSE":
            if target and value:
                move_mouse(int(target), int(value))
        # --- Virtual Desktop ---
        elif action == "SWITCH_DESKTOP_LEFT":
            switch_desktop_left()
        elif action == "SWITCH_DESKTOP_RIGHT":
            switch_desktop_right()

        # --- Media Controls ---
        elif action == "PLAY_MEDIA":
            play_media()
        elif action == "PAUSE_MEDIA":
            pause_media()
        elif action == "STOP_MEDIA":
            stop_media()
        elif action == "NEXT_TRACK":
            next_track()
        elif action == "PREV_TRACK":
            prev_track()

        # --- Screen AI Actions ---
        elif action == "SCREEN_CLICK_ELEMENT":
            desc = value or target or "button"
            screen_click_element(str(desc))
        elif action == "SCREEN_TYPE_IN_FIELD":
            text_to_type = str(value) if value else ""
            field_desc = str(target) if target else None
            if text_to_type:
                screen_type_in_field(text_to_type, field_desc)
            else:
                print("⚠️ SCREEN_TYPE_IN_FIELD needs value (text to type)")

        elif action == "FLOW_ASMR_VIDEO":
            payload = _parse_flow_payload(target=target, value=value)
            run_flow_image_to_video(
                subject=payload["subject"],
                image_prompt=payload["image_prompt"],
                video_prompt=payload["video_prompt"],
                image_timeout=payload["image_timeout"],
                video_timeout=payload["video_timeout"],
                color=payload["color"],
                material=payload["material"],
                surface_effect=payload["surface_effect"],
            )

        elif action == "SEND_WHATSAPP":
            if target and value:
                send_whatsapp_message(target, str(value))
            else:
                print("⚠️ SEND_WHATSAPP needs both target (recipient) and value (message)")

        elif action == "SEND_WHATSAPP_FILE_SMART":
            # value carries full natural command, e.g., "papa ko resume bhejo"
            cmd = str(value).strip() if value else ""
            if not cmd and target:
                cmd = str(target).strip()
            if cmd:
                wa_handle_send_command(cmd)
            else:
                print("⚠️ SEND_WHATSAPP_FILE_SMART needs value command text")

        elif action == "SEND_WHATSAPP_VOICE_NOTE":
            # target: contact name, value: voice note text
            if target and value:
                ok = wa_send_voice_note(str(target), str(value))
                if ok:
                    print(f"✅ Voice note sent to {target}")
                else:
                    print(f"❌ Voice note send failed for {target}")
            else:
                print("⚠️ SEND_WHATSAPP_VOICE_NOTE needs target (contact) and value (text)")

        elif action in ["SHUTDOWN", "RESTART", "SLEEP", "LOCK", "SCREENSHOT"]:
            system_action(action)

        elif action == "WAIT":
            sec = float(value) if value else 1.0
            time.sleep(sec)

        # Talk-only intents (no PC action needed)
        elif action in ["GREETING", "HOW_ARE_YOU", "THANKS", "WHO_ARE_YOU"]:
            pass  # Only speak, no action

        else:
            print(f"⚠️ Unknown action: {action}")

    except Exception as e:
        print(f"❌ Error executing {action}: {e}")


# --- Steps Executor (used by Gemini brain) ---
def execute_steps(steps):
    if not steps:
        return
    for step in steps:
        execute_action(
            action=step.get("action"),
            target=step.get("target"),
            value=step.get("value"),
        )
