import sys
import os
import time
import threading
import mss
from PIL import Image
import cv2
import numpy as np
import pytesseract
import pyautogui
import random
import re
from pynput import keyboard

# 動態匯入上層 lib
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib')))
import autobuff

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ====== 全域參數 ======
REGION_HP = {'top': 1070, 'left': 508, 'width': 154, 'height': 23}
SAVE_OCR_IMAGE = False
OCR_INTERVAL = 0.2
HEAL_KEY = 'ctrl'
HEAL_KEY_HOLD_MIN = 0.10
HEAL_KEY_HOLD_MAX = 0.20
HEAL_INTERVAL_MIN = 0.10
HEAL_INTERVAL_MAX = 0.20
IDLE_TIME = 5.0
GUARD_TIME = 1.0
HEAL_STOP_WHEN_FULL = False

MOVE_LEFT_KEY = "left"
MOVE_RIGHT_KEY = "right"
IDLE_MOVE_MIN = 0.2
IDLE_MOVE_MAX = 0.4
IDLE_MOVE_INTERVAL_MIN = 0.8
IDLE_MOVE_INTERVAL_MAX = 1.5

running = True
paused = False
started = False

def nowstr():
    return time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())

def extract_hp(text):
    match = re.search(r'HP\[(\d+)\s*/\s*(\d+)\]', text, re.IGNORECASE)
    if not match:
        match = re.search(r'(\d+)\s*/\s*(\d+)', text)
    if match:
        current = int(match.group(1))
        total = int(match.group(2))
        return current, total
    return None, None

def pre_process(pil_img):
    img = np.array(pil_img)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    scale = 3
    gray = cv2.resize(gray, (gray.shape[1]*scale, gray.shape[0]*scale), interpolation=cv2.INTER_CUBIC)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th

def monitor_keys():
    global running, started, paused
    def on_press(key):
        global running, started, paused
        try:
            if key.char == 'q':
                print("[EXIT] 偵測到 q，程式結束")
                running = False
                return False
            elif key.char == 'r' and not started:
                print("[START] 偵測到 r，開始自動補血")
                started = True
            elif key.char == 'p':
                paused = not paused
                if paused:
                    print("[PAUSE] 已暫停，按 p 恢復")
                else:
                    print("[RESUME] 已恢復")
        except AttributeError:
            pass
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

def ocr_hp():
    with mss.mss() as sct:
        shot = sct.grab(REGION_HP)
        img = Image.frombytes('RGB', shot.size, shot.rgb)
    proc = pre_process(img)
    custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=HP0123456789[]/'
    ocr_txt = pytesseract.image_to_string(proc, config=custom_config)
    hp, max_hp = extract_hp(ocr_txt)
    return hp, max_hp

def heal_action():
    hold_time = random.uniform(HEAL_KEY_HOLD_MIN, HEAL_KEY_HOLD_MAX)
    pyautogui.keyDown(HEAL_KEY)
    time.sleep(hold_time)
    pyautogui.keyUp(HEAL_KEY)
    print(f"{nowstr()} [HEAL] 按下 {HEAL_KEY}，hold {hold_time:.2f}s")

def idle_move_action(should_interrupt):
    key = random.choice([MOVE_LEFT_KEY, MOVE_RIGHT_KEY])
    hold_time = random.uniform(IDLE_MOVE_MIN, IDLE_MOVE_MAX)
    pyautogui.keyDown(key)
    t_start = time.time()
    while time.time() - t_start < hold_time:
        if should_interrupt():
            pyautogui.keyUp(key)
            print(f"{nowstr()} [IDLE-MOVE] 移動中被扣血，恢復補血")
            return False
        time.sleep(0.1)
    pyautogui.keyUp(key)
    print(f"{nowstr()} [IDLE-MOVE] 移動 {key}，hold {hold_time:.2f}s")
    return True

def should_interrupt():
    hp, max_hp = ocr_hp()
    return hp is not None and max_hp is not None and hp < max_hp

def main_loop():
    global running, started, paused
    print("等待 r 開始，q 結束，p 暫停/繼續")
    while running and not started:
        time.sleep(0.2)

    last_damage_time = None
    in_heal_mode = False
    in_guard_mode = False
    in_idle_mode = False

    while running:
        if paused:
            time.sleep(0.2)
            continue

        hp, max_hp = ocr_hp()
        now = time.time()
        if hp is not None and max_hp is not None:
            print(f"{nowstr()} 偵測血量：{hp}/{max_hp}")
            # 一但被扣血就進補血
            if hp < max_hp:
                if not in_heal_mode:
                    print(f"{nowstr()} [INFO] 偵測到被扣血，開始自動補血")
                    in_heal_mode = True
                    in_guard_mode = False
                    in_idle_mode = False
                last_damage_time = now

            if in_heal_mode:
                heal_action()
                time.sleep(random.uniform(HEAL_INTERVAL_MIN, HEAL_INTERVAL_MAX))
                if last_damage_time is not None and (now - last_damage_time) >= IDLE_TIME:
                    print(f"{nowstr()} [GUARD] 進入警戒模式 {GUARD_TIME}秒")
                    in_heal_mode = False
                    in_guard_mode = True
                    guard_start_time = time.time()
            elif in_guard_mode:
                guard_ok = True
                while time.time() - guard_start_time < GUARD_TIME and running:
                    if should_interrupt():
                        in_heal_mode = True
                        in_guard_mode = False
                        in_idle_mode = False
                        last_damage_time = time.time()
                        print(f"{nowstr()} [GUARD] 警戒期間被扣血，恢復補血")
                        guard_ok = False
                        break
                    time.sleep(OCR_INTERVAL)
                if guard_ok:
                    print(f"{nowstr()} [IDLE] 警戒結束，進入空閒")
                    in_guard_mode = False
                    in_idle_mode = True
            elif in_idle_mode:
                # idle時，優先buff，buff時可被中斷
                buff_result = autobuff.check_and_buff(should_interrupt=should_interrupt)
                if buff_result is False:
                    print(f"{nowstr()} [IDLE] Buff被打斷，立即進補血")
                    in_idle_mode = False
                    in_heal_mode = True
                    last_damage_time = time.time()
                    continue
                elif buff_result is True:
                    t0 = time.time()
                    while time.time() - t0 < 2.0:
                        if should_interrupt():
                            print(f"{nowstr()} [IDLE] Buff結束後馬上被扣血，立即進補血")
                            in_idle_mode = False
                            in_heal_mode = True
                            last_damage_time = time.time()
                            break
                        time.sleep(0.1)
                    continue
                # buff未到，執行移動，移動時隨時能中斷
                move_ok = idle_move_action(should_interrupt)
                if not move_ok:
                    in_idle_mode = False
                    in_heal_mode = True
                    last_damage_time = time.time()
                    continue
                interval = random.uniform(IDLE_MOVE_INTERVAL_MIN, IDLE_MOVE_INTERVAL_MAX)
                print(f"{nowstr()} [IDLE-MOVE] 等待 {interval:.2f}s 再移動")
                t1 = time.time()
                while time.time() - t1 < interval and running:
                    if should_interrupt():
                        print(f"{nowstr()} [IDLE-MOVE] 間隔中被扣血，恢復補血")
                        in_idle_mode = False
                        in_heal_mode = True
                        last_damage_time = time.time()
                        break
                    time.sleep(0.1)
            else:
                time.sleep(OCR_INTERVAL)
        else:
            print(f"{nowstr()} [WARN] 血量辨識失敗")
            time.sleep(OCR_INTERVAL)

if __name__ == "__main__":
    threading.Thread(target=monitor_keys, daemon=True).start()
    main_loop()
