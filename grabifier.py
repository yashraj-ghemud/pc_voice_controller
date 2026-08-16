"""
Grabifier - Standalone mouse coordinate grab tool.

Features:
- Full-screen overlay with live horizontal/vertical crosshair.
- Cursor coordinate label near pointer: (x, y).
- Right-side panel (Playwright-like) that records mouse clicks.
- Records click type (left/middle/right), x/y coordinates, and timestamp.
- Saves logs in the same folder as this script as both JSON and CSV.

Usage:
1) Run: python grabifier.py
2) Move mouse to see crosshair and coordinate readout.
3) Press R to start recording clicks.
4) Press P to pause/resume recording.
5) Press C to clear logs, S to save logs, Esc to quit.
"""

from __future__ import annotations

import csv
import json
import time
import ctypes
import threading
from dataclasses import dataclass, asdict
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

import pyautogui
import pyperclip

try:
    import screen_ai
except Exception:
    screen_ai = None


@dataclass
class ClickEvent:
    index: int
    timestamp: str
    epoch: float
    button: str
    x: int
    y: int


class GrabifierApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.records: list[ClickEvent] = []
        self.recording_active = False
        self.recording_paused = False
        self.capture_suspended = False
        self.replay_running = False
        self.poll_job = None

        self._prev_mouse_down = {"left": False, "middle": False, "right": False}
        self._prev_key_down = {"r": False, "p": False, "c": False, "s": False, "f": False, "esc": False}

        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()

        self._configure_overlay_window()
        self._build_overlay_canvas()
        self._build_side_panel()
        self._bind_events()
        self.root.after(120, self._make_overlay_clickthrough_windows)
        self.root.after(650, self._make_overlay_clickthrough_windows)
        self._start_global_polling()

    def _configure_overlay_window(self) -> None:
        self.root.title("Grabifier Overlay")
        self.root.geometry(f"{self.screen_w}x{self.screen_h}+0+0")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        # Slight transparency so underlying UI stays visible.
        self.root.attributes("-alpha", 0.15)
        self.root.configure(bg="#101010")

    def _build_overlay_canvas(self) -> None:
        self.canvas = tk.Canvas(self.root, bg="#101010", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.h_line = self.canvas.create_line(0, 0, self.screen_w, 0, fill="#00ffaa", width=1)
        self.v_line = self.canvas.create_line(0, 0, 0, self.screen_h, fill="#00ffaa", width=1)
        self.coord_text = self.canvas.create_text(
            12,
            12,
            text="(0, 0)",
            fill="#ffffff",
            anchor="nw",
            font=("Consolas", 11, "bold"),
        )

        self.status_rect = self.canvas.create_rectangle(0, 0, 0, 0, fill="#111111", outline="")
        self.status_text = self.canvas.create_text(
            0,
            0,
            text="",
            fill="#ffffff",
            anchor="center",
            font=("Segoe UI", 11, "bold"),
        )
        self.canvas.itemconfigure(self.status_rect, state="hidden")
        self.canvas.itemconfigure(self.status_text, state="hidden")
        self.status_hide_job = None

    def _build_side_panel(self) -> None:
        self.panel = tk.Toplevel(self.root)
        self.panel.title("Grabifier Recorder")
        panel_w = 430
        panel_h = min(self.screen_h, 840)
        panel_x = max(0, self.screen_w - panel_w)
        panel_y = 0
        self.panel.geometry(f"{panel_w}x{panel_h}+{panel_x}+{panel_y}")
        self.panel.attributes("-topmost", True)
        self.panel.configure(bg="#111111")
        self.panel.protocol("WM_DELETE_WINDOW", self.quit_all)

        header = tk.Frame(self.panel, bg="#111111")
        header.pack(fill="x", padx=10, pady=(10, 6))

        title = tk.Label(
            header,
            text="Grabifier Click Log",
            fg="#ffffff",
            bg="#111111",
            font=("Segoe UI", 12, "bold"),
        )
        title.pack(side="left")

        self.counter_var = tk.StringVar(value="Events: 0")
        counter = tk.Label(
            header,
            textvariable=self.counter_var,
            fg="#bbbbbb",
            bg="#111111",
            font=("Consolas", 10),
        )
        counter.pack(side="right")

        table_frame = tk.Frame(self.panel, bg="#111111")
        table_frame.pack(fill="both", expand=True, padx=10, pady=6)

        cols = ("#", "time", "button", "x", "y")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=20)
        self.tree.heading("#", text="#")
        self.tree.heading("time", text="Time")
        self.tree.heading("button", text="Button")
        self.tree.heading("x", text="X")
        self.tree.heading("y", text="Y")

        self.tree.column("#", width=45, anchor="center")
        self.tree.column("time", width=120, anchor="center")
        self.tree.column("button", width=80, anchor="center")
        self.tree.column("x", width=75, anchor="center")
        self.tree.column("y", width=75, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        btn_row = tk.Frame(self.panel, bg="#111111")
        btn_row.pack(fill="x", padx=10, pady=(4, 10))

        save_btn = tk.Button(
            btn_row,
            text="Save Logs",
            command=self.save_logs,
            bg="#1f6feb",
            fg="#ffffff",
            activebackground="#2f81f7",
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=7,
        )
        save_btn.pack(side="left")

        clear_btn = tk.Button(
            btn_row,
            text="Clear",
            command=self.clear_logs,
            bg="#30363d",
            fg="#ffffff",
            activebackground="#484f58",
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=7,
        )
        clear_btn.pack(side="left", padx=(8, 0))

        run_btn = tk.Button(
            btn_row,
            text="Run Flow Replay",
            command=self.start_flow_replay,
            bg="#238636",
            fg="#ffffff",
            activebackground="#2ea043",
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=7,
        )
        run_btn.pack(side="left", padx=(8, 0))

        prompt_box = tk.Frame(self.panel, bg="#111111")
        prompt_box.pack(fill="x", padx=10, pady=(0, 10))

        img_lbl = tk.Label(prompt_box, text="Image prompt (used after click #4):", fg="#d0d7de", bg="#111111")
        img_lbl.pack(anchor="w")
        self.image_prompt_input = tk.Text(prompt_box, height=3, wrap="word", bg="#0d1117", fg="#ffffff", insertbackground="#ffffff")
        self.image_prompt_input.pack(fill="x", pady=(2, 8))
        self.image_prompt_input.insert("1.0", "Ultra realistic macro ASMR still image of a crystal glass apple on wooden board, knife above subject, cinematic light")

        vid_lbl = tk.Label(prompt_box, text="Video prompt (used after click #8):", fg="#d0d7de", bg="#111111")
        vid_lbl.pack(anchor="w")
        self.video_prompt_input = tk.Text(prompt_box, height=3, wrap="word", bg="#0d1117", fg="#ffffff", insertbackground="#ffffff")
        self.video_prompt_input.pack(fill="x", pady=(2, 8))
        self.video_prompt_input.insert("1.0", "ASMR cutting video, close-up macro shot, slow satisfying cut, realistic texture motion, 9:16")

        info = tk.Label(
            btn_row,
            text="R Start | P Pause | S Save | C Clear | F Run Replay | Esc Exit",
            fg="#bbbbbb",
            bg="#111111",
            font=("Consolas", 10),
        )
        info.pack(side="right")

    def _bind_events(self) -> None:
        # Keep panel close shortcut; global keys are handled by polling.
        self.panel.bind("<Escape>", lambda _e: self.quit_all())

    def _make_overlay_clickthrough_windows(self) -> None:
        """Allow clicks to pass through overlay window to real apps below."""
        try:
            hwnd = self.root.winfo_id()
            user32 = ctypes.windll.user32

            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_NOACTIVATE = 0x08000000

            SWP_NOSIZE = 0x0001
            SWP_NOMOVE = 0x0002
            SWP_NOZORDER = 0x0004
            SWP_NOACTIVATE = 0x0010
            SWP_FRAMECHANGED = 0x0020

            get_long = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
            set_long = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)

            targets = [hwnd]
            parent_hwnd = user32.GetParent(hwnd)
            if parent_hwnd:
                targets.append(parent_hwnd)

            for h in targets:
                ex_style = get_long(h, GWL_EXSTYLE)
                ex_style |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
                set_long(h, GWL_EXSTYLE, ex_style)
                user32.SetWindowPos(
                    h,
                    0,
                    0,
                    0,
                    0,
                    0,
                    SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED,
                )
        except Exception:
            # If unsupported, tool still works in normal mode.
            pass

    def _start_global_polling(self) -> None:
        self._poll_global_state()

    def _is_vk_down(self, vk_code: int) -> bool:
        return bool(ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000)

    def _poll_global_state(self) -> None:
        x, y = self.root.winfo_pointerx(), self.root.winfo_pointery()
        self._update_crosshair(x, y)

        # Mouse buttons (global)
        mouse_map = {
            "left": 0x01,
            "right": 0x02,
            "middle": 0x04,
        }
        for button, vk in mouse_map.items():
            down = self._is_vk_down(vk)
            if down and not self._prev_mouse_down[button]:
                self._record_click(button, x, y)
            self._prev_mouse_down[button] = down

        # Keyboard controls (global)
        key_map = {
            "r": 0x52,
            "p": 0x50,
            "c": 0x43,
            "s": 0x53,
            "f": 0x46,
            "esc": 0x1B,
        }
        for key, vk in key_map.items():
            down = self._is_vk_down(vk)
            if down and not self._prev_key_down[key]:
                self._handle_key_action(key)
            self._prev_key_down[key] = down

        self.poll_job = self.root.after(16, self._poll_global_state)

    def _handle_key_action(self, key: str) -> None:
        if key == "r":
            self.start_recording()
        elif key == "p":
            self.toggle_pause()
        elif key == "c":
            self.clear_logs(show_status=True)
        elif key == "s":
            self.save_logs(show_popup=False, show_status=True)
        elif key == "f":
            self.start_flow_replay()
        elif key == "esc":
            self.quit_all()

    def on_keypress(self, event: tk.Event) -> None:
        key = event.keysym.lower()
        if key == "r":
            self.start_recording()
        elif key == "p":
            self.toggle_pause()
        elif key == "c":
            self.clear_logs(show_status=True)
        elif key == "s":
            self.save_logs(show_popup=False, show_status=True)

    def _update_crosshair(self, x: int, y: int) -> None:
        self.canvas.coords(self.h_line, 0, y, self.screen_w, y)
        self.canvas.coords(self.v_line, x, 0, x, self.screen_h)

        label_x = x + 14
        label_y = y + 14

        if label_x > self.screen_w - 120:
            label_x = x - 108
        if label_y > self.screen_h - 28:
            label_y = y - 22

        self.canvas.coords(self.coord_text, label_x, label_y)
        self.canvas.itemconfig(self.coord_text, text=f"({x}, {y})")

    def _record_click(self, button: str, x: int, y: int) -> None:
        if self.capture_suspended:
            return
        if not self.recording_active or self.recording_paused:
            return

        now_epoch = time.time()
        ts = time.strftime("%H:%M:%S", time.localtime(now_epoch))
        item = ClickEvent(
            index=len(self.records) + 1,
            timestamp=ts,
            epoch=now_epoch,
            button=button,
            x=x,
            y=y,
        )
        self.records.append(item)

        self.tree.insert("", "end", values=(item.index, item.timestamp, item.button, item.x, item.y))
        self.counter_var.set(f"Events: {len(self.records)}")

    def start_recording(self) -> None:
        if self.recording_active and not self.recording_paused:
            self.show_status("Recording already ON", "#1f6feb")
            return

        if not self.recording_active:
            self.recording_active = True
            self.recording_paused = False
            self.show_status("Recording STARTED", "#2ea043")
            return

        self.recording_paused = False
        self.show_status("Recording RESUMED", "#2ea043")

    def toggle_pause(self) -> None:
        if not self.recording_active:
            self.show_status("Press R first to start recording", "#d29922")
            return

        self.recording_paused = not self.recording_paused
        if self.recording_paused:
            self.show_status("Recording PAUSED", "#d29922")
        else:
            self.show_status("Recording RESUMED", "#2ea043")

    def clear_logs(self, show_status: bool = False) -> None:
        self.records.clear()
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.counter_var.set("Events: 0")
        if show_status:
            self.show_status("Logs CLEARED", "#30363d")

    def save_logs(self, show_popup: bool = True, show_status: bool = False) -> None:
        if not self.records:
            if show_popup:
                messagebox.showinfo("Grabifier", "No click events to save yet.")
            if show_status:
                self.show_status("No events to save", "#d29922")
            return

        ts = time.strftime("%Y%m%d_%H%M%S")
        base = Path(__file__).resolve().parent / f"grabifier_log_{ts}"
        json_path = base.with_suffix(".json")
        csv_path = base.with_suffix(".csv")

        with json_path.open("w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in self.records], f, ensure_ascii=False, indent=2)

        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["index", "timestamp", "epoch", "button", "x", "y"])
            for r in self.records:
                writer.writerow([r.index, r.timestamp, r.epoch, r.button, r.x, r.y])

        if show_popup:
            messagebox.showinfo(
                "Grabifier",
                f"Saved:\n{json_path.name}\n{csv_path.name}",
            )
        if show_status:
            self.show_status(f"Saved {json_path.name} and {csv_path.name}", "#1f6feb")

    def show_status(self, message: str, bg_color: str = "#111111", duration_ms: int = 1600) -> None:
        text_w = max(280, min(760, len(message) * 8 + 40))
        x1 = (self.screen_w - text_w) // 2
        x2 = x1 + text_w
        y2 = self.screen_h - 24
        y1 = y2 - 40
        text_x = self.screen_w // 2
        text_y = (y1 + y2) // 2

        self.canvas.coords(self.status_rect, x1, y1, x2, y2)
        self.canvas.coords(self.status_text, text_x, text_y)
        self.canvas.itemconfig(self.status_rect, fill=bg_color, state="normal")
        self.canvas.itemconfig(self.status_text, text=message, state="normal")
        self.canvas.tag_raise(self.status_rect)
        self.canvas.tag_raise(self.status_text)

        if self.status_hide_job is not None:
            self.root.after_cancel(self.status_hide_job)
        self.status_hide_job = self.root.after(duration_ms, self.hide_status)

    def _show_status_threadsafe(self, message: str, bg_color: str = "#111111", duration_ms: int = 1600) -> None:
        self.root.after(0, lambda: self.show_status(message, bg_color, duration_ms))

    def _wait_condition_with_vision(self, condition: str, timeout: int, fallback_seconds: int) -> bool:
        if screen_ai is None:
            time.sleep(fallback_seconds)
            return True

        try:
            return bool(
                screen_ai.wait_for_visual_condition(
                    condition_description=condition,
                    timeout=timeout,
                    interval=4,
                    stable_checks=2,
                )
            )
        except Exception:
            time.sleep(fallback_seconds)
            return True

    def _do_real_click(self, event: ClickEvent) -> None:
        button = event.button if event.button in ("left", "middle", "right") else "left"
        pyautogui.click(event.x, event.y, button=button)

    def start_flow_replay(self) -> None:
        if self.replay_running:
            self.show_status("Replay already running", "#d29922")
            return

        if len(self.records) < 14:
            self.show_status("Need at least 14 recorded clicks", "#d29922", 2200)
            return

        self.replay_running = True
        worker = threading.Thread(target=self._run_flow_replay_worker, daemon=True)
        worker.start()

    def _run_flow_replay_worker(self) -> None:
        old_pause = self.recording_paused
        self.recording_paused = True
        self.capture_suspended = True

        image_prompt = self.image_prompt_input.get("1.0", "end").strip()
        video_prompt = self.video_prompt_input.get("1.0", "end").strip()
        recorded = list(self.records[:14])

        try:
            self._show_status_threadsafe("Replay starts in 3 sec (steps 1-14)", "#1f6feb", 1900)
            time.sleep(3)

            for idx, event in enumerate(recorded, start=1):
                if idx > 1:
                    prev_event = recorded[idx - 2]
                    delay = max(0.0, float(event.epoch) - float(prev_event.epoch))
                    time.sleep(delay)

                self._do_real_click(event)

                if idx == 4:
                    pyperclip.copy(image_prompt)
                    pyautogui.hotkey("ctrl", "v")
                    self._show_status_threadsafe("Image prompt pasted after click #4", "#2ea043", 1500)
                    time.sleep(0.35)

                elif idx == 5:
                    self._show_status_threadsafe("Waiting for image generation...", "#1f6feb", 1800)
                    ok = self._wait_condition_with_vision(
                        condition=(
                            "Generated image is visible and no active loading spinner/progress for image generation remains."
                        ),
                        timeout=150,
                        fallback_seconds=45,
                    )
                    if ok:
                        self._show_status_threadsafe("Image generation complete", "#2ea043", 1800)
                    else:
                        self._show_status_threadsafe("Image check timed out, continuing", "#d29922", 1800)

                elif idx == 8:
                    pyperclip.copy(video_prompt)
                    pyautogui.hotkey("ctrl", "v")
                    self._show_status_threadsafe("Video prompt pasted after click #8", "#2ea043", 1500)
                    time.sleep(0.35)

                elif idx == 9:
                    self._show_status_threadsafe("Waiting for video generation...", "#1f6feb", 1800)
                    ok = self._wait_condition_with_vision(
                        condition=(
                            "Generated video is visible and playable, and no active generation spinner/progress is visible."
                        ),
                        timeout=300,
                        fallback_seconds=60,
                    )
                    if ok:
                        self._show_status_threadsafe("Video generation complete", "#2ea043", 1800)
                    else:
                        self._show_status_threadsafe("Video check timed out, continuing", "#d29922", 1800)

            self._show_status_threadsafe("Flow replay finished (steps 1-14)", "#2ea043", 2200)
        except Exception as e:
            self._show_status_threadsafe(f"Replay error: {e}", "#da3633", 2600)
        finally:
            self.capture_suspended = False
            self.recording_paused = old_pause
            self.replay_running = False

    def hide_status(self) -> None:
        self.canvas.itemconfigure(self.status_rect, state="hidden")
        self.canvas.itemconfigure(self.status_text, state="hidden")
        self.status_hide_job = None

    def quit_all(self) -> None:
        if self.poll_job is not None:
            try:
                self.root.after_cancel(self.poll_job)
            except Exception:
                pass
        try:
            self.panel.destroy()
        except Exception:
            pass
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    app = GrabifierApp(root)
    app.show_status("Press R to start recording", "#1f6feb", duration_ms=2200)
    root.mainloop()


if __name__ == "__main__":
    main()
