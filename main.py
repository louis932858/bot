import discord
from discord.ext import commands
import sqlite3
import time
import os
from dotenv import load_dotenv

# ======================
# TOKEN
# ======================
load_dotenv()
TOKEN = os.getenv("TOKEN")

# ======================
# INTENTS
# ======================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# ======================
# DATABASE
# ======================
conn = sqlite3.connect("shift.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS shifts (
    user_id INTEGER PRIMARY KEY,
    start_time REAL,
    total_time REAL DEFAULT 0,
    original_name TEXT
)
""")
conn.commit()

# ======================
# CONFIG
# ======================
ON_ROLE = "OnDuty"
OFF_ROLE = "OffDuty"

# ======================
# HELPERS
# ======================
def get_role(guild, name):
    return discord.utils.get(guild.roles, name=name)


def start_shift(user_id, name):
    now = time.time()

    c.execute("""
    INSERT INTO shifts (user_id, start_time, total_time, original_name)
    VALUES (?, ?, 0, ?)
    ON CONFLICT(user_id) DO UPDATE SET start_time=?, original_name=?
    """, (user_id, now, name, now, name))

    conn.commit()


def end_shift(user_id):
    c.execute("SELECT start_time, total_time FROM shifts WHERE user_id=?", (user_id,))
    row = c.fetchone()

    if row and row[0]:
        duration = time.time() - row[0]
        total = row[1] or 0

        c.execute("""
        UPDATE shifts
        SET total_time=?, start_time=NULL
        WHERE user_id=?
        """, (total + duration, user_id))

        conn.commit()


def get_original_name(user_id):
    c.execute("SELECT original_name FROM shifts WHERE user_id=?", (user_id,))
    row = c.fetchone()
    return row[0] if row else None


def get_hours(user_id):
    c.execute("SELECT total_time FROM shifts WHERE user_id=?", (user_id,))
    row = c.fetchone()
    return round((row[0] if row else 0) / 3600, 2)


# ======================
# DIENSTON
# ======================
@bot.command()
async def dienston(ctx):

    member = ctx.author
    guild = ctx.guild

    on_role = get_role(guild, ON_ROLE) or await guild.create_role(name=ON_ROLE)
    off_role = get_role(guild, OFF_ROLE) or await guild.create_role(name=OFF_ROLE)

    await member.add_roles(on_role)
    await member.remove_roles(off_role)

    start_shift(member.id, member.name)

    try:
        await member.edit(nick=f"[🟢IM DIENST🟢] {member.name}")
    except:
        pass

    await ctx.send(f"🟢 {member.mention} ist jetzt im DIENST")


# ======================
# DIENSTOFF
# ======================
@bot.command()
async def dienstoff(ctx):

    member = ctx.author
    guild = ctx.guild

    on_role = get_role(guild, ON_ROLE)
    off_role = get_role(guild, OFF_ROLE) or await guild.create_role(name=OFF_ROLE)

    if on_role:
        await member.remove_roles(on_role)

    await member.add_roles(off_role)

    end_shift(member.id)

    original = get_original_name(member.id)

    try:
          await member.edit(nick=f"[🔴AUS DIENST🔴] {member.name}")
    except:
        pass

    hours = get_hours(member.id)

    await ctx.send(f"🔴 {member.mention} ist OFF DUTY | ⏱️ {hours} Stunden")


# ======================
# LEADERBOARD
# ======================
@bot.command()
async def leaderboard(ctx):

    c.execute("SELECT user_id, total_time FROM shifts ORDER BY total_time DESC LIMIT 10")
    rows = c.fetchall()

    embed = discord.Embed(title="📊 Dienst Leaderboard", color=0x00ff00)

    for i, (uid, t) in enumerate(rows, start=1):
        user = await bot.fetch_user(uid)
        embed.add_field(
            name=f"{i}. {user}",
            value=f"⏱️ {round(t/3600,2)} Stunden",
            inline=False
        )

    await ctx.send(embed=embed)


# ======================
# READY
# ======================
@bot.event
async def on_ready():
    print(f"Bot online als {bot.user}")


bot.run(TOKEN)
