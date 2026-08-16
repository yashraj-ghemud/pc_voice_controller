import sys
import os
import time

print("🔍 Starting Verification...")

def test_imports():
    print("\n📦 Testing Imports...")
    modules = ["json", "time", "webbrowser", "platform", "ctypes", "comtypes", "asyncio"]
    pip_modules = ["pyautogui", "keyboard", "AppOpener", "pycaw", "edge_tts", "playsound"]
    
    all_passed = True
    
    for mod in modules:
        try:
            __import__(mod)
            print(f"✅ {mod} imported")
        except ImportError as e:
            print(f"❌ {mod} FAILED: {e}")
            all_passed = False

    for mod in pip_modules:
        try:
            __import__(mod)
            print(f"✅ {mod} imported")
        except ImportError as e:
            print(f"❌ {mod} FAILED (Need pip install): {e}")
            all_passed = False
            
    return all_passed

def test_actions_mock():
    print("\n⚙️ Testing Actions (Mock)...")
    try:
        import actions
        # We won't run them to avoid side effects, just check existence
        if hasattr(actions, 'execute_steps'):
            print("✅ actions.execute_steps exists")
        else:
            print("❌ actions.execute_steps MISSING")
            return False
    except ImportError:
        print("❌ Cannot import actions.py")
        return False
    return True

def test_tts_mock():
    print("\n🗣️ Testing TTS (File Check)...")
    if os.path.exists("tts.py"):
        print("✅ tts.py exists")
        try:
            import tts
            if hasattr(tts, 'speak'):
                print("✅ tts.speak exists")
            else:
                 print("❌ tts.speak MISSING")
                 return False
        except ImportError:
            print("❌ Cannot import tts.py")
            return False
    else:
        print("❌ tts.py MISSING")
        return False
    return True

def main():
    if not test_imports():
        print("\n❌ CRITICAL: Dependencies missing. Please run 'pip install -r requirements.txt'")
        return

    if not test_actions_mock():
        print("\n❌ CRITICAL: actions.py has issues.")
        return

    if not test_tts_mock():
        print("\n❌ CRITICAL: tts.py has issues.")
        return

    print("\n✅ All Static Checks Passed!")
    print("🚀 You can now run 'python main.py'")

if __name__ == "__main__":
    main()
