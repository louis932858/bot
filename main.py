import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import time
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ======================
# 🗄️ DATABASE
# ======================
conn = sqlite3.connect("shift.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS shifts (
    user_id INTEGER PRIMARY KEY,
    start_time REAL,
    total_time REAL DEFAULT 0,
    last_action REAL
)
""")
conn.commit()

# ======================
# CONFIG
# ======================
ON_ROLE = "OnDuty"
OFF_ROLE = "OffDuty"
AFK_TIME = 300

# ======================
# HELPERS
# ======================
def get_role(guild, name):
    return discord.utils.get(guild.roles, name=name)


def start_shift(uid):
    now = time.time()
    c.execute("""
    INSERT INTO shifts (user_id, start_time, last_action, total_time)
    VALUES (?, ?, ?, 0)
    ON CONFLICT(user_id) DO UPDATE SET start_time=?, last_action=?
    """, (uid, now, now, now, now))
    conn.commit()


def end_shift(uid):
    c.execute("SELECT start_time, total_time FROM shifts WHERE user_id=?", (uid,))
    row = c.fetchone()

    if row and row[0]:
        duration = time.time() - row[0]
        total = row[1] or 0

        c.execute("""
        UPDATE shifts SET total_time=?, start_time=NULL WHERE user_id=?
        """, (total + duration, uid))
        conn.commit()


def update_activity(uid):
    c.execute("UPDATE shifts SET last_action=? WHERE user_id=?", (time.time(), uid))
    conn.commit()


def is_afk(uid):
    c.execute("SELECT last_action FROM shifts WHERE user_id=?", (uid,))
    row = c.fetchone()

    if not row or not row[0]:
        return False

    return (time.time() - row[0]) > AFK_TIME


# ======================
# AFK TRACKING
# ======================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    update_activity(message.author.id)
    await bot.process_commands(message)


# ======================
# BUTTONS
# ======================
class ShiftView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="On Duty", style=discord.ButtonStyle.success, emoji="🟢")
    async def on(self, interaction: discord.Interaction, button: discord.ui.Button):

        member = interaction.user
        guild = interaction.guild

        on_role = get_role(guild, ON_ROLE) or await guild.create_role(name=ON_ROLE)
        off_role = get_role(guild, OFF_ROLE) or await guild.create_role(name=OFF_ROLE)

        await member.add_roles(on_role)
        await member.remove_roles(off_role)

        start_shift(member.id)
        update_activity(member.id)

        try:
            await member.edit(nick=f"[ON DUTY] {member.name}")
        except:
            pass

        await interaction.response.send_message("🟢 ON DUTY", ephemeral=True)

    @discord.ui.button(label="Off Duty", style=discord.ButtonStyle.danger, emoji="🔴")
    async def off(self, interaction: discord.Interaction, button: discord.ui.Button):

        member = interaction.user
        guild = interaction.guild

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

        await interaction.response.send_message("🔴 OFF DUTY", ephemeral=True)


# ======================
# SLASH COMMANDS
# ======================
@bot.tree.command(name="onduty")
async def onduty(interaction: discord.Interaction):
    await ShiftView().on(interaction, None)


@bot.tree.command(name="offduty")
async def offduty(interaction: discord.Interaction):
    await ShiftView().off(interaction, None)


@bot.tree.command(name="leaderboard")
async def leaderboard(interaction: discord.Interaction):

    c.execute("SELECT user_id, total_time FROM shifts ORDER BY total_time DESC LIMIT 10")
    rows = c.fetchall()

    embed = discord.Embed(title="📊 Leaderboard", color=0x00ff00)

    for i, (uid, t) in enumerate(rows, start=1):
        user = await bot.fetch_user(uid)
        embed.add_field(
            name=f"{i}. {user}",
            value=f"⏱️ {round(t/3600,2)} Stunden",
            inline=False
        )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="afkcheck")
@app_commands.checks.has_permissions(administrator=True)
async def afkcheck(interaction: discord.Interaction, member: discord.Member):

    if is_afk(member.id):
        msg = f"⚠️ {member.mention} ist AFK"
    else:
        msg = f"✅ {member.mention} ist aktiv"

    await interaction.response.send_message(msg, ephemeral=True)


# ======================
# START
# ======================
@bot.event
async def on_ready():
    print(f"Bot online {bot.user}")
    await bot.tree.sync()
    print("Slash Commands synced")


bot.run(TOKEN)
