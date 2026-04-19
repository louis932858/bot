from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

def db():
    conn = sqlite3.connect("shift.db")
    c = conn.cursor()
    return conn, c


@app.route("/")
def home():
    conn, c = db()

    c.execute("SELECT user_id, total_time FROM shifts ORDER BY total_time DESC")
    data = c.fetchall()

    leaderboard = []
    for uid, t in data:
        leaderboard.append({
            "user_id": uid,
            "hours": round(t / 3600, 2)
        })

    conn.close()
    return render_template("index.html", leaderboard=leaderboard)


@app.route("/reset/<int:user_id>")
def reset(user_id):
    conn, c = db()
    c.execute("UPDATE shifts SET total_time=0, start_time=NULL WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    return "Reset done ✔"


def run_dashboard():
    app.run(host="0.0.0.0", port=8080)
