import tkinter as tk
import pyautogui
from pynput import mouse
import time

class CoordTool:
    def __init__(self, root):
        self.root = root
        self.root.title("滑鼠座標紀錄工具")
        self.root.geometry("800x300")
        self.root.resizable(False, False)

        self.xy1 = None
        self.xy2 = None

        self.last_click_time = 0
        self.double_click_interval = 0.35  # 連點兩下最大間隔（秒）

        self.label_live = tk.Label(root, text="即時座標：", font=("Consolas", 16))
        self.label_live.pack(pady=5)

        self.label_1 = tk.Label(root, text="雙擊#1：-", font=("Consolas", 14), fg="blue")
        self.label_1.pack()
        self.label_2 = tk.Label(root, text="雙擊#2：-", font=("Consolas", 14), fg="blue")
        self.label_2.pack()
        self.label_diff = tk.Label(root, text="差值：-", font=("Consolas", 14), fg="green")
        self.label_diff.pack(pady=5)

        self.btn_reset = tk.Button(root, text="Reset", font=("Consolas", 12), command=self.reset)
        self.btn_reset.pack(pady=7)

        # 啟動全域滑鼠監聽
        self.listener = mouse.Listener(on_click=self.on_global_click)
        self.listener.start()

        self.update_position()

    def update_position(self):
        x, y = pyautogui.position()
        self.label_live.config(text=f"即時座標：X:{x}  Y:{y}")
        self.root.after(30, self.update_position)

    def on_global_click(self, x, y, button, pressed):
        # 只處理左鍵「按下」事件
        if pressed and button == mouse.Button.left:
            now = time.time()
            if now - self.last_click_time < self.double_click_interval:
                # 符合雙擊，主執行緒處理
                self.root.after(0, self.record_double_click, x, y)
                self.last_click_time = 0  # 重置，避免三連擊被認為兩次雙擊
            else:
                self.last_click_time = now

    def record_double_click(self, x, y):
        if self.xy1 is None:
            self.xy1 = (x, y)
            self.label_1.config(text=f"雙擊#1：X:{x}  Y:{y}")
            self.label_2.config(text="雙擊#2：-")
            self.label_diff.config(text="差值：-")
            self.xy2 = None
        elif self.xy2 is None:
            self.xy2 = (x, y)
            self.label_2.config(text=f"雙擊#2：X:{x}  Y:{y}")
            self.calc_diff()

    def calc_diff(self):
        if self.xy1 and self.xy2:
            dx = abs(self.xy2[0] - self.xy1[0])
            dy = abs(self.xy2[1] - self.xy1[1])
            self.label_diff.config(text=f"差值：ΔX={dx}  ΔY={dy}  (width={dx}, height={dy})")

    def reset(self):
        self.xy1 = None
        self.xy2 = None
        self.label_1.config(text="雙擊#1：-")
        self.label_2.config(text="雙擊#2：-")
        self.label_diff.config(text="差值：-")

if __name__ == "__main__":
    root = tk.Tk()
    app = CoordTool(root)
    root.mainloop()
