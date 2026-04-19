import discord
from discord.ext import commands
from discord import app_commands
import datetime
import os

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# 📦 Speicher (RAM)
dienstzeiten = {}      # user_id -> sekunden
aktive_dienste = {}    # user_id -> startzeit
dienstplan = []        # tägliche Schichten (ohne Datum)

# 🔄 BOT START
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot online: {bot.user}")

# 🟢 DIENST AN
@bot.tree.command(name="dienston", description="Gehe in den Dienst")
async def dienston(interaction: discord.Interaction):
    user_id = interaction.user.id

    if user_id in aktive_dienste:
        await interaction.response.send_message("❌ Du bist bereits im Dienst!", ephemeral=True)
        return

    aktive_dienste[user_id] = datetime.datetime.now()
    await interaction.response.send_message("🟢 Du bist jetzt im Dienst!")

# 🔴 DIENST AUS
@bot.tree.command(name="dienstoff", description="Gehe aus dem Dienst")
async def dienstoff(interaction: discord.Interaction):
    user_id = interaction.user.id

    if user_id not in aktive_dienste:
        await interaction.response.send_message("❌ Du bist nicht im Dienst!", ephemeral=True)
        return

    start = aktive_dienste.pop(user_id)
    dauer = (datetime.datetime.now() - start).total_seconds()

    dienstzeiten[user_id] = dienstzeiten.get(user_id, 0) + dauer

    await interaction.response.send_message(
        f"🔴 Dienst beendet! Zeit: {int(dauer // 60)} Minuten"
    )

# 🏆 LEADERBOARD
@bot.tree.command(name="leaderboard", description="Zeigt die aktivsten Mitglieder")
async def leaderboard(interaction: discord.Interaction):

    if not dienstzeiten:
        await interaction.response.send_message("📭 Keine Daten vorhanden.")
        return

    sorted_users = sorted(dienstzeiten.items(), key=lambda x: x[1], reverse=True)

    text = "🏆 **Leaderboard**\n\n"

    for i, (user_id, zeit) in enumerate(sorted_users[:10], start=1):
        try:
            user = await bot.fetch_user(user_id)
            stunden = round(zeit / 3600, 2)
            text += f"{i}. {user.name} - {stunden}h\n"
        except:
            continue

    await interaction.response.send_message(text)

# 📅 DIENSTPLAN (OHNE DATUM → TÄGLICH GÜLTIG)
@bot.tree.command(name="dienstplan_erstellen", description="Erstelle eine tägliche Schicht")
@app_commands.describe(
    user="User",
    zeit="Zeit (z.B. 18:00-22:00)"
)
async def dienstplan_erstellen(interaction: discord.Interaction, user: discord.Member, zeit: str):

    dienstplan.append({
        "user": user.id,
        "zeit": zeit
    })

    await interaction.response.send_message(
        f"📅 Tägliche Schicht erstellt:\n👤 {user.mention}\n⏰ {zeit}"
    )

# 📋 DIENSTPLAN ANZEIGEN
@bot.tree.command(name="dienstplan", description="Zeigt den täglichen Dienstplan")
async def dienstplan_show(interaction: discord.Interaction):

    if not dienstplan:
        await interaction.response.send_message("📭 Kein Dienstplan vorhanden.")
        return

    text = "📅 **Täglicher Dienstplan**\n\n"

    for s in dienstplan:
        user = await bot.fetch_user(s["user"])
        text += f"👤 {user.name} | ⏰ {s['zeit']}\n"

    await interaction.response.send_message(text)

# ❌ DIENSTPLAN LÖSCHEN
@bot.tree.command(name="dienstplan_loeschen", description="Löscht alle Schichten")
async def dienstplan_delete(interaction: discord.Interaction):
    dienstplan.clear()
    await interaction.response.send_message("🗑️ Dienstplan gelöscht!")

# 🔑 TOKEN (Railway)
bot.run(os.getenv("TOKEN"))
