import os
from collections import Counter
from keylogger import get_keys_per_second

def get_key_stats():
    log_file = "data/logs/keystrokes.txt"
    stats = {"total_keys": 0, "most_common": "None"}

    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            data = f.read()
            printable = [c for c in data if c.isprintable() or c in '\n \t']
            stats["total_keys"] = len(printable)
            if printable:
                common = Counter(printable).most_common(1)
                stats["most_common"] = common[0][0] if common else "None"
    return stats

def get_activity_series():
    return get_keys_per_second()