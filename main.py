import discord
from discord.ext import commands
from discord import app_commands
import datetime
import sqlite3
import os

# =========================
# BOT SETUP
# =========================
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# DATABASE (SQLite)
# =========================
conn = sqlite3.connect("bot.db")
c = conn.cursor()

# Dienstzeiten
c.execute("""
CREATE TABLE IF NOT EXISTS dienst (
    user_id INTEGER,
    sekunden REAL
)
""")

# Aktive Dienste
c.execute("""
CREATE TABLE IF NOT EXISTS active (
    user_id INTEGER,
    start_time TEXT
)
""")

# Wochenplan
c.execute("""
CREATE TABLE IF NOT EXISTS plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag TEXT,
    user_id INTEGER,
    zeit TEXT
)
""")

conn.commit()

# =========================
# HELPER
# =========================
def add_time(user_id, sekunden):
    c.execute("SELECT sekunden FROM dienst WHERE user_id=?", (user_id,))
    row = c.fetchone()

    if row:
        new_time = row[0] + sekunden
        c.execute("UPDATE dienst SET sekunden=? WHERE user_id=?", (new_time, user_id))
    else:
        c.execute("INSERT INTO dienst VALUES (?,?)", (user_id, sekunden))

    conn.commit()

# =========================
# BOT READY
# =========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Online als {bot.user}")

# =========================
# 🟢 DIENST AN
# =========================
@bot.tree.command(name="dienston")
async def dienston(interaction: discord.Interaction):
    user = interaction.user

    c.execute("SELECT * FROM active WHERE user_id=?", (user.id,))
    if c.fetchone():
        await interaction.response.send_message("❌ Schon im Dienst!", ephemeral=True)
        return

    c.execute("INSERT INTO active VALUES (?,?)", (user.id, datetime.datetime.now().isoformat()))
    conn.commit()

    try:
        await user.edit(nick=f"🟢 | {user.name}")
    except:
        pass

    await interaction.response.send_message("🟢 Dienst gestartet!")

# =========================
# 🔴 DIENST AUS
# =========================
@bot.tree.command(name="dienstoff")
async def dienstoff(interaction: discord.Interaction):
    user = interaction.user

    c.execute("SELECT start_time FROM active WHERE user_id=?", (user.id,))
    row = c.fetchone()

    if not row:
        await interaction.response.send_message("❌ Nicht im Dienst!", ephemeral=True)
        return

    start = datetime.datetime.fromisoformat(row[0])
    dauer = (datetime.datetime.now() - start).total_seconds()

    add_time(user.id, dauer)

    c.execute("DELETE FROM active WHERE user_id=?", (user.id,))
    conn.commit()

    try:
        await user.edit(nick=f"🔴 | {user.name}")
    except:
        pass

    await interaction.response.send_message(f"🔴 Dienst beendet! {int(dauer//60)} Minuten")

# =========================
# 🏆 LEADERBOARD
# =========================
@bot.tree.command(name="leaderboard")
async def leaderboard(interaction: discord.Interaction):

    c.execute("SELECT user_id, sekunden FROM dienst ORDER BY sekunden DESC LIMIT 10")
    rows = c.fetchall()

    if not rows:
        await interaction.response.send_message("📭 Keine Daten")
        return

    text = "🏆 **Leaderboard**\n\n"

    for i, (uid, sec) in enumerate(rows, start=1):
        user = await bot.fetch_user(uid)
        text += f"{i}. {user.name} - {round(sec/3600,2)}h\n"

    await interaction.response.send_message(text)

# =========================
# 📅 SCHICHT ERSTELLEN (WOCHENTAG)
# =========================
@bot.tree.command(name="schicht")
@app_commands.describe(
    tag="Montag-Sonntag",
    user="User",
    zeit="z.B. 18:00-22:00"
)
async def schicht(interaction: discord.Interaction, tag: str, user: discord.Member, zeit: str):

    tag = tag.capitalize()

    c.execute("INSERT INTO plan (tag,user_id,zeit) VALUES (?,?,?)",
              (tag, user.id, zeit))
    conn.commit()

    await interaction.response.send_message(f"📅 {tag} gespeichert für {user.name} ({zeit})")

# =========================
# 📋 WOCHENPLAN
# =========================
@bot.tree.command(name="wochenplan")
async def wochenplan(interaction: discord.Interaction):

    c.execute("SELECT tag,user_id,zeit FROM plan")
    rows = c.fetchall()

    if not rows:
        await interaction.response.send_message("📭 Kein Plan")
        return

    text = "📅 **Wochenplan**\n\n"

    days = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]

    for day in days:
        text += f"📆 **{day}**\n"

        found = False
        for tag, uid, zeit in rows:
            if tag == day:
                user = await bot.fetch_user(uid)
                text += f"👤 {user.name} | ⏰ {zeit}\n"
                found = True

        if not found:
            text += "Keine Schichten\n"

        text += "\n"

    await interaction.response.send_message(text)

# =========================
# ❌ PLAN RESET
# =========================
@bot.tree.command(name="resetplan")
async def resetplan(interaction: discord.Interaction):
    c.execute("DELETE FROM plan")
    conn.commit()

    await interaction.response.send_message("🗑️ Wochenplan gelöscht!")

# =========================
# START BOT (RAILWAY)
# =========================
bot.run(os.getenv("TOKEN"))
