import pyautogui
import random
import time
import mss
import threading
import requests
import queue
import os
import re
import sys
from pynput import keyboard
from rapidocr import RapidOCR
from PIL import Image

# ===== NB/PC 圖片路徑與 webhook 切換 =====
PATH_NB = "target/nb"
PATH_PC = "target/pc"
PATH_IMG = PATH_NB  # <--- NB or PC，這裡切換

WEBHOOK_NB = 'https://discordapp.com/api/webhooks/1388593414391464006/GWMx8K2fYSCDxl6HUOql9foXFOLDvhy4x2QUdO5OcITtpoAQ8TLV8eMRS8O7Pe_ud-yf'
WEBHOOK_PC = 'https://discord.com/api/webhooks/xxx'
WEBHOOK_URL = WEBHOOK_NB  # <--- NB or PC，這裡切換

DETECT_TARGETS = [
    f"{PATH_IMG}/catalog.png",
    f"{PATH_IMG}/channel.png",
    f"{PATH_IMG}/random_change.png",
    f"{PATH_IMG}/confirm.png",
    f"{PATH_IMG}/login.png",
    f"{PATH_IMG}/choosing.png",
]

# ===== 其餘全域參數區 =====
BOSS_NAME_MAP = {
    '大菇菇': '大菇菇',
    '書生': '書生',
    '樹妖王': '樹妖王',
    '出現': '咕咕鐘',
    '巨大的': '未知Boss',
    '叫聲': '未知Boss',
    '深山': '未知Boss',
    '仙人': '未知Boss',
    '歡樂': '雪毛怪人',
    '狐':   '九尾狐',
    '存在': '巴洛古',
}
KEY_START = 'r'
KEY_EXIT  = 'q'
KEY_PAUSE = 'p'

SEND_CHANNEL_IMAGE = False
SEND_CHANNEL_TEXT = True
AUTO_CONTINUE_AFTER_NOTIFY = False

OCR_BBOX = {'top': 100, 'left': 400, 'width': 1200, 'height': 500}
OCR_QUEUE_SIZE = 10
OCR_INTERVAL = 0.3
OCR_TIMEOUT = 20
SAVE_OCR_IMG = False
OCR_SAVE_DIR = "debug/ocr"

CHANNEL_CAPTURE_DIR = "debug/channel_info"
CHANNEL_CAPTURE_REGION = {'top': 270, 'left': 540, 'width': 160, 'height': 40}

CATALOG_CLICK_DELAY = 0.5
CHANNEL_CLICK_DELAY = 1.2
MOVE_RANDOM_X = (100, 500)
MOVE_RANDOM_Y = (100, 500)
MOVE_TO_DELAY = 0.2
MOVE_CLICK_RANDOM_OFFSET = 5

POST_NOTIFY_WAIT = 3
POST_NOTIFY_KEY = 'esc'

STAGE_TIMEOUT = 60
SLEEP_BEFORE_FIND = 1.0   # 每輪找圖前等待
SLEEP_BEFORE_CLICK = 1.0  # 找到圖後點擊前等待
HUMAN_PRESS_MIN = 0.1     # 最小按壓（秒）
HUMAN_PRESS_MAX = 0.3     # 最大按壓（秒）

TWO_FA_BUG = True
RETRY_LAST_LOC_CLICK = True  # <--- 沒找到圖時是否點擊上一個步驟找到圖的座標，預設開啟

pyautogui.FAILSAFE = False
running = True
paused = False
wait_for_start = False

last_global_loc = None  # 全域記錄最近一次成功找到圖的滑鼠座標

def monitor_keys():
    global running, paused, wait_for_start
    def on_press(key):
        global running, paused, wait_for_start
        try:
            if key.char == KEY_EXIT:
                print(f"偵測到 {KEY_EXIT}，全部腳本結束")
                running = False
                os._exit(0)
            elif key.char == KEY_PAUSE:
                paused = not paused
                if paused:
                    print(f"[PAUSE] 已暫停自動找王，按一次 {KEY_PAUSE} 恢復")
                else:
                    print(f"[RESUME] 已恢復自動找王")
            elif key.char == KEY_START and wait_for_start:
                wait_for_start = False
                print(f"[RESUME] 收到 {KEY_START}，繼續下一輪找王")
        except AttributeError:
            pass
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

def wait_start_key():
    print(f"請按 {KEY_START} 開始自動找王")
    COMBO = {keyboard.KeyCode.from_char(KEY_START)}
    current_keys = set()
    def on_press(key):
        current_keys.add(key)
        if COMBO.issubset(current_keys):
            return False
    def on_release(key):
        try:
            current_keys.remove(key)
        except KeyError:
            pass
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

def wait_for_start_key():
    global wait_for_start
    wait_for_start = True
    print(f"[WAIT] 找到王，等待你按下 {KEY_START} 以繼續 ...")
    while wait_for_start and running:
        time.sleep(0.1)

