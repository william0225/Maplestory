import pyautogui
import threading
import time
import random

BUFF_KEYS = ['1', '2']
BUFF_HOLD_TIME = 0.13
BUFF_INTERVAL_SEC = 270
BUFF_RANDOM_DELAY = (1, 5)
KEY_PRESS_DELAY = (0.1, 0.3)
KEY_ACTION_GAP = (1, 3)

_last_buff_time = 0
_buff_lock = threading.Lock()

def nowstr():
    return time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())

def do_buff(should_interrupt=None):
    """
    施放全套 buff，支援隨時被打斷
    should_interrupt: 可傳入 lambda 或 function，每次施放前呼叫，回傳 True 則立即中止
    """
    global _last_buff_time
    with _buff_lock:
        print(f"{nowstr()} [AutoBuff] 執行 Buff 技能")
        for idx, key_name in enumerate(BUFF_KEYS):
            if should_interrupt and should_interrupt():
                print(f"{nowstr()} [AutoBuff] Buff 被中斷！")
                return False  # 被打斷
            key_delay = random.uniform(*KEY_PRESS_DELAY)
            time.sleep(key_delay)
            pyautogui.keyDown(key_name)
            time.sleep(BUFF_HOLD_TIME)
            pyautogui.keyUp(key_name)
            print(f"  Buff [{key_name}] 按壓 {BUFF_HOLD_TIME:.2f} 秒")
            if idx != len(BUFF_KEYS) - 1:
                gap = random.uniform(*KEY_ACTION_GAP)
                print(f"    Buff間隔 {gap:.2f} 秒")
                time.sleep(gap)
        _last_buff_time = time.time()
        print(f"{nowstr()} [AutoBuff] Buff 技能完成")
        return True  # 完成未被中斷

def check_and_buff(should_interrupt=None):
    """
    判斷是否該 Buff，到了時間自動施放，施放過程可被中斷（傳入 should_interrupt 函式）
    回傳 True: Buff 已完整執行
    回傳 False: Buff 被中斷（主程式應立即進補血）
    回傳 None: 不需 Buff
    """
    global _last_buff_time
    now = time.time()
    if now - _last_buff_time >= BUFF_INTERVAL_SEC:
        return do_buff(should_interrupt)
    return None  # 不需 Buff

# -- 兼容舊的循環 buff main（不影響之前 main.py 的用法）--
running = True
started = False

def monitor_keys():
    global running, started
    def on_press(key):
        global running, started
        try:
            if key.char == 'q':
                print("[AutoBuff] 偵測到 q，程式結束")
                running = False
                return False
            elif key.char == 'r' and not started:
                print("[AutoBuff] 偵測到 r，開始自動 Buff")
                started = True
        except AttributeError:
            pass
    from pynput import keyboard
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

def run_autobuff(running_flag, started_flag, lock):
    round_count = 0
    print("等待你按下 r 開始自動 Buff (按 q 可隨時結束)...")
    while running_flag[0] and not started_flag[0]:
        time.sleep(0.1)
    if running_flag[0] and started_flag[0]:
        while running_flag[0]:
            with lock:
                round_count += 1
                print(f"\n========== AutoBuff 第 {round_count} 輪 ==========")
                do_buff()
                time.sleep(3)
            delay = BUFF_INTERVAL_SEC + random.uniform(*BUFF_RANDOM_DELAY)
            print(f"[AutoBuff] 下次預計 {delay:.1f} 秒後")
            time.sleep(delay)
    print("\n[AutoBuff] 結束")

if __name__ == '__main__':
    threading.Thread(target=monitor_keys, daemon=True).start()
    running_flag = [True]
    started_flag = [False]
    lock = threading.Lock()
    run_autobuff(running_flag, started_flag, lock)
