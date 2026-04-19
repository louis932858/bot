import discord
from discord.ext import commands
from discord import app_commands
import datetime
import os

# =========================
# INTENTS
# =========================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# SPEICHER (RAM)
# =========================
dienstzeiten = {}
aktive_dienste = {}
dienstplan = []

# =========================
# BOT START
# =========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Online als {bot.user}")

# =========================
# 🟢 DIENST AN
# =========================
@bot.tree.command(name="dienston", description="Gehe in den Dienst")
async def dienston(interaction: discord.Interaction):
    user = interaction.user

    if user.id in aktive_dienste:
        await interaction.response.send_message("❌ Du bist schon im Dienst!", ephemeral=True)
        return

    aktive_dienste[user.id] = datetime.datetime.now()

    try:
        await user.edit(nick=f"🟢 | {user.name}")
    except:
        pass

    await interaction.response.send_message("🟢 Du bist jetzt im Dienst!")

# =========================
# 🔴 DIENST AUS
# =========================
@bot.tree.command(name="dienstoff", description="Gehe aus dem Dienst")
async def dienstoff(interaction: discord.Interaction):
    user = interaction.user

    if user.id not in aktive_dienste:
        await interaction.response.send_message("❌ Du bist nicht im Dienst!", ephemeral=True)
        return

    start = aktive_dienste.pop(user.id)
    dauer = (datetime.datetime.now() - start).total_seconds()

    dienstzeiten[user.id] = dienstzeiten.get(user.id, 0) + dauer

    try:
        await user.edit(nick=f"🔴 | {user.name}")
    except:
        pass

    await interaction.response.send_message(
        f"🔴 Dienst beendet! Zeit: {int(dauer // 60)} Minuten"
    )

# =========================
# 🏆 LEADERBOARD
# =========================
@bot.tree.command(name="leaderboard", description="Zeigt die aktivsten Mitglieder")
async def leaderboard(interaction: discord.Interaction):

    if not dienstzeiten:
        await interaction.response.send_message("📭 Keine Daten vorhanden.")
        return

    sorted_users = sorted(dienstzeiten.items(), key=lambda x: x[1], reverse=True)

    text = "🏆 **Leaderboard**\n\n"

    for i, (uid, sec) in enumerate(sorted_users[:10], start=1):
        user = await bot.fetch_user(uid)
        text += f"{i}. {user.name} - {round(sec/3600, 2)}h\n"

    await interaction.response.send_message(text)

# =========================
# 📅 SCHICHT ERSTELLEN
# =========================
@bot.tree.command(name="schicht", description="Erstelle eine Schicht")
@app_commands.describe(
    tag="Montag-Sonntag",
    user="User",
    zeit="z.B. 18:00-22:00"
)
async def schicht(interaction: discord.Interaction, tag: str, user: discord.Member, zeit: str):

    tag = tag.capitalize()

    gueltig = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]

    if tag not in gueltig:
        await interaction.response.send_message("❌ Ungültiger Wochentag!", ephemeral=True)
        return

    dienstplan.append({
        "tag": tag,
        "user": user.id,
        "zeit": zeit
    })

    await interaction.response.send_message(
        f"📅 Schicht erstellt:\n👤 {user.mention}\n📆 {tag}\n⏰ {zeit}"
    )

# =========================
# 📋 DIENSTPLAN ANZEIGEN
# =========================
@bot.tree.command(name="dienstplan", description="Zeigt den Wochenplan")
async def dienstplan_show(interaction: discord.Interaction):

    if not dienstplan:
        await interaction.response.send_message("📭 Kein Dienstplan vorhanden.")
        return

    text = "📅 **Wochenplan**\n\n"

    tage = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]

    for tag in tage:
        text += f"📆 **{tag}**\n"

        found = False
        for s in dienstplan:
            if s["tag"] == tag:
                user = await bot.fetch_user(s["user"])
                text += f"👤 {user.name} | ⏰ {s['zeit']}\n"
                found = True

        if not found:
            text += "Keine Schichten\n"

        text += "\n"

    await interaction.response.send_message(text)

# =========================
# 🗑️ PLAN LÖSCHEN
# =========================
@bot.tree.command(name="resetplan", description="Löscht den Dienstplan")
async def resetplan(interaction: discord.Interaction):
    dienstplan.clear()
    await interaction.response.send_message("🗑️ Dienstplan gelöscht!")

# =========================
# BOT START (RAILWAY)
# =========================
bot.run(os.getenv("TOKEN"))
