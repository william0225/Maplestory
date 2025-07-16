import sys, os, time, threading, random, re
import mss
from PIL import Image
import cv2
import numpy as np
import pytesseract
import pyautogui
from pynput import keyboard

# 動態匯入上層 lib
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib')))
import autobuff

# ========== 模式選擇 ==========
MODE = "all"   # all=補血/移動/buff全功能，buff=只自動buff

# ========== 參數區 ==========
REGION_HP = {'top': 1060, 'left': 560, 'width': 92, 'height': 24}
OCR_INTERVAL = 0.1
IDLE_TIME = 10.0
GUARD_TIME = 2.0

HEAL_KEY = 'ctrl'
HEAL_KEY_HOLD_MIN = 3.0
HEAL_KEY_HOLD_MAX = 5.0
HEAL_MOVE_CHANCE = 0.3
MOVE_LEFT_KEY = "left"
MOVE_RIGHT_KEY = "right"
JUMP_KEY = "space"

# ========== 日志設定 ==========
LOG_DIR = os.path.join(os.path.dirname(__file__), 'debug')
LOG_FILE = os.path.join(LOG_DIR, 'log.txt')
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)
os.makedirs(LOG_DIR, exist_ok=True)
def log_mon(msg):
    ts = time.strftime('[%Y-%m-%d %H:%M:%S]')
    line = f"{ts} [monk] {msg}"
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')

# ========== 全域狀態 ==========
NEED_HEAL = False
CUR_HP = None
MAX_HP = None
running = True
paused = False
started = False

def nowstr():
    return time.strftime('[%Y-%m-%d %H:%M:%S]')

def extract_hp(text):
    m = re.search(r'(\d+)\s*/\s*(\d+)', text)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None

def pre_process(img_pil):
    arr = np.array(img_pil)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, (gray.shape[1]*3, gray.shape[0]*3), interpolation=cv2.INTER_CUBIC)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th

def monitor_keys():
    global running, started, paused
    def on_press(key):
        global running, started, paused
        try:
            if key.char == 'q':
                log_mon("偵測到 q，程式結束")
                running = False
                return False
            elif key.char == 'r' and not started:
                log_mon("偵測到 r，開始")
                started = True
            elif key.char == 'p':
                paused = not paused
                log_mon("已暫停" if paused else "已恢復")
        except:
            pass
    log_mon("啟動鍵盤監聽")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

def ocr_hp():
    with mss.mss() as sct:
        shot = sct.grab(REGION_HP)
        img = Image.frombytes('RGB', shot.size, shot.rgb)
    proc = pre_process(img)
    cfg = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789/'
    txt = pytesseract.image_to_string(proc, config=cfg).strip()
    hp, mh = extract_hp(txt)
    return hp, mh, txt

def ocr_monitor():
    global NEED_HEAL, CUR_HP, MAX_HP, running
    log_mon("啟動 OCR 監測")
    last_hit = None
    while running:
        hp, mh, txt = ocr_hp()
        CUR_HP, MAX_HP = hp, mh
        if hp is not None:
            if hp < mh:
                NEED_HEAL = True
                last_hit = time.time()
                log_mon(f"OCR='{hp}/{mh}' => NEED_HEAL=True")
            else:
                if last_hit and time.time() - last_hit > IDLE_TIME:
                    NEED_HEAL = False
                log_mon(f"OCR='{hp}/{mh}' => NEED_HEAL={NEED_HEAL}")
        else:
            log_mon(f"OCR失敗 txt='{txt}'")
        time.sleep(OCR_INTERVAL)

def heal_action():
    log_mon(f"[HEAL] 長按 {HEAL_KEY}")
    pyautogui.keyDown(HEAL_KEY)
    hold = random.uniform(HEAL_KEY_HOLD_MIN, HEAL_KEY_HOLD_MAX)
    time.sleep(hold)
    pyautogui.keyUp(HEAL_KEY)
    log_mon(f"[HEAL] 補血持續 {hold:.2f}s")
    if random.random() < HEAL_MOVE_CHANCE:
        d = random.uniform(0.1, 0.2)
        time.sleep(d)
        mk = random.choice([MOVE_LEFT_KEY, MOVE_RIGHT_KEY])
        pyautogui.keyDown(mk); pyautogui.keyDown(JUMP_KEY)
        time.sleep(random.uniform(0.05,0.1))
        pyautogui.keyUp(mk); pyautogui.keyUp(JUMP_KEY)
        log_mon(f"[HEAL] 瞬移 {mk}+{JUMP_KEY}")

def main_behavior():
    global running, paused, NEED_HEAL
    log_mon("等待 r 開始")
    while running and not started:
        time.sleep(0.05)
    log_mon("進入主迴圈")
    in_guard = False

    while running:
        if paused:
            time.sleep(0.1)
            continue
        if NEED_HEAL:
            log_mon("被打，立即補血")
            while NEED_HEAL and running:
                heal_action()
                time.sleep(0.02)
            log_mon("補血結束，進入警戒")
            in_guard = True
            continue
        if in_guard:
            log_mon(f"[GUARD] 警戒 {GUARD_TIME}s")
            t0 = time.time()
            while time.time() - t0 < GUARD_TIME and running:
                if NEED_HEAL:
                    log_mon("警戒期間被打，恢復補血")
                    break
                time.sleep(0.05)
            else:
                log_mon("警戒結束，進入 idle")
                autobuff_only = False
            in_guard = False
            continue
        # idle 模式
        log_mon("idle 模式，嘗試 Buff/移動")
        res = autobuff.check_and_buff(lambda: NEED_HEAL, None)
        if res is False:
            log_mon("Buff 被打斷，回補血")
            continue
        # 若沒有 buff，或 buff 過後再進行簡易移動
        mk = random.choice([MOVE_LEFT_KEY, MOVE_RIGHT_KEY])
        hold = random.uniform(0.1, 0.2)
        pyautogui.keyDown(mk); time.sleep(hold); pyautogui.keyUp(mk)
        log_mon(f"[IDLE-MOVE] {mk} hold {hold:.2f}s")
        time.sleep(random.uniform(0.5, 1.0))

def autobuff_only():
    global running, started
    interval = autobuff.BUFF_INTERVAL_SEC
    log_mon("只執行 autobuff 模式")
    while running and not started:
        time.sleep(0.05)
    last = 0
    while running:
        now = time.time()
        if now - last >= interval:
            autobuff.do_buff()
            autobuff.buff_move_preset()
            last = now
        time.sleep(0.1)

if __name__ == "__main__":
    threading.Thread(target=monitor_keys, daemon=True).start()
    if MODE == "all":
        threading.Thread(target=ocr_monitor, daemon=True).start()
        main_behavior()
    else:
        autobuff_only()