def safe_locate(path, confidence=0.8):
    try:
        return pyautogui.locateOnScreen(path, confidence=confidence)
    except pyautogui.ImageNotFoundException:
        return None
    except Exception as e:
        print(f"[ERROR] {path} 找圖時異常: {e}")
        return None

def human_click(x, y):
    # numpy int -> python int
    x = int(x)
    y = int(y)
    pyautogui.moveTo(x, y, random.uniform(0.15, 0.3), pyautogui.easeInElastic)
    pyautogui.mouseDown()
    time.sleep(random.uniform(HUMAN_PRESS_MIN, HUMAN_PRESS_MAX))
    pyautogui.mouseUp()

def patch_2fa_reload():
    for action_img in ["menu.png", "reload.png", "yes.png"]:
        img_path = f"{PATH_IMG}/{action_img}"
        print(f"[2FA BUG] 點擊 {action_img}")
        location = None
        for _ in range(10):
            if not running:
                return
            location = safe_locate(img_path, confidence=0.8)
            if location:
                x, y = pyautogui.center(location)
                human_click(x, y)
                time.sleep(0.5)
                break
            time.sleep(0.5)
        if not location:
            print(f"[2FA BUG] {action_img} 找不到，跳過此步")

def find_and_click_with_retry(img_path, stage_name, timeout, is_login=False):
    global last_global_loc, running, paused
    t0 = time.time()
    retry = 0
    fa2_count = 0
    last_loc = None
    while running:
        if paused:
            print(f"[PAUSE] 已暫停在 {stage_name}，等待恢復 ...")
            while paused and running:
                time.sleep(0.3)
            # 恢復後繼續 while，不reset timer
        if time.time() - t0 > timeout:
            print(f"[TIMEOUT] {stage_name} 階段等待超過 {timeout} 秒，結束程式！")
            os._exit(1)
        time.sleep(SLEEP_BEFORE_FIND)
        if not running:
            break
        if is_login and TWO_FA_BUG:
            fa2_path = f"{PATH_IMG}/2fa.png"
            fa2_loc = safe_locate(fa2_path, confidence=0.8)
            if fa2_loc:
                print(f"[{stage_name}] 發現2fa.png，執行2FA補丁（login重試計數歸零）")
                patch_2fa_reload()
                fa2_count += 1
                t0 = time.time()
                retry = 0
                last_loc = None
                continue
        loc = safe_locate(img_path, confidence=0.8)
        if loc:
            print(f"[{stage_name}] 找到 {img_path}，第{retry+1}次嘗試")
            time.sleep(SLEEP_BEFORE_CLICK)
            x, y = pyautogui.center(loc)
            human_click(x, y)
            time.sleep(1.0)
            last_global_loc = (x, y)
            last_loc = (x, y)
            return True, retry, fa2_count
        else:
            retry += 1
            if RETRY_LAST_LOC_CLICK and last_global_loc is not None:
                print(f"[{stage_name}] 沒找到 {img_path}，重試第{retry}次，點擊上個成功座標 {last_global_loc}")
                x, y = last_global_loc
                human_click(x, y)
                time.sleep(0.5)
            else:
                print(f"[{stage_name}] 沒找到 {img_path}，重試第{retry}次，無可點擊座標略過")
        if loc:
            last_loc = pyautogui.center(loc)
    return False, retry, fa2_count

def auto_finder():
    global running, paused
    switch_count = 0
    fa2_total = 0
    while running:
        if paused:
            print(f"[PAUSE] 自動找王已暫停，等待恢復 ...")
        while paused and running:
            time.sleep(0.3)
        fa2_round = 0
        for target in DETECT_TARGETS:
            if not running:
                return
            if paused: break
            step = target.split('/')[-1].replace('.png', '').upper()
            if "login.png" in target:
                result, retry, fa2_count = find_and_click_with_retry(target, "LOGIN", STAGE_TIMEOUT, is_login=True)
                fa2_round = fa2_count
                fa2_total += fa2_count
                continue
            result, retry, _ = find_and_click_with_retry(target, step, STAGE_TIMEOUT, is_login=False)
            if "random_change.png" in target:
                switch_count += 1
        boss_name = confirm_boss()
        if boss_name:
            channel_text = capture_and_send_channel_info(boss_name)
            if SEND_CHANNEL_TEXT:
                msg = f"頻道{channel_text} 找到 {boss_name}！"
                send_discord_text(msg)
            post_notify_action()
            print(f"\n[統計] 這次換了 {switch_count} 次頻道（不含2FA）。")
            if fa2_round > 0:
                print(f"[統計] 這輪遇到 2FA BUG 補丁 {fa2_round} 次，總累積 {fa2_total} 次。")
            if not AUTO_CONTINUE_AFTER_NOTIFY:
                wait_for_start_key()
            switch_count = 0
            fa2_round = 0

