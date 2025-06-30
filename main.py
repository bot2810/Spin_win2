
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import os
import sqlite3
from utils.telegram_api import send_telegram_message

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecret")  # Use env var for secret key

# --- Constants ---
MAIN_BOT_TOKEN = "bot" + os.environ.get("MAIN_BOT_TOKEN")
VIEW_BOT_TOKEN = "bot" + os.environ.get("VIEW_BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
SPINS_PER_DAY = 15
TELEGRAM_API_URL = "https://api.telegram.org/"

# --- Database ---
DATABASE_FILE = "spin_win.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE NOT NULL,
            spins_today INTEGER DEFAULT 0,
            total_earnings REAL DEFAULT 0.0,
            adblock_detected INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

with app.app_context():
    init_db()


# --- Helper Functions ---

def generate_spin_reward():
    return round(random.uniform(0.10, 1.00), 2)

def calculate_final_earnings(spins, total_earned):
    #ensure total earning mostly 2.50 per 15 spins
    if spins == SPINS_PER_DAY:
        return 2.50
    else:
        return total_earned # or maybe 0.0 if you dont want to store value

def generate_scratch_reward():
    return round(random.uniform(1.00, 5.00), 2)

def notify_admin(message):
    send_telegram_message(VIEW_BOT_TOKEN, ADMIN_ID, message)

# --- Routes ---

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        telegram_id = request.form.get("telegram_id")
        if telegram_id:
            try:
                telegram_id = int(telegram_id)
            except ValueError:
                return render_template("index.html", error="Invalid Telegram ID")

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            user = cursor.fetchone()

            if not user:
                cursor.execute("INSERT INTO users (telegram_id) VALUES (?)", (telegram_id,))
                conn.commit()
                user = cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()

            conn.close()

            session["telegram_id"] = telegram_id
            notify_admin(f"User {telegram_id} started game")
            return redirect(url_for("spin"))
        else:
            return render_template("index.html", error="Please enter your Telegram ID")
    return render_template("index.html")

@app.route("/spin")
def spin():
    telegram_id = session.get("telegram_id")
    if not telegram_id:
        return redirect(url_for("index"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT spins_today, total_earnings FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    spins_today = user['spins_today']
    total_earnings = user['total_earnings']
    conn.close()

    if spins_today >= SPINS_PER_DAY:
        return redirect(url_for("scratch"))

    return render_template("spin.html", spins_left=SPINS_PER_DAY - spins_today, total_earnings=total_earnings)

@app.route("/spin_action", methods=["POST"])
def spin_action():
    telegram_id = session.get("telegram_id")
    if not telegram_id:
        return jsonify({"error": "Not logged in"})

    ad_blocked = request.form.get("ad_blocked") == "true"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT spins_today, total_earnings FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    spins_today = user['spins_today']
    total_earnings = user['total_earnings']

    if spins_today >= SPINS_PER_DAY:
        conn.close()
        return jsonify({"redirect": url_for("scratch")})

    if ad_blocked:
        # User loses spin/reward if ad is blocked
        conn.close()
        return jsonify({"reward": 0, "spins_left": SPINS_PER_DAY - spins_today, "total_earnings": total_earnings})

    reward = generate_spin_reward()

    new_spins_today = spins_today + 1
    new_total_earnings = total_earnings + reward

    if new_spins_today == SPINS_PER_DAY:
        final_earnings = calculate_final_earnings(new_spins_today, new_total_earnings)
        new_total_earnings = final_earnings


    cursor.execute("UPDATE users SET spins_today = ?, total_earnings = ? WHERE telegram_id = ?", (new_spins_today, new_total_earnings, telegram_id))
    conn.commit()
    conn.close()

    notify_admin(f"User {telegram_id} completed spin {new_spins_today}/{SPINS_PER_DAY}")


    return jsonify({"reward": reward, "spins_left": SPINS_PER_DAY - new_spins_today, "total_earnings": new_total_earnings})

@app.route("/scratch")
def scratch():
    telegram_id = session.get("telegram_id")
    if not telegram_id:
        return redirect(url_for("index"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT total_earnings FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    total_earnings = user['total_earnings']
    conn.close()

    return render_template("scratch.html", total_earnings=total_earnings)


@app.route("/scratch_action", methods=["POST"])
def scratch_action():
    telegram_id = session.get("telegram_id")
    if not telegram_id:
        return jsonify({"error": "Not logged in"})

    scratch_reward = generate_scratch_reward()

    # Send reward to main bot
    send_telegram_message(MAIN_BOT_TOKEN, telegram_id, f"/addbalance {telegram_id} {scratch_reward}")

    notify_admin(f"User {telegram_id} used scratch card, won ₹{scratch_reward}")

    # Reset spins for the day
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET spins_today = 0, total_earnings = 0 WHERE telegram_id = ?", (telegram_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": f"You won ₹{scratch_reward}!", "redirect": url_for("index")})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
