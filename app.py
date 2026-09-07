import os
import secrets
import time
import smtplib
from email.message import EmailMessage
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

otp_data = {}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_env():
    env = {}
    if os.path.exists(os.path.join(BASE_DIR, ".env")):
        with open(os.path.join(BASE_DIR, ".env")) as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    env[k] = v
    return env

ENV = load_env()

@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/<path:path>")
def files(path):
    return send_from_directory(BASE_DIR, path)

@app.route("/api/send-otp", methods=["POST"])
def send_otp():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()

    admin_email = ENV.get("ADMIN_EMAIL", "").lower()

    if not email or email != admin_email:
        return jsonify({"ok": False, "message": "Invalid recovery email"}), 400

    otp = str(secrets.randbelow(900000) + 100000)

    otp_data[email] = {
        "otp": otp,
        "expires": time.time() + 300
    }

    msg = EmailMessage()
    msg["Subject"] = "SAMUI SEVA SADAN - Admin OTP"
    msg["From"] = ENV.get("MAIL_USERNAME")
    msg["To"] = email
    msg.set_content(
        f"Your SAMUI SEVA SADAN Admin Password Reset OTP is: {otp}\n\n"
        "This OTP is valid for 5 minutes."
    )

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(
                ENV.get("MAIL_USERNAME"),
                ENV.get("MAIL_APP_PASSWORD")
            )
            smtp.send_message(msg)

        return jsonify({"ok": True, "message": "OTP sent to your email"})
    except Exception as e:
        print("MAIL ERROR:", e)
        return jsonify({"ok": False, "message": "Email could not be sent"}), 500

@app.route("/api/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    otp = data.get("otp", "").strip()

    record = otp_data.get(email)

    if not record:
        return jsonify({"ok": False, "message": "OTP not found. Please request a new OTP."}), 400

    if time.time() > record["expires"]:
        otp_data.pop(email, None)
        return jsonify({"ok": False, "message": "OTP expired. Please request a new OTP."}), 400

    if otp != record["otp"]:
        return jsonify({"ok": False, "message": "Invalid OTP."}), 400

    otp_data[email]["verified"] = True

    return jsonify({"ok": True, "message": "OTP verified successfully."})

@app.route("/api/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    new_password = data.get("new_password", "").strip()

    record = otp_data.get(email)

    if not record or not record.get("verified"):
        return jsonify({"ok": False, "message": "Please verify OTP first."}), 400

    if len(new_password) < 6:
        return jsonify({"ok": False, "message": "Password must be at least 6 characters."}), 400

    reset_file = os.path.join(BASE_DIR, ".admin_password")

    with open(reset_file, "w") as f:
        f.write(new_password)

    otp_data.pop(email, None)

    return jsonify({"ok": True, "message": "Password reset successfully."})

@app.route("/api/admin-login", methods=["POST"])
def admin_login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if username != "admin":
        return jsonify({"ok": False, "message": "Invalid Admin Name or Password"}), 401

    password_file = os.path.join(BASE_DIR, ".admin_password")

    if os.path.exists(password_file):
        with open(password_file, "r") as f:
            saved_password = f.read().strip()
    else:
        saved_password = "REMOVED_ADMIN_PASSWORD"

    if password == saved_password:
        return jsonify({"ok": True, "message": "Login successful"})

    return jsonify({"ok": False, "message": "Invalid Admin Name or Password"}), 401

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=False)
