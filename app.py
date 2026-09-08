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

    env_file = os.path.join(BASE_DIR, ".env")

    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()

                if "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    env[key.strip()] = value.strip()

    return env


ENV = load_env()
ENV.update(os.environ)


# =========================
# WEBSITE
# =========================

@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/<path:path>")
def files(path):
    return send_from_directory(BASE_DIR, path)


# =========================
# SEND OTP
# =========================

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

    otp = str(secrets.randbelow(900000) + 100000)

    otp_data[email] = {
        "otp": otp,
        "expires": time.time() + 300,
        "verified": False
    }

    msg = EmailMessage()

    msg["Subject"] = "SAMUI SEVA SADAN - Admin Password Reset OTP"
    msg["From"] = ENV.get("MAIL_USERNAME")
    msg["To"] = email

    msg.set_content(
        f"""SAMUI SEVA SADAN

Your Admin Password Reset OTP is:

{otp}

This OTP is valid for 5 minutes.

If you did not request a password reset, please ignore this email.
"""
    )

    try:

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465,
            timeout=15
        ) as smtp:

            smtp.login(
                ENV.get("MAIL_USERNAME"),
                ENV.get("MAIL_APP_PASSWORD")
            )

            smtp.send_message(msg)

        return jsonify({
            "ok": True,
            "message": "OTP sent to your email"
        })

    except Exception as e:

        print("MAIL ERROR:", e)

        otp_data.pop(email, None)

        return jsonify({
            "ok": False,
            "message": "Email could not be sent"
        }), 500


# =========================
# VERIFY OTP
# =========================

@app.route("/api/verify-otp", methods=["POST"])
def verify_otp():

    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    otp = data.get("otp", "").strip()

    admin_email = ENV.get("ADMIN_EMAIL", "").strip().lower()

    if email != admin_email:
        return jsonify({
            "ok": False,
            "message": "Invalid recovery email"
        }), 400

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


# =========================
# RESET PASSWORD
# =========================

@app.route("/api/reset-password", methods=["POST"])
def reset_password():

    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    new_password = data.get("new_password", "").strip()

    admin_email = ENV.get("ADMIN_EMAIL", "").strip().lower()

    if email != admin_email:
        return jsonify({
            "ok": False,
            "message": "Invalid recovery email"
        }), 400

    record = otp_data.get(email)

    if not record or not record.get("verified"):

        return jsonify({
            "ok": False,
            "message": "Please verify OTP first."
        }), 400

    if time.time() > record["expires"]:

        otp_data.pop(email, None)

        return jsonify({
            "ok": False,
            "message": "OTP expired. Please request a new OTP."
        }), 400

    if len(new_password) < 6:

        return jsonify({
            "ok": False,
            "message": "Password must be at least 6 characters."
        }), 400

    # Save new password
    reset_file = os.path.join(BASE_DIR, ".admin_password")

    try:

        with open(reset_file, "w") as f:
            f.write(new_password)

        # Immediately change password for current server
        ENV["ADMIN_PASSWORD"] = new_password

        # OTP can only be used once
        otp_data.pop(email, None)

        return jsonify({
            "ok": True,
            "message": "Password reset successfully."
        })

    except Exception as e:

        print("PASSWORD RESET ERROR:", e)

        return jsonify({
            "ok": False,
            "message": "Could not reset password."
        }), 500


# =========================
# ADMIN LOGIN
# =========================

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

    reset_file = os.path.join(BASE_DIR, ".admin_password")

    saved_password = ""

    # First check reset password
    if os.path.exists(reset_file):

        try:

            with open(reset_file, "r") as f:
                saved_password = f.read().strip()

        except Exception as e:

            print("PASSWORD FILE ERROR:", e)

    # If reset password does not exist,
    # use Render Environment Variable
    if not saved_password:

        saved_password = ENV.get(
            "ADMIN_PASSWORD",
            ""
        ).strip()

    if password == saved_password:

        return jsonify({
            "ok": True,
            "message": "Login successful"
        })

    return jsonify({
        "ok": False,
        "message": "Invalid Admin Name or Password"
    }), 401


# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=8080,
        debug=False
    )
