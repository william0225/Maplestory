import pyautogui
import random
import time
import mss
import threading
import requests
import queue
import os
import re
from pynput import keyboard
from rapidocr import RapidOCR
from PIL import Image

# ===== NB/PC 圖片路徑與 webhook 切換 =====
PATH_NB = "target/nb"
PATH_PC = "target/pc"
PATH_IMG = PATH_NB  # <--- NB or PC，這裡切換

WEBHOOK_NB = 'https://discordapp.com/api/webhooks/1388593414391464006/GWMx8K2fYSCDxl6HUOql9foXFOLDvhy4x2QUdO5OcITtpoAQ8TLV8eMRS8O7Pe_ud-yf'
WEBHOOK_PC = 'https://discordapp.com/api/webhooks/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
WEBHOOK_URL = WEBHOOK_NB  # <--- NB or PC，這裡切換

# 所有圖片檔都拼在 PATH_IMG 下面
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
    '歡樂': '未知Boss',
    # ...可持續擴充
}
KEY_START = 'r'   # 啟動/續行
KEY_EXIT  = 'q'   # 結束
KEY_PAUSE = 'p'   # 暫停/恢復

SEND_CHANNEL_IMAGE = True
SEND_CHANNEL_TEXT = True
AUTO_CONTINUE_AFTER_NOTIFY = True

OCR_BBOX = {'top': 100, 'left': 400, 'width': 1200, 'height': 500}
OCR_QUEUE_SIZE = 10
OCR_INTERVAL = 0.3
OCR_TIMEOUT = 20
SAVE_OCR_IMG = True
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

pyautogui.FAILSAFE = False
running = True
paused = False
wait_for_start = False

def monitor_keys():
    global running, paused, wait_for_start
    def on_press(key):
        global running, paused, wait_for_start
        try:
            if key.char == KEY_EXIT:
                print(f"偵測到 {KEY_EXIT}，全部腳本結束")
                running = False
                return False
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
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

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

def detect_and_click(png, speed=None):
    global running
    if speed is None:
        speed = random.uniform(0.3, 0.5)
    pyautogui.moveTo(
        random.randint(MOVE_RANDOM_X[0], MOVE_RANDOM_X[1]),
        random.randint(MOVE_RANDOM_Y[0], MOVE_RANDOM_Y[1]),
        MOVE_TO_DELAY,
        pyautogui.easeOutQuad
    )
    print('尋找圖片:', png)
    start_time = time.time()
    while running:
        try:
            location = pyautogui.locateOnScreen(png, confidence=0.8)
        except Exception as e:
            print(f"找圖時異常: {e}")
            location = None
        if location is not None:
            break
        else:
            if 'timeout' in png:
                return
            time.sleep(1)
            now = time.time()
            if now - start_time > 1:
                if 'confirm' in png:
                    detect_and_click(f"{PATH_IMG}/confirm_timeout.png")
                elif 'login' in png:
                    detect_and_click(f"{PATH_IMG}/login_timeout.png")
                elif 'choosing' in png:
                    detect_and_click(f"{PATH_IMG}/choosing_timeout.png")
    if location is None:
        print(f"[WARN] {png} 找不到圖，跳過此步驟")
        return
    point = pyautogui.center(location)
    x = int(point.x + random.uniform(-MOVE_CLICK_RANDOM_OFFSET, MOVE_CLICK_RANDOM_OFFSET))
    y = int(point.y + random.uniform(-MOVE_CLICK_RANDOM_OFFSET, MOVE_CLICK_RANDOM_OFFSET))
    pyautogui.moveTo(x, y, speed, pyautogui.easeInElastic)
    if 'login' in png:
        time.sleep(3)
        pyautogui.click()
    time.sleep(random.uniform(0.05, 0.1))
    if 'freemarket' in png or 'login' in png:
        pyautogui.click(clicks=2, interval=0.1)
    else:
        pyautogui.click()
    time.sleep(random.uniform(0.1, 0.2))
    if 'login' in png:
        pyautogui.click()

def auto_finder():
    global running, paused
    while running:
        if paused:
            print(f"[PAUSE] 自動找王已暫停，等待恢復 ...")
        while paused and running:
            time.sleep(0.3)
        for target in DETECT_TARGETS:
            if not running: return
            if paused: break
            detect_and_click(target)
            if not running: return
            if 'choosing' in target:
                boss_name = confirm_boss()
                if boss_name:
                    channel_text = capture_and_send_channel_info(boss_name)
                    if SEND_CHANNEL_TEXT:
                        msg = f"頻道{channel_text} 找到 {boss_name}！"
                        send_discord_text(msg)
                    post_notify_action()
                    if not AUTO_CONTINUE_AFTER_NOTIFY:
                        wait_for_start_key()

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
    detect_and_click(f"{PATH_IMG}/catalog.png")
    time.sleep(CATALOG_CLICK_DELAY)
    detect_and_click(f"{PATH_IMG}/channel.png")
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
    threading.Thread(target=monitor_keys, daemon=True).start()
    auto_finder()
    print("程式結束")
