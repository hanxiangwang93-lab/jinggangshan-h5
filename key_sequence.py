import ctypes
import time
import threading
import tkinter as tk
from tkinter import ttk

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

SC_SPACE = 0x39
SC_F = 0x21
SC_ESCAPE = 0x01

KEYS = [
    ("Space ①", SC_SPACE),
    ("Space ②", SC_SPACE),
    ("Space ③", SC_SPACE),
    ("F",       SC_F),
    ("Escape",  SC_ESCAPE),
]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("ki", KEYBDINPUT),
        ("padding", ctypes.c_ubyte * 8),
    ]


def press_key(sc):
    down = INPUT(
        type=INPUT_KEYBOARD,
        ki=KEYBDINPUT(wVk=0, wScan=sc, dwFlags=KEYEVENTF_SCANCODE, time=0, dwExtraInfo=None),
    )
    up = INPUT(
        type=INPUT_KEYBOARD,
        ki=KEYBDINPUT(wVk=0, wScan=sc, dwFlags=KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, time=0, dwExtraInfo=None),
    )
    ctypes.windll.user32.SendInput(1, ctypes.pointer(down), ctypes.sizeof(INPUT))
    time.sleep(0.08)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(up), ctypes.sizeof(INPUT))
    time.sleep(0.08)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("KeySequence")
        self.root.geometry("340x320")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e1e")

        self.running = False
        self.count = 0
        self.loop_thread = None

        self._build_ui()

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 13, "bold"), foreground="#ffffff", background="#1e1e1e")
        style.configure("Key.TLabel", font=("Segoe UI", 11), foreground="#cccccc", background="#1e1e1e")
        style.configure("Count.TLabel", font=("Segoe UI", 10), foreground="#888888", background="#1e1e1e")
        style.configure("Status.TLabel", font=("Segoe UI", 11, "bold"), foreground="#888888", background="#1e1e1e")
        style.configure("Start.TButton", font=("Segoe UI", 12, "bold"), padding=10)
        style.configure("Stop.TButton", font=("Segoe UI", 12, "bold"), padding=10)

        # Title
        ttk.Label(self.root, text="按键序列工具", style="Title.TLabel").pack(pady=(20, 5))

        # Sequence display
        ttk.Label(self.root, text="序列:  Space  →  Space  →  Space  →  F  →  Escape",
                  style="Key.TLabel").pack(pady=(0, 10))

        # Arrow chain
        arrow_frame = tk.Frame(self.root, bg="#1e1e1e")
        arrow_frame.pack(pady=5)

        for i, (name, _) in enumerate(KEYS):
            lbl = tk.Label(arrow_frame, text=name, font=("Segoe UI", 10, "bold"),
                           fg="#ffdd00", bg="#2a2a2a", padx=10, pady=6,
                           relief="flat", borderwidth=0)
            lbl.pack(side="left", padx=3)
            if i < len(KEYS) - 1:
                tk.Label(arrow_frame, text="→", font=("Segoe UI", 10),
                         fg="#555555", bg="#1e1e1e").pack(side="left", padx=2)

        # Count
        self.count_label = ttk.Label(self.root, text="执行次数: 0", style="Count.TLabel")
        self.count_label.pack(pady=(15, 5))

        # Status
        self.status_label = ttk.Label(self.root, text="等待开始...", style="Status.TLabel")
        self.status_label.pack(pady=(0, 15))

        # Buttons
        btn_frame = tk.Frame(self.root, bg="#1e1e1e")
        btn_frame.pack(pady=5)

        self.start_btn = ttk.Button(btn_frame, text="▶  开始", style="Start.TButton", command=self.start)
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="■  停止", style="Stop.TButton", command=self.stop, state="disabled")
        self.stop_btn.pack(side="left", padx=5)

    def start(self):
        self.running = True
        self.count = 0
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_label.config(text="运行中...", foreground="#4caf50")
        self.count_label.config(text="执行次数: 0")
        self.loop_thread = threading.Thread(target=self._loop, daemon=True)
        self.loop_thread.start()

    def stop(self):
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_label.config(text=f"已停止 (共 {self.count} 次)", foreground="#888888")

    def _highlight_key(self, idx):
        """Update status to show current key"""
        if not self.running:
            return
        name = KEYS[idx][0]
        self.status_label.config(text=f"▶ {name}", foreground="#ffdd00")

    def _loop(self):
        while self.running:
            self.count += 1
            self.root.after(0, lambda c=self.count: self.count_label.config(text=f"执行次数: {c}"))
            self.root.after(0, lambda c=self.count: self.status_label.config(text=f"第 {c} 次执行中...", foreground="#ffdd00"))

            for i, (name, sc) in enumerate(KEYS):
                if not self.running:
                    return
                self.root.after(0, lambda n=name: self.status_label.config(text=f"▶ {n}", foreground="#ffdd00"))
                press_key(sc)
                time.sleep(0.25)

            if not self.running:
                return
            self.root.after(0, lambda: self.status_label.config(text="等待 3 秒...", foreground="#888888"))
            time.sleep(3)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