def send_discord_image(img_path, msg="頻道資訊截圖"):
    with open(img_path, "rb") as f:
        files = {"file": f}
        data = {"content": msg}
        resp = requests.post(WEBHOOK_URL, data=data, files=files)
        if resp.ok:
            print("[INFO] 頻道截圖已發送至 Discord")
        else:
            print("[WARN] 頻道截圖發送失敗", resp.text)

def send_discord_text(msg):
    data = {"content": msg, "username": "通知機器人"}
    resp = requests.post(WEBHOOK_URL, json=data)
    if resp.ok:
        print(f"[INFO] Discord已發送：{msg}")
    else:
        print("[WARN] Discord發送失敗", resp.text)

def ocr_channel_img(img):
    ocr_engine = RapidOCR()
    result = ocr_engine(img)
    if result.txts and len(result.txts) > 0:
        for txt in result.txts:
            match = re.search(r"\d+", txt)
            if match:
                return match.group(0)
        return result.txts[0]
    else:
        return "?"

def capture_and_send_channel_info(boss_name):
    find_and_click_with_retry(f"{PATH_IMG}/catalog.png", "CATALOG", STAGE_TIMEOUT)
    time.sleep(CATALOG_CLICK_DELAY)
    find_and_click_with_retry(f"{PATH_IMG}/channel.png", "CHANNEL", STAGE_TIMEOUT)
    time.sleep(CHANNEL_CLICK_DELAY)
    os.makedirs(CHANNEL_CAPTURE_DIR, exist_ok=True)
    fname = f"{CHANNEL_CAPTURE_DIR}/channel_{int(time.time()*1000)}.png"
    with mss.mss() as sct:
        region = CHANNEL_CAPTURE_REGION
        shot = sct.grab(region)
        img = Image.frombytes('RGB', shot.size, shot.rgb)
        img.save(fname)
    print(f"[INFO] 頻道資訊截圖存檔：{fname}")

    channel_text = ocr_channel_img(img)
    if SEND_CHANNEL_IMAGE:
        send_discord_image(fname, msg=f"頻道{channel_text} 找到 {boss_name}！（附圖）")
    return channel_text

def post_notify_action():
    print(f"[INFO] 發送通知後等待 {POST_NOTIFY_WAIT} 秒，準備自動按下 {POST_NOTIFY_KEY.upper()} 鍵")
    time.sleep(POST_NOTIFY_WAIT)
    pyautogui.press(POST_NOTIFY_KEY)
    print(f"[INFO] 已自動按下 {POST_NOTIFY_KEY.upper()}")

def confirm_boss(timeout_seconds=OCR_TIMEOUT):
    queue_size = OCR_QUEUE_SIZE
    img_queue = queue.Queue(maxsize=queue_size)
    ocr_engine = RapidOCR()
    stats = {'count': 0}
    found_event = threading.Event()
    bbox = OCR_BBOX.copy()
    found_boss_name = [None]
    def capture_loop():
        with mss.mss() as sct:
            while not found_event.is_set() and stats['count'] < queue_size:
                start = time.time()
                shot = sct.grab(bbox)
                img = Image.frombytes('RGB', shot.size, shot.rgb)
                if SAVE_OCR_IMG:
                    os.makedirs(OCR_SAVE_DIR, exist_ok=True)
                    fname = f"{OCR_SAVE_DIR}/ocr_{int(time.time()*1000)}.png"
                    img.save(fname)
                try:
                    img_queue.put(img, timeout=1)
                except queue.Full:
                    print("Queue 已滿，丟棄此張圖片")
                elapsed = time.time() - start
                time.sleep(max(0, OCR_INTERVAL - elapsed))
                print(time.time(), '截圖')
                stats['count'] += 1
        img_queue.put(None)
    def ocr_loop():
        while True:
            item = img_queue.get()
            if item is None:
                break
            results = ocr_engine(item)
            if results.txts:
                for txt in results.txts:
                    for phrase, boss_name in BOSS_NAME_MAP.items():
                        if phrase in txt:
                            found_boss_name[0] = boss_name
                            found_event.set()
                            print(f"{time.strftime('%H:%M:%S')} 找到王[{boss_name}]：{txt}")
                            img_queue.task_done()
                            return
            img_queue.task_done()
            print(time.strftime('%H:%M:%S'), 'OCR處理完成')
    t1 = threading.Thread(target=capture_loop, daemon=True)
    t2 = threading.Thread(target=ocr_loop, daemon=True)
    t1.start()
    t2.start()
    finished = found_event.wait(timeout=timeout_seconds)
    if finished:
        return found_boss_name[0]
    else:
        return None

if __name__ == '__main__':
    wait_start_key()
    monitor_keys()
    auto_finder()
    print("程式結束")
