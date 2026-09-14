import os
import secrets
import time
import smtplib
from email.message import EmailMessage
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

@app.after_request
def add_cache_control(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
otp_data = {}

def load_env():
    env = {}
    env_file = os.path.join(BASE_DIR, ".env")

    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()

    env.update(os.environ)
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
    admin_email = ENV.get("ADMIN_EMAIL", "").strip().lower()

    if not email or email != admin_email:
        return jsonify({
            "ok": False,
            "message": "Invalid recovery email"
        }), 400

    smtp_host = ENV.get("SMTP_HOST", "smtp.gmail.com").strip()
    smtp_port = int(ENV.get("SMTP_PORT", "465").strip() or "465")
    smtp_username = ENV.get("MAIL_USERNAME", "").strip()
    smtp_password = ENV.get("MAIL_APP_PASSWORD", "").strip()

    if not smtp_username or not smtp_password:
        return jsonify({
            "ok": False,
            "message": "Email service is not configured"
        }), 500

    otp = str(secrets.randbelow(900000) + 100000)

    otp_data[email] = {
        "otp": otp,
        "expires": time.time() + 300,
        "verified": False
    }

    try:
        msg = EmailMessage()
        msg["Subject"] = "SAMUI SEVA SADAN - Admin OTP"
        msg["From"] = smtp_username
        msg["To"] = email

        msg.set_content(
            f"Your SAMUI SEVA SADAN Admin Password Reset OTP is: {otp}\n\n"
            "This OTP is valid for 5 minutes."
        )

        with smtplib.SMTP_SSL(
            smtp_host,
            smtp_port,
            timeout=15
        ) as server:
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

        return jsonify({
            "ok": True,
            "message": "OTP sent to your email"
        })

    except Exception as e:
        print("SMTP ERROR:", e)
        otp_data.pop(email, None)

        return jsonify({
            "ok": False,
            "message": "OTP email could not be sent"
        }), 500


@app.route("/api/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    otp = data.get("otp", "").strip()

    record = otp_data.get(email)

    if not record:
        return jsonify({
            "ok": False,
            "message": "OTP not found. Please request a new OTP."
        }), 400

    if time.time() > record["expires"]:
        otp_data.pop(email, None)

        return jsonify({
            "ok": False,
            "message": "OTP expired. Please request a new OTP."
        }), 400

    if otp != record["otp"]:
        return jsonify({
            "ok": False,
            "message": "Invalid OTP."
        }), 400

    record["verified"] = True

    return jsonify({
        "ok": True,
        "message": "OTP verified successfully."
    })


@app.route("/api/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    new_password = data.get("new_password", "").strip()

    record = otp_data.get(email)

    if not record or not record.get("verified"):
        return jsonify({
            "ok": False,
            "message": "Please verify OTP first."
        }), 400

    if len(new_password) < 6:
        return jsonify({
            "ok": False,
            "message": "Password must be at least 6 characters."
        }), 400

    # IMPORTANT:
    # Render's ADMIN_PASSWORD environment variable is used for login.
    # A running Render process cannot permanently change its environment
    # variable from this file.
    #
    # Therefore password reset is stored locally here for development,
    # but Render login still requires ADMIN_PASSWORD to be updated
    # in Render Environment Variables.

    reset_file = os.path.join(BASE_DIR, ".admin_password")

    with open(reset_file, "w") as f:
        f.write(new_password)

    otp_data.pop(email, None)

    return jsonify({
        "ok": True,
        "message": "Password reset successfully."
    })


@app.route("/api/admin-login", methods=["POST"])
def admin_login():
    data = request.get_json() or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if username != "admin":
        return jsonify({
            "ok": False,
            "message": "Invalid Admin Name or Password"
        }), 401

    # Use reset password file first.
    # If it does not exist, use ADMIN_PASSWORD environment variable.
    reset_file = os.path.join(BASE_DIR, ".admin_password")
    saved_password = ""

    if os.path.exists(reset_file):
        try:
            with open(reset_file, "r") as f:
                saved_password = f.read().strip()
        except Exception:
            saved_password = ""

    if not saved_password:
        saved_password = ENV.get("ADMIN_PASSWORD", "").strip()

    if password and saved_password and password == saved_password:
        return jsonify({
            "ok": True,
            "message": "Login successful"
        })

    return jsonify({
        "ok": False,
        "message": "Invalid Admin Name or Password"
    }), 401


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=False)
