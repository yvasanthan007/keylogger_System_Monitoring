import os, shutil

def sync_to_cloud():
    try:
        cloud_dir = "data/cloud"
        os.makedirs(cloud_dir, exist_ok=True)
        shutil.copy("data/logs/keystrokes.txt", cloud_dir)
        return "Synced to cloud (local mock)"
    except Exception as e:
        return f"Error: {e}"