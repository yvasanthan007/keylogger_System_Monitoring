import pyautogui, os
from datetime import datetime

def capture_screenshot():
    try:
        os.makedirs("data/screenshots", exist_ok=True)
        filename = datetime.now().strftime("data/screenshots/%Y%m%d_%H%M%S.png")
        pyautogui.screenshot(filename)
        return filename
    except Exception as e:
        return f"Error: {e}"