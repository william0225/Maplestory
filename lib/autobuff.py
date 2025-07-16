# lib/autobuff.py
import pyautogui
import time
import random
import threading

# ===== 全域 Buff 參數 =====
BUFF_KEYS = ['1', '2']
BUFF_INTERVAL_SEC = 270       # 整體 Buff 輪迴間隔
KEY_HOLD_BASE = 0.13
KEY_PRESS_DELAY = (0.06, 0.15)
KEY_ACTION_GAP = (0.7, 1.7)

# ===== buff-only 模式下 preset 移動 =====
BUFF_MOVE_LEFT_KEY = 'left'
BUFF_MOVE_RIGHT_KEY = 'right'
BUFF_MOVE_LEFT_TIMES = 2
BUFF_MOVE_RIGHT_TIMES = 2
BUFF_MOVE_HOLD_MIN = 0.12
BUFF_MOVE_HOLD_MAX = 0.23
BUFF_MOVE_GAP_MIN = 0.09
BUFF_MOVE_GAP_MAX = 0.17

# 內部狀態
_last_buff_time = 0.0
_buff_index = 0
_lock = threading.Lock()

def nowstr():
    return time.strftime("[%Y-%m-%d %H:%M:%S]")

def do_buff(should_interrupt=None):
    """
    放完整組 Buff，可被中斷。
    支援半組 buff 恢復續放。
    """
    global _last_buff_time, _buff_index
    with _lock:
        start_idx = _buff_index
        # 若間隔已到或是新一輪，重設 start_idx
        if time.time() - _last_buff_time >= BUFF_INTERVAL_SEC:
            start_idx = 0
        print(f"{nowstr()} [autobuff] 開始 Buff (從 idx={start_idx})")
        for idx in range(start_idx, len(BUFF_KEYS)):
            key = BUFF_KEYS[idx]
            # 中途可被打斷
            if should_interrupt and should_interrupt():
                print(f"{nowstr()} [autobuff] Buff 被中斷 at idx={idx}")
                return False
            # 按鍵前隨機延遲
            d = random.uniform(*KEY_PRESS_DELAY)
            time.sleep(d)
            pyautogui.keyDown(key)
            # 按下持續
            hold = KEY_HOLD_BASE + random.uniform(-0.03, 0.04)
            time.sleep(hold)
            pyautogui.keyUp(key)
            print(f"{nowstr()} [autobuff] Buff [{key}] 按壓 {hold:.2f}s")
            # 更新進度與時間
            _buff_index = idx + 1
            _last_buff_time = time.time()
            # 若非最後一招，間隔
            if idx < len(BUFF_KEYS) - 1:
                gap = random.uniform(*KEY_ACTION_GAP)
                time.sleep(gap)
                print(f"{nowstr()} [autobuff] Buff 間隔 {gap:.2f}s")
        # 一輪完成
        print(f"{nowstr()} [autobuff] Buff 一輪完成")
        _buff_index = 0
        _last_buff_time = time.time()
        return True

def buff_move_preset():
    """
    buff-only 模式下，固定 左x次 後 右x次 的移動
    """
    print(f"{nowstr()} [autobuff] preset 移動 開始")
    for i in range(BUFF_MOVE_LEFT_TIMES):
        hold = random.uniform(BUFF_MOVE_HOLD_MIN, BUFF_MOVE_HOLD_MAX)
        pyautogui.keyDown(BUFF_MOVE_LEFT_KEY)
        time.sleep(hold)
        pyautogui.keyUp(BUFF_MOVE_LEFT_KEY)
        print(f"{nowstr()} [autobuff] 左移 {i+1}/{BUFF_MOVE_LEFT_TIMES} hold {hold:.2f}s")
        time.sleep(random.uniform(BUFF_MOVE_GAP_MIN, BUFF_MOVE_GAP_MAX))
    for i in range(BUFF_MOVE_RIGHT_TIMES):
        hold = random.uniform(BUFF_MOVE_HOLD_MIN, BUFF_MOVE_HOLD_MAX)
        pyautogui.keyDown(BUFF_MOVE_RIGHT_KEY)
        time.sleep(hold)
        pyautogui.keyUp(BUFF_MOVE_RIGHT_KEY)
        print(f"{nowstr()} [autobuff] 右移 {i+1}/{BUFF_MOVE_RIGHT_TIMES} hold {hold:.2f}s")
        time.sleep(random.uniform(BUFF_MOVE_GAP_MIN, BUFF_MOVE_GAP_MAX))

def check_and_buff(should_interrupt=None):
    """
    Idle 模式呼叫此函式：
      - 若當前有未完成的半組 buff，立即續放
      - 否則若已超過 BUFF_INTERVAL_SEC，啟動新一輪 buff
      - 回傳 True=已放完、False=被打斷、None=尚未到時間
    """
    global _last_buff_time, _buff_index
    # 若半組未完成
    if _buff_index > 0:
        return do_buff(should_interrupt)
    # 若輪迴到時間
    if time.time() - _last_buff_time >= BUFF_INTERVAL_SEC:
        return do_buff(should_interrupt)
    return None
