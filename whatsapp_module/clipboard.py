import os
import subprocess


def copy_file_to_clipboard(file_path: str) -> bool:
    """Copy file to Windows clipboard using PowerShell Set-Clipboard."""
    if not file_path:
        return False

    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        return False

    ps_cmd = f'Set-Clipboard -Path "{abs_path}"'
    try:
        subprocess.run(["powershell", "-command", ps_cmd], check=True)
        return True
    except Exception as e:
        print(f"❌ Clipboard copy failed: {e}")
        return False
