import sys
import threading
import time
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt
from pynput import mouse, keyboard

MONITOR_KEYS = ['ctrl', 'space']

class DoubleClickRecorder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("全域滑鼠雙擊+按鍵時間")
        self.setGeometry(350, 300, 400, 250)

        self.label1 = QLabel("第一次雙擊：尚未記錄")
        self.label2 = QLabel("第二次雙擊：尚未記錄")
        self.label3 = QLabel("區域尺寸：尚未計算")
        self.key_label = QLabel("按鍵狀態")
        self.timing_label = QLabel("")
        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self.reset_all)

        vbox = QVBoxLayout()
        vbox.addWidget(self.label1)
        vbox.addWidget(self.label2)
        vbox.addWidget(self.label3)
        vbox.addWidget(self.key_label)
        vbox.addWidget(self.timing_label)
        vbox.addWidget(self.reset_btn)
        self.setLayout(vbox)

        self.pos1 = None
        self.pos2 = None
        self.last_click_time = 0
        self.last_is_first = True
        self.pressed_times = {}  # key: time

        threading.Thread(target=self.mouse_thread, daemon=True).start()
        threading.Thread(target=self.key_thread, daemon=True).start()

    # --- 滑鼠 ---
    def mouse_thread(self):
        with mouse.Listener(on_click=self.on_mouse_click) as listener:
            listener.join()

    def on_mouse_click(self, x, y, button, pressed):
        if pressed and button == mouse.Button.left:
            now = time.time()
            if now - self.last_click_time < 0.35:
                # 這一組雙擊完成：進行第一次or第二次紀錄
                if self.last_is_first:
                    self.pos1 = (x, y)
                    self.pos2 = None
                    self.update_ui("first", x, y)
                    self.last_is_first = False
                else:
                    self.pos2 = (x, y)
                    self.update_ui("second", x, y)
                    self.calc_size()
                    self.last_is_first = True
                self.last_click_time = 0  # reset
            else:
                self.last_click_time = now  # 第一擊
                # 不直接加1：因為雙擊事件要等到第二下才成立

    def update_ui(self, which, x, y):
        if which == "first":
            self.label1.setText(f"第一次雙擊：left={x}, top={y}")
            self.label2.setText("第二次雙擊：尚未記錄")
            self.label3.setText("區域尺寸：尚未計算")
        elif which == "second":
            self.label2.setText(f"第二次雙擊：left={x}, top={y}")

    def calc_size(self):
        if self.pos1 and self.pos2:
            width = abs(self.pos2[0] - self.pos1[0])
            height = abs(self.pos2[1] - self.pos1[1])
            self.label3.setText(f"區域尺寸：width={width}, height={height}")

    # --- 鍵盤 ---
    def key_thread(self):
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()

    def _keyname(self, key):
        if isinstance(key, keyboard.Key):
            if key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
                return 'ctrl'
            if key == keyboard.Key.space:
                return 'space'
            return str(key).replace("Key.", "")
        elif hasattr(key, 'char'):
            return key.char
        else:
            return str(key)

    def on_press(self, key):
        keyname = self._keyname(key)
        if keyname in MONITOR_KEYS and keyname not in self.pressed_times:
            t = time.time()
            self.pressed_times[keyname] = t
            now_str = time.strftime("%H:%M:%S", time.localtime(t))
            self.key_label.setText(f"[{now_str}] 按下 {keyname}")

    def on_release(self, key):
        keyname = self._keyname(key)
        if keyname in MONITOR_KEYS and keyname in self.pressed_times:
            t_release = time.time()
            t_press = self.pressed_times.pop(keyname)
            delta = t_release - t_press
            now_str = time.strftime("%H:%M:%S", time.localtime(t_release))
            self.key_label.setText(f"[{now_str}] 放開 {keyname}")
            self.timing_label.setText(f"{keyname} 按壓時間：{delta:.3f} 秒")

    # --- 重置 ---
    def reset_all(self):
        self.pos1 = None
        self.pos2 = None
        self.last_is_first = True
        self.label1.setText("第一次雙擊：尚未記錄")
        self.label2.setText("第二次雙擊：尚未記錄")
        self.label3.setText("區域尺寸：尚未計算")
        self.key_label.setText("按鍵狀態")
        self.timing_label.setText("")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DoubleClickRecorder()
    win.show()
    sys.exit(app.exec_())
