import discord
from discord.ext import commands
import sqlite3
import time
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

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
    total_time REAL DEFAULT 0
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


def start_shift(uid):
    now = time.time()

    c.execute("""
    INSERT INTO shifts (user_id, start_time, total_time)
    VALUES (?, ?, 0)
    ON CONFLICT(user_id) DO UPDATE SET start_time=?
    """, (uid, now, now))

    conn.commit()


def end_shift(uid):
    c.execute("SELECT start_time, total_time FROM shifts WHERE user_id=?", (uid,))
    row = c.fetchone()

    if row and row[0]:
        duration = time.time() - row[0]
        total = row[1] or 0

        c.execute("""
        UPDATE shifts
        SET total_time=?, start_time=NULL
        WHERE user_id=?
        """, (total + duration, uid))

        conn.commit()


# ======================
# COMMAND: DIENSTON
# ======================
@bot.command(name="dienston")
async def dienston(ctx):

    member = ctx.author
    guild = ctx.guild

    on_role = get_role(guild, ON_ROLE) or await guild.create_role(name=ON_ROLE)
    off_role = get_role(guild, OFF_ROLE) or await guild.create_role(name=OFF_ROLE)

    await member.add_roles(on_role)
    await member.remove_roles(off_role)

    start_shift(member.id)

    try:
        await member.edit(nick=f"[ON DUTY] {member.name}")
    except:
        pass

    await ctx.send(f"🟢 {member.mention} ist jetzt im DIENST")


# ======================
# COMMAND: DIENSTOFF
# ======================
@bot.command(name="dienstoff")
async def dienstoff(ctx):

    member = ctx.author
    guild = ctx.guild

    on_role = get_role(guild, ON_ROLE)
    off_role = get_role(guild, OFF_ROLE) or await guild.create_role(name=OFF_ROLE)

    if on_role:
        await member.remove_roles(on_role)

    await member.add_roles(off_role)

    end_shift(member.id)

    try:
        await member.edit(nick=member.name)
    except:
        pass

    await ctx.send(f"🔴 {member.mention} ist jetzt AUS DEM DIENST")


# ======================
# READY
# ======================
@bot.event
async def on_ready():
    print(f"Bot online als {bot.user}")


bot.run(TOKEN)
