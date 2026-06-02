import os
import sqlite3
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from twilio.rest import Client

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "orders.db"
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__, static_folder=".")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                tea TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                phone TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


init_db()


def send_whatsapp_message(name, tea, quantity, phone):
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_WHATSAPP_FROM")
    to_number = os.getenv("TWILIO_WHATSAPP_TO") or phone

    if not all([account_sid, auth_token, from_number]):
        print("WhatsApp notification skipped: Twilio credentials are not configured.")
        return {"status": "skipped", "reason": "missing_twilio_credentials"}

    client = Client(account_sid, auth_token)
    message = (
        f"New tea order received from {name}. "
        f"Tea: {tea}, Quantity: {quantity}, Phone: {phone}."
    )

    try:
        sent = client.messages.create(
            from_=from_number,
            body=message,
            to=to_number,
        )
        return {"status": "sent", "sid": sent.sid}
    except Exception as exc:
        print(f"WhatsApp notification failed: {exc}")
        return {"status": "failed", "reason": str(exc)}


@app.route("/api/orders", methods=["POST"])
def create_order():
    data = request.get_json(silent=True) or request.form or {}
    name = (data.get("name") or "").strip()
    tea = (data.get("tea") or "").strip()
    quantity = int(data.get("quantity") or data.get("qty") or 1)
    phone = (data.get("phone") or "").strip()

    if not all([name, tea, phone]):
        return jsonify({"ok": False, "error": "Name, tea preference, and phone are required."}), 400

    created_at = datetime.now().isoformat(timespec="seconds")

    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO orders (name, tea, quantity, phone, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, tea, quantity, phone, created_at),
        )
        order_id = cursor.lastrowid
        conn.commit()

    whatsapp_result = send_whatsapp_message(name, tea, quantity, phone)

    return jsonify({
        "ok": True,
        "order_id": order_id,
        "message": "Order saved successfully.",
        "whatsapp": whatsapp_result,
    })


@app.route("/api/orders", methods=["GET"])
def list_orders():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, name, tea, quantity, phone, created_at FROM orders ORDER BY id DESC"
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def serve_static(path):
    if path.startswith("api/"):
        return app.handle_exception(Exception("Not found"))
    return send_from_directory(app.static_folder, path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
