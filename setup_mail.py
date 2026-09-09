import getpass
from pathlib import Path

email = input("Gmail address: ").strip()
app_password = getpass.getpass("Gmail App Password: ").replace(" ", "").strip()

Path(".env").write_text(
    f"ADMIN_EMAIL={email}\n"
    f"MAIL_USERNAME={email}\n"
    f"MAIL_APP_PASSWORD={app_password}\n"
)

Path(".env").chmod(0o600)
print("\n✅ Gmail settings saved securely.")
