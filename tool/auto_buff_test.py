import pyautogui
import threading
import time
import random
from pynput import keyboard

buff_actions = [
    ('1', 0.13),
    ('2', 0.13),
]
buff_main_interval = 270
buff_random_delay = (1, 5)
buff_keypress_delay = (0.1, 0.3)
buff_action_gap = (1, 3)  # Buff動作之間的間隔（秒）
running = True
started = False

def monitor_keys():
    def on_press(key):
        global running, started  # ← 關鍵修正
        try:
            if key.char == 'q':
                print("偵測到 q，程式即將停止。")
                running = False
                return False
            elif key.char == 'r' and not started:
                print("偵測到 r，AutoBuff 循環開始！")
                started = True
        except AttributeError:
            pass
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

def press_key(key_name, hold_time):
    pyautogui.keyDown(key_name)
    time.sleep(hold_time)
    pyautogui.keyUp(key_name)
    print(f"  Buff [{key_name}] 按壓 {hold_time:.2f} 秒")

def do_buff():
    print(f"\n[AutoBuff] 開始放 Buff 技能")
    total = len(buff_actions)
    for idx, (key_name, hold_time) in enumerate(buff_actions):
        if not running: break
        key_delay = random.uniform(*buff_keypress_delay)
        print(f"    等待 {int(key_delay*1000)} ms 再按 [{key_name}]")
        time.sleep(key_delay)
        press_key(key_name, hold_time)
        # 除了最後一個之外，每個Buff之後都要多等 1~3秒
        if idx != total - 1:
            gap = random.uniform(*buff_action_gap)
            print(f"    Buff間隔 {gap:.2f} 秒")
            time.sleep(gap)
    print("[AutoBuff] 本輪 Buff 技能完成")

if __name__ == '__main__':
    threading.Thread(target=monitor_keys, daemon=True).start()
    round_count = 0

    print("等待你按下 r 開始自動 Buff (按 q 可隨時結束)...")
    while running and not started:
        time.sleep(0.1)

    if running and started:
        round_count += 1
        print(f"\n========== AutoBuff 第 {round_count} 輪 (首次 Buff) ==========")
        do_buff()
        next_buff_time = time.time() + buff_main_interval + random.uniform(*buff_random_delay)
        print(f"[AutoBuff] 下次預計 {next_buff_time - time.time():.1f} 秒後（{time.strftime('%H:%M:%S', time.localtime(next_buff_time))}）")

        while running:
            now = time.time()
            if now >= next_buff_time:
                round_count += 1
                print(f"\n========== AutoBuff 第 {round_count} 輪 ==========")
                do_buff()
                delay = buff_main_interval + random.uniform(*buff_random_delay)
                next_buff_time = now + delay
                print(f"[AutoBuff] 下次預計 {delay:.1f} 秒後（{time.strftime('%H:%M:%S', time.localtime(next_buff_time))}）")
            time.sleep(0.1)

    print("\n程式結束，歡迎下次使用！")
